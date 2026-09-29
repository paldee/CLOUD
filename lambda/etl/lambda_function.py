"""AgriChain ETL Lambda (S3 CSV -> Amazon RDS PostgreSQL data warehouse).

Invoked in two ways:
  1. By AWS Step Functions (state machine "agrichain-etl") with the EventBridge
     "Object Created" event emitted by the S3 CSV bucket.
     (The classic S3 notification shape {"Records": [...]} is accepted too.)
  2. By CloudFormation as a custom resource (Custom::SchemaInit) at stack
     create/update time. It creates the schema + dim_date and seeds the
     DynamoDB login table. The RDS instance lives in private subnets, so this is
     the only place that can reach it during provisioning.
"""
import hashlib
import json
import os
import secrets
import ssl
import urllib.parse
import urllib.request
from datetime import datetime

import boto3
import pandas as pd
from sqlalchemy import create_engine, text

DB_HOST = os.environ.get("DB_HOST")
DB_NAME = os.environ.get("DB_NAME", "postgres")
DB_USER = os.environ.get("DB_USER")
DB_PASS = os.environ.get("DB_PASS")
DB_PORT = os.environ.get("DB_PORT", "5432")
DB_SCHEMA = os.environ.get("DB_SCHEMA", "data_warehouse")
DYNAMODB_TABLE = os.environ.get("DYNAMODB_TABLE", "user_login")

s3_client = boto3.client("s3")

_engine = None


def get_db_engine():
    """Create (and reuse across warm invocations) the SQLAlchemy engine."""
    global _engine
    if _engine is None:
        ctx = ssl.create_default_context()
        ctx.check_hostname = False  # traffic never leaves the VPC
        ctx.verify_mode = ssl.CERT_NONE
        url = "postgresql+pg8000://{}:{}@{}:{}/{}".format(
            urllib.parse.quote_plus(DB_USER or ""),
            urllib.parse.quote_plus(DB_PASS or ""),
            DB_HOST,
            DB_PORT,
            DB_NAME,
        )
        _engine = create_engine(
            url,
            connect_args={"ssl_context": ctx},
            pool_pre_ping=True,
        )
    return _engine


def get_surrogate_key_mapping(engine, table_name, sk_col, bk_col):
    """Load {business_key: surrogate_key} used to resolve fact foreign keys."""
    query = f"SELECT {sk_col}, {bk_col} FROM {DB_SCHEMA}.{table_name}"
    # SCD Type 2 dimensions: only the current version is a valid lookup target
    if table_name in ("dim_farmer", "dim_customer"):
        query += " WHERE is_current = true"
    df_lookup = pd.read_sql(query, con=engine)
    return dict(zip(df_lookup[bk_col], df_lookup[sk_col]))


def load(df, engine, table):
    # CSVs carry source-only columns (national_id, phone, is_active, ...) that the
    # warehouse schema intentionally omits: keep only the target table's columns
    cols = pd.read_sql(
        text("SELECT column_name FROM information_schema.columns "
             "WHERE table_schema = :s AND table_name = :t"),
        con=engine, params={"s": DB_SCHEMA, "t": table},
    )["column_name"].tolist()
    dropped = [c for c in df.columns if c not in cols]
    if dropped:
        print(f"{table}: ignoring source-only columns {dropped}")
    df = df[[c for c in df.columns if c in cols]]
    df.to_sql(
        name=table,
        con=engine,
        schema=DB_SCHEMA,
        if_exists="append",
        index=False,
        method="multi",
        chunksize=500,
    )
    return table


def date_key(series):
    # string based: pandas cannot hold the 9999-12-31 sentinel as a datetime64[ns]
    return series.astype(str).str.slice(0, 10).str.replace("-", "", regex=False).astype(int)


def map_keys(df, engine, specs):
    """specs: [(dim_table, sk_col, bk_col)] -> adds <sk_col>, fails on unmatched keys."""
    for table, sk_col, bk_col in specs:
        df[sk_col] = df[bk_col].map(get_surrogate_key_mapping(engine, table, sk_col, bk_col))
        missing = df[sk_col].isna()
        if missing.any():
            bad = sorted(df.loc[missing, bk_col].astype(str).unique())[:10]
            raise ValueError(
                f"{missing.sum()} row(s) reference {bk_col} not found in {table} "
                f"(e.g. {bad}). Upload the dimension files first."
            )
        df[sk_col] = df[sk_col].astype(int)
    return df


# ==========================================
# ETL: File routing & data cleansing
# ==========================================
def etl_crop(df, engine):
    df["crop_name"] = df["crop_name"].str.strip()
    df["standard_price_per_unit"] = df["standard_price_per_unit"].fillna(0.00).clip(lower=0)
    return load(df, engine, "dim_crop")


