#!/usr/bin/env python3
"""Package and deploy the AgriChain stack to AWS (Learner Lab friendly).

Needs only Python 3 + boto3 and AWS credentials in the environment / ~/.aws
(copy them from "AWS Details" in the Learner Lab page).

    python infra/deploy.py --groq-key gsk_xxx --admin-password "Your-Login-Pass1"

What it does
  1. creates the artifacts bucket, stores the Groq key + DB password in SSM
     Parameter Store (SecureString) - they never appear in the template
  2. builds app.zip (Express + FastAPI) and lambda.zip (ETL, Linux wheels)
  3. creates/updates the CloudFormation stack and prints the site URL
"""
import argparse
import hashlib
import os
import secrets
import shutil
import string
import subprocess
import sys
import tempfile
import zipfile
from pathlib import Path

import boto3
from botocore.exceptions import ClientError

ROOT = Path(__file__).resolve().parent.parent
TEMPLATE = ROOT / "infra" / "agrichain-stack.yaml"
APP_EXCLUDE_DIRS = {".git", "node_modules", ".venv", "venv", "dataset", "tests", "infra",
                    "lambda", "assets", "__pycache__", ".pytest_cache", ".vscode", ".idea"}
APP_EXCLUDE_FILES = {".env", "package-handoff.bat", "setup.bat", "start.bat"}


def log(msg):
    print(f"==> {msg}", flush=True)


def build_app_zip(dest):
    with zipfile.ZipFile(dest, "w", zipfile.ZIP_DEFLATED) as zf:
        for path in sorted(ROOT.rglob("*")):
            rel = path.relative_to(ROOT)
            if path.is_dir() or set(rel.parts[:-1]) & APP_EXCLUDE_DIRS:
                continue
            if rel.name in APP_EXCLUDE_FILES or rel.suffix in {".pem", ".zip", ".pyc", ".log"}:
                continue
            zf.write(path, rel.as_posix())


def build_lambda_zip(dest):
    src = ROOT / "lambda" / "etl"
    with tempfile.TemporaryDirectory() as tmp:
        build = Path(tmp) / "pkg"
        log("Installing Lambda dependencies for Linux x86_64 / Python 3.12 (a minute or two)")
        subprocess.check_call([
            sys.executable, "-m", "pip", "install", "-q", "--target", str(build),
            "--platform", "manylinux2014_x86_64", "--platform", "manylinux_2_28_x86_64",
            "--python-version", "3.12", "--implementation", "cp", "--only-binary=:all:",
            "-r", str(src / "requirements.txt"),
        ])
        for junk in list(build.rglob("tests")) + list(build.rglob("__pycache__")):
            shutil.rmtree(junk, ignore_errors=True)
        for name in ("lambda_function.py", "schema.sql"):
            shutil.copy(src / name, build / name)
        with zipfile.ZipFile(dest, "w", zipfile.ZIP_DEFLATED) as zf:
            for path in build.rglob("*"):
                if path.is_file():
                    zf.write(path, path.relative_to(build).as_posix())