def etl_farmer(df, engine):
    df["farmer_name"] = df["farmer_name"].str.strip()
    df["valid_from"] = datetime.now().date()  # real dates: pg8000 sends str as text
    df["valid_to"] = datetime(9999, 12, 31).date()
    df["is_current"] = True
    # NOTE: a full SCD Type 2 would also close (valid_to) the previous version
    return load(df, engine, "dim_farmer")


def etl_warehouse(df, engine):
    df["manager_name"] = df["manager_name"].str.strip()
    df["current_warehouse_name"] = df["warehouse_name"]
    df["capacity_ton"] = df["capacity_ton"].clip(lower=0)
    df = df.drop(columns=["warehouse_name"])
    return load(df, engine, "dim_warehouse")


def etl_customer(df, engine):
    df["customer_name"] = df["customer_name"].str.strip()
    df["credit_limit_thb"] = df["credit_limit_thb"].fillna(0.00)
    df["valid_from"] = datetime.now().date()  # real dates: pg8000 sends str as text
    df["valid_to"] = datetime(9999, 12, 31).date()
    df["is_current"] = True
    return load(df, engine, "dim_customer")


def etl_harvest(df, engine):
    df["harvest_date_key"] = date_key(df["harvest_date"])
    df["quantity_kg"] = df["quantity_kg"].clip(lower=0)
    df["price_per_kg"] = df["price_per_kg"].clip(lower=0)
    df["total_amount_thb"] = df["quantity_kg"] * df["price_per_kg"]
    df = map_keys(df, engine, [
        ("dim_farmer", "farmer_sk", "farmer_id"),
        ("dim_crop", "crop_sk", "crop_id"),
        ("dim_warehouse", "warehouse_sk", "warehouse_id"),
    ])
    df = df.drop(columns=["farmer_id", "crop_id", "warehouse_id", "harvest_date"])
    return load(df, engine, "fact_harvest")


def etl_sales(df, engine):
    df["sale_date_key"] = date_key(df["sale_date"])
    df["quantity_kg"] = df["quantity_kg"].clip(lower=0)
    df["discount_pct"] = df["discount_pct"].fillna(0.00)
    df = map_keys(df, engine, [
        ("dim_customer", "customer_sk", "customer_id"),
        ("dim_crop", "crop_sk", "crop_id"),
        ("dim_warehouse", "warehouse_sk", "warehouse_id"),
    ])
    df = df.drop(columns=["customer_id", "crop_id", "warehouse_id", "sale_date", "order_id"])
    return load(df, engine, "fact_sales")


def etl_shipment(df, engine):
    df["shipment_date_key"] = date_key(df["shipment_date"])
    # Null delivery date -> 9999-12-31 per the data dictionary
    df["delivery_date"] = df["delivery_date"].fillna("9999-12-31")
    df["delivery_date_key"] = date_key(df["delivery_date"])
    df = map_keys(df, engine, [
        ("dim_customer", "customer_sk", "customer_id"),
        ("dim_crop", "crop_sk", "crop_id"),
        ("dim_warehouse", "warehouse_sk", "warehouse_id"),
    ])
    df = df.drop(columns=[
        "customer_id", "crop_id", "warehouse_id", "shipment_date",
        "delivery_date", "driver_name", "vehicle_plate",
    ])
    return load(df, engine, "fact_shipment")


def etl_inventory(df, engine):
    df["snapshot_date_key"] = date_key(df["snapshot_date"])
    df["received_kg"] = df["received_kg"].fillna(0.00)
    df["sold_kg"] = df["sold_kg"].fillna(0.00)
    df = map_keys(df, engine, [
        ("dim_crop", "crop_sk", "crop_id"),
        ("dim_warehouse", "warehouse_sk", "warehouse_id"),
    ])
    df = df.drop(columns=["crop_id", "warehouse_id", "snapshot_date", "stock_status"])
    return load(df, engine, "fact_inventory")


# File name keyword -> ETL handler (dimensions first, then facts)
ROUTES = [
    ("Crop", etl_crop),
    ("Farmer", etl_farmer),
    ("Warehouse", etl_warehouse),
    ("Customer", etl_customer),
    ("Harvest", etl_harvest),
    ("Sales", etl_sales),
    ("Shipment", etl_shipment),
    ("Inventory", etl_inventory),
]


def extract_s3_object(event):
    """Return (bucket, key) from an EventBridge or classic S3 notification event."""
    if "Records" in event:
        s3 = event["Records"][0]["s3"]
        bucket, key = s3["bucket"]["name"], s3["object"]["key"]
    else:
        detail = event["detail"]
        bucket, key = detail["bucket"]["name"], detail["object"]["key"]
    return bucket, urllib.parse.unquote_plus(key, encoding="utf-8")


def run_etl(event):
    bucket, key = extract_s3_object(event)
    print(f"ETL start: s3://{bucket}/{key}")

    if not key.lower().endswith(".csv"):
        print(f"Skipping non-CSV object: {key}")
        return {"statusCode": 200, "body": f"Skipped non-CSV object {key}"}

    filename = key.rsplit("/", 1)[-1]
    handler = next((fn for word, fn in ROUTES if word in filename), None)
    if handler is None:
        # Permanent failure: Step Functions must not retry a file we cannot route
        raise ValueError(f"File pattern not recognized: {key}")

    obj = s3_client.get_object(Bucket=bucket, Key=key)
    df = pd.read_csv(obj["Body"], encoding="utf-8-sig")  # source CSVs carry a BOM
    target_table = handler(df, get_db_engine())

    msg = f"ETL completed for {key}: inserted {len(df)} rows into {DB_SCHEMA}.{target_table}"
    print(msg)
    return {"statusCode": 200, "body": msg, "table": target_table, "rows": int(len(df))}


# ==========================================
# Provisioning (CloudFormation custom resource)
# ==========================================
def hash_password(password):
    """scrypt hash; format must stay in sync with server.js (verifyPassword)."""
    salt = secrets.token_bytes(16)
    digest = hashlib.scrypt(password.encode(), salt=salt, n=16384, r=8, p=1, dklen=64)
    return f"scrypt$16384$8$1${salt.hex()}${digest.hex()}"


def init_schema():
    """Create schema/tables from schema.sql and fill dim_date (idempotent)."""
    sql_path = os.path.join(os.path.dirname(__file__), "schema.sql")
    with open(sql_path, encoding="utf-8") as fh:
        lines = [ln for ln in fh.read().splitlines() if not ln.strip().startswith("--")]
    statements = [s.strip() for s in "\n".join(lines).split(";") if s.strip()]

    with get_db_engine().begin() as conn:
        for stmt in statements:
            conn.execute(text(stmt))
        # dim_date has no source CSV: generate it (plus the 9999-12-31 sentinel used
        # for shipments that have not been delivered yet)
        conn.execute(text(f"""
            INSERT INTO {DB_SCHEMA}.dim_date (date_key, date, day, month, quarter, year, weekday)
            SELECT to_char(d, 'YYYYMMDD')::int, d::date, EXTRACT(DAY FROM d)::int,
                   EXTRACT(MONTH FROM d)::int, EXTRACT(QUARTER FROM d)::int,
                   EXTRACT(YEAR FROM d)::int, trim(to_char(d, 'Day'))
            FROM generate_series('2015-01-01'::date, '2035-12-31'::date, interval '1 day') AS d
            ON CONFLICT (date_key) DO NOTHING
        """))
        conn.execute(text(f"""
            INSERT INTO {DB_SCHEMA}.dim_date (date_key, date, day, month, quarter, year, weekday)
            VALUES (99991231, '9999-12-31', 31, 12, 4, 9999, 'Friday')
            ON CONFLICT (date_key) DO NOTHING
        """))
    print(f"Schema '{DB_SCHEMA}' ready")


def seed_admin_user(props):
    username = (props.get("AdminUsername") or "").lower().strip()
    password = props.get("AdminPassword")
    if not username or not password:
        return
    table = boto3.resource("dynamodb").Table(DYNAMODB_TABLE)
    try:
        table.put_item(
            Item={
                "username": username,
                "password": hash_password(password),
                "name": props.get("AdminName") or username,
                "role": "Admin",
                "createdAt": datetime.utcnow().isoformat() + "Z",
            },
            ConditionExpression="attribute_not_exists(username)",
        )
        print(f"Seeded login user '{username}'")
    except table.meta.client.exceptions.ConditionalCheckFailedException:
        print(f"Login user '{username}' already exists; left untouched")


def send_cfn_response(event, context, status, reason=""):
    body = json.dumps({
        "Status": status,
        "Reason": reason or f"See CloudWatch log stream {context.log_stream_name}",
        "PhysicalResourceId": event.get("PhysicalResourceId") or "agrichain-schema-init",
        "StackId": event["StackId"],
        "RequestId": event["RequestId"],
        "LogicalResourceId": event["LogicalResourceId"],
        "Data": {},
    }).encode()
    req = urllib.request.Request(
        event["ResponseURL"], data=body, method="PUT", headers={"Content-Type": ""}
    )
    urllib.request.urlopen(req, timeout=20)


def handle_custom_resource(event, context):
    status, reason = "SUCCESS", ""
    try:
        if event["RequestType"] in ("Create", "Update"):
            init_schema()
            seed_admin_user(event.get("ResourceProperties", {}))
    except Exception as exc:  # always answer CloudFormation or the stack hangs for 1h
        print(f"Provisioning failed: {exc!r}")
        status, reason = "FAILED", str(exc)[:500]
    send_cfn_response(event, context, status, reason)


def lambda_handler(event, context):
    if "RequestType" in event and "ResponseURL" in event:
        return handle_custom_resource(event, context)
    try:
        return run_etl(event)
    except Exception as exc:
        print(f"ETL failed: {exc!r}")
        raise