def sha8(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()[:8]


def get_or_create_param(ssm, name, value=None, generate=False):
    """Return the SecureString value, writing `value` (or a generated one) if given/missing."""
    if value is None:
        try:
            return ssm.get_parameter(Name=name, WithDecryption=True)["Parameter"]["Value"]
        except ClientError as exc:
            if exc.response["Error"]["Code"] != "ParameterNotFound" or not generate:
                raise SystemExit(f"SSM parameter {name} does not exist yet - pass its value on the command line")
            while True:  # Redshift requires at least one upper, one lower and one digit
                value = "".join(secrets.choice(string.ascii_letters + string.digits) for _ in range(20))
                if any(c.islower() for c in value) and any(c.isupper() for c in value) and any(c.isdigit() for c in value):
                    break
    ssm.put_parameter(Name=name, Value=value, Type="SecureString", Overwrite=True)
    return value


def deploy_stack(cfn, name, params):
    body = TEMPLATE.read_text(encoding="utf-8")
    cfn_params = [{"ParameterKey": k, "ParameterValue": v} for k, v in params.items()]
    try:
        cfn.describe_stacks(StackName=name)
        exists = True
    except ClientError:
        exists = False
    try:
        if exists:
            log(f"Updating stack {name}")
            cfn.update_stack(StackName=name, TemplateBody=body, Parameters=cfn_params)
            waiter = cfn.get_waiter("stack_update_complete")
        else:
            log(f"Creating stack {name} (Redshift takes ~5-10 minutes)")
            cfn.create_stack(StackName=name, TemplateBody=body, Parameters=cfn_params,
                             OnFailure="DO_NOTHING" if os.environ.get("KEEP_ON_FAILURE") else "ROLLBACK")
            waiter = cfn.get_waiter("stack_create_complete")
    except ClientError as exc:
        if "No updates are to be performed" in str(exc):
            log("Stack already up to date")
            return
        raise
    try:
        waiter.wait(StackName=name, WaiterConfig={"Delay": 20, "MaxAttempts": 180})
    except Exception:
        for ev in cfn.describe_stack_events(StackName=name)["StackEvents"][:40]:
            if "FAILED" in ev["ResourceStatus"]:
                print(f"  {ev['LogicalResourceId']}: {ev.get('ResourceStatusReason')}")
        raise SystemExit("Stack deployment failed (see reasons above)")


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--stack-name", default="agrichain")
    ap.add_argument("--region", default=os.environ.get("AWS_DEFAULT_REGION", "us-east-1"))
    ap.add_argument("--groq-key", help="Groq API key (omit to reuse the one already in SSM)")
    ap.add_argument("--db-password", help="Redshift master password (needs upper+lower+digit), letters/digits, 12+ (default: generated once, kept in SSM)")
    ap.add_argument("--admin-username", default="admin")
    ap.add_argument("--admin-name", default="Administrator")
    ap.add_argument("--admin-password", required=True, help="password of the first web login")
    ap.add_argument("--key-name", default="", help="optional EC2 key pair for SSH, e.g. vockey")
    ap.add_argument("--ssh-cidr", default="", help="optional CIDR allowed to SSH")
    ap.add_argument("--capacity", default="2")
    ap.add_argument("--node-type", default="ra3.large", help="Redshift node type (Learner Lab: ra3.* / rg.*)")
    ap.add_argument("--nodes", default="1", help="Redshift node count (1 = single-node)")
    args = ap.parse_args()

    session = boto3.Session(region_name=args.region)
    account = session.client("sts").get_caller_identity()["Account"]
    s3, ssm, cfn = session.client("s3"), session.client("ssm"), session.client("cloudformation")

    bucket = f"{args.stack_name}-artifacts-{account}-{args.region}"
    log(f"Artifacts bucket: {bucket}")
    try:
        s3.head_bucket(Bucket=bucket)
    except ClientError:
        kw = {} if args.region == "us-east-1" else {
            "CreateBucketConfiguration": {"LocationConstraint": args.region}}
        s3.create_bucket(Bucket=bucket, **kw)
        s3.put_public_access_block(Bucket=bucket, PublicAccessBlockConfiguration={
            "BlockPublicAcls": True, "IgnorePublicAcls": True,
            "BlockPublicPolicy": True, "RestrictPublicBuckets": True})

    log("Storing secrets in SSM Parameter Store")
    db_param, groq_param = f"/{args.stack_name}/db_password", f"/{args.stack_name}/groq_api_key"
    db_password = get_or_create_param(ssm, db_param, args.db_password, generate=True)
    get_or_create_param(ssm, groq_param, args.groq_key)

    with tempfile.TemporaryDirectory() as tmp:
        app_zip, lam_zip = Path(tmp, "app.zip"), Path(tmp, "lambda.zip")
        log("Packaging application")
        build_app_zip(app_zip)
        build_lambda_zip(lam_zip)
        app_key, lam_key = f"app/app-{sha8(app_zip)}.zip", f"lambda/etl-{sha8(lam_zip)}.zip"
        for path, key in ((app_zip, app_key), (lam_zip, lam_key)):
            log(f"Uploading s3://{bucket}/{key} ({path.stat().st_size / 1e6:.1f} MB)")
            s3.upload_file(str(path), bucket, key)

    params = {
        "ProjectName": args.stack_name, "ArtifactsBucket": bucket,
        "AppZipKey": app_key, "LambdaZipKey": lam_key,
        "DBPassword": db_password, "DbPasswordParam": db_param, "GroqApiKeyParam": groq_param,
        "AdminUsername": args.admin_username, "AdminName": args.admin_name,
        "AdminPassword": args.admin_password, "KeyName": args.key_name, "SshCidr": args.ssh_cidr,
        "DesiredCapacity": args.capacity, "RedshiftNodeType": args.node_type, "RedshiftNodes": args.nodes,
    }
    deploy_stack(cfn, args.stack_name, params)

    outputs = cfn.describe_stacks(StackName=args.stack_name)["Stacks"][0].get("Outputs", [])
    print()
    for out in outputs:
        print(f"{out['OutputKey']:>18}: {out['OutputValue']}")
    print("\nInstances need ~5 more minutes to install and pass ALB health checks.")


if __name__ == "__main__":
    main()
