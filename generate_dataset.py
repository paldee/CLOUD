"""
Agriculture Supply Chain Data Warehouse — Dataset Generator
===========================================================
สร้าง 8 ไฟล์ CSV จำลองสำหรับ ETL Pipeline ของโครงการ
รวม ~170,000 records ครอบคลุมข้อมูล 5 ปี (2021-2025)
"""

import csv
import os
import uuid
import random
from datetime import date, timedelta, datetime
import sys

sys.stdout.reconfigure(encoding='utf-8')
random.seed(42)

# ===========================================================
# OUTPUT DIRECTORY
# ===========================================================
BASE_DIR = r"d:\kmitl\cloud\project\dataset"
MASTER_DIR = os.path.join(BASE_DIR, "master")
OPERATIONAL_DIR = os.path.join(BASE_DIR, "operational")
os.makedirs(MASTER_DIR, exist_ok=True)
os.makedirs(OPERATIONAL_DIR, exist_ok=True)

# ===========================================================
# REFERENCE DATA (จากข้อมูลจริงของไทย)
# ===========================================================

# จังหวัดไทยจริงพร้อมภูมิภาค (ดึงจากข้อมูลข้าวนาปรัง/ยางพารา)
PROVINCES = [
    # ภาคเหนือ
    ("เชียงราย", "ภาคเหนือ"), ("เชียงใหม่", "ภาคเหนือ"), ("ลำปาง", "ภาคเหนือ"),
    ("ลำพูน", "ภาคเหนือ"), ("แพร่", "ภาคเหนือ"), ("น่าน", "ภาคเหนือ"),
    ("พะเยา", "ภาคเหนือ"), ("แม่ฮ่องสอน", "ภาคเหนือ"), ("ตาก", "ภาคเหนือ"),
    ("พิษณุโลก", "ภาคเหนือ"), ("สุโขทัย", "ภาคเหนือ"), ("อุตรดิตถ์", "ภาคเหนือ"),
    ("กำแพงเพชร", "ภาคเหนือ"), ("พิจิตร", "ภาคเหนือ"), ("เพชรบูรณ์", "ภาคเหนือ"),
    ("นครสวรรค์", "ภาคเหนือ"), ("อุทัยธานี", "ภาคเหนือ"),
    # ภาคตะวันออกเฉียงเหนือ
    ("นครราชสีมา", "ภาคตะวันออกเฉียงเหนือ"), ("อุบลราชธานี", "ภาคตะวันออกเฉียงเหนือ"),
    ("ขอนแก่น", "ภาคตะวันออกเฉียงเหนือ"), ("สกลนคร", "ภาคตะวันออกเฉียงเหนือ"),
    ("อุดรธานี", "ภาคตะวันออกเฉียงเหนือ"), ("บุรีรัมย์", "ภาคตะวันออกเฉียงเหนือ"),
    ("สุรินทร์", "ภาคตะวันออกเฉียงเหนือ"), ("ศรีสะเกษ", "ภาคตะวันออกเฉียงเหนือ"),
    ("ร้อยเอ็ด", "ภาคตะวันออกเฉียงเหนือ"), ("มหาสารคาม", "ภาคตะวันออกเฉียงเหนือ"),
    ("กาฬสินธุ์", "ภาคตะวันออกเฉียงเหนือ"), ("ชัยภูมิ", "ภาคตะวันออกเฉียงเหนือ"),
    ("เลย", "ภาคตะวันออกเฉียงเหนือ"), ("หนองบัวลำภู", "ภาคตะวันออกเฉียงเหนือ"),
    ("หนองคาย", "ภาคตะวันออกเฉียงเหนือ"), ("มุกดาหาร", "ภาคตะวันออกเฉียงเหนือ"),
    ("นครพนม", "ภาคตะวันออกเฉียงเหนือ"), ("ยโสธร", "ภาคตะวันออกเฉียงเหนือ"),
    ("อำนาจเจริญ", "ภาคตะวันออกเฉียงเหนือ"), ("บึงกาฬ", "ภาคตะวันออกเฉียงเหนือ"),
    # ภาคกลาง
    ("กรุงเทพมหานคร", "ภาคกลาง"), ("สุพรรณบุรี", "ภาคกลาง"),
    ("ชัยนาท", "ภาคกลาง"), ("สิงห์บุรี", "ภาคกลาง"), ("อ่างทอง", "ภาคกลาง"),
    ("อยุธยา", "ภาคกลาง"), ("ลพบุรี", "ภาคกลาง"), ("สระบุรี", "ภาคกลาง"),
    ("ปทุมธานี", "ภาคกลาง"), ("นนทบุรี", "ภาคกลาง"), ("นครปฐม", "ภาคกลาง"),
    ("ราชบุรี", "ภาคกลาง"), ("กาญจนบุรี", "ภาคกลาง"),
    # ภาคตะวันออก
    ("ชลบุรี", "ภาคตะวันออก"), ("ระยอง", "ภาคตะวันออก"), ("จันทบุรี", "ภาคตะวันออก"),
    ("ตราด", "ภาคตะวันออก"), ("ฉะเชิงเทรา", "ภาคตะวันออก"), ("ปราจีนบุรี", "ภาคตะวันออก"),
    ("นครนายก", "ภาคตะวันออก"), ("สระแก้ว", "ภาคตะวันออก"),
    # ภาคใต้
    ("สงขลา", "ภาคใต้"), ("สุราษฎร์ธานี", "ภาคใต้"), ("นครศรีธรรมราช", "ภาคใต้"),
    ("ชุมพร", "ภาคใต้"), ("ระนอง", "ภาคใต้"), ("กระบี่", "ภาคใต้"),
    ("พังงา", "ภาคใต้"), ("ภูเก็ต", "ภาคใต้"), ("ตรัง", "ภาคใต้"),
    ("พัทลุง", "ภาคใต้"), ("สตูล", "ภาคใต้"), ("ปัตตานี", "ภาคใต้"),
    ("ยะลา", "ภาคใต้"), ("นราธิวาส", "ภาคใต้"),
]

# พืชเศรษฐกิจไทยจาก source data จริง พร้อม metadata
CROPS_DATA = [
    # crop_name, category, unit, price_min, price_max, harvest_months
    ("ข้าวนาปรัง",  "ธัญพืช",      "กิโลกรัม", 8.0,  13.0,  [1, 2, 3, 4, 5]),
    ("ข้าวนาปี",    "ธัญพืช",      "กิโลกรัม", 8.0,  13.0,  [10, 11, 12, 1]),
    ("ข้าวหอมมะลิ", "ธัญพืช",      "กิโลกรัม", 14.0, 22.0,  [10, 11, 12, 1]),
    ("ข้าวโพดเลี้ยงสัตว์", "ธัญพืช", "กิโลกรัม", 7.0,  11.0,  [3, 4, 5, 6, 7, 8]),
    ("มันสำปะหลัง", "พืชหัว",      "กิโลกรัม", 2.5,  4.0,   [2, 3, 4, 5, 6]),
    ("ยางพารา",     "พืชยืนต้น",   "กิโลกรัม", 50.0, 80.0,  [1,2,3,4,5,6,7,8,9,10,11,12]),
    ("ปาล์มน้ำมัน", "พืชยืนต้น",   "กิโลกรัม", 4.0,  7.0,   [1,2,3,4,5,6,7,8,9,10,11,12]),
    ("ลิ้นจี่",     "ผลไม้",       "กิโลกรัม", 40.0, 80.0,  [4, 5, 6]),
    ("ลำไย",        "ผลไม้",       "กิโลกรัม", 20.0, 45.0,  [7, 8, 9]),
    ("ทุเรียน",     "ผลไม้",       "กิโลกรัม", 80.0, 200.0, [4, 5, 6, 7]),
    ("มังคุด",      "ผลไม้",       "กิโลกรัม", 40.0, 90.0,  [5, 6, 7, 8]),
    ("อ้อย",        "พืชอุตสาหกรรม","กิโลกรัม", 1.0,  1.5,   [11, 12, 1, 2, 3]),
    ("สับปะรด",     "ผลไม้",       "กิโลกรัม", 5.0,  12.0,  [3, 4, 5, 6, 7]),
    ("กาแฟ",        "พืชไร่",      "กิโลกรัม", 60.0, 120.0, [11, 12, 1, 2]),
    ("ข้าวฟ่าง",    "ธัญพืช",      "กิโลกรัม", 6.0,  9.0,   [7, 8, 9, 10]),
]

# ชื่อสหกรณ์จริงในไทย
COOPERATIVES = [
    "สหกรณ์การเกษตรเชียงราย จำกัด",
    "สหกรณ์การเกษตรนครราชสีมา จำกัด",
    "สหกรณ์การเกษตรขอนแก่น จำกัด",
    "สหกรณ์การเกษตรสุราษฎร์ธานี จำกัด",
    "สหกรณ์การเกษตรสงขลา จำกัด",
    "สหกรณ์ชาวสวนยางระยอง จำกัด",
    "สหกรณ์ชาวสวนปาล์มชุมพร จำกัด",
    "สหกรณ์การเกษตรลำปาง จำกัด",
    "สหกรณ์การเกษตรอุบลราชธานี จำกัด",
    "สหกรณ์การเกษตรสุพรรณบุรี จำกัด",
]

# ชื่อลูกค้า (บริษัทรับซื้อผลผลิตเกษตร)
CUSTOMER_TYPES = ["ผู้ส่งออก", "โรงงานแปรรูป", "ตลาดค้าส่ง", "ห้างค้าปลีก", "สหกรณ์ผู้บริโภค"]
COMPANY_PREFIXES = ["บริษัท", "ห้างหุ้นส่วน", "สหกรณ์"]
COMPANY_SUFFIXES = ["จำกัด", "จำกัด (มหาชน)"]

# ===========================================================
# HELPER FUNCTIONS
# ===========================================================

def random_date(start_year=2021, end_year=2025):
    start = date(start_year, 1, 1)
    end = date(end_year, 12, 31)
    return start + timedelta(days=random.randint(0, (end - start).days))

def random_date_in_months(year, months):
    month = random.choice(months)
    # Handle cross-year: month 1 in Jan might be previous year's harvest for napi
    day = random.randint(1, 28)
    try:
        return date(year, month, day)
    except:
        return date(year, month, 28)

def gen_id(prefix):
    return f"{prefix}-{str(uuid.uuid4())[:8].upper()}"

def round2(x):
    return round(x, 2)

def random_thai_first_name():
    firsts = ["สมชาย", "สมหญิง", "วิชัย", "สุดา", "ประสิทธิ์", "มาลี", "สมพงษ์", "ลัดดา",
              "ชาญชัย", "กมลา", "วิทยา", "นภา", "อนันต์", "ศิริ", "ธวัช", "จันทร์",
              "สุชาติ", "นงลักษณ์", "พิชัย", "สุนิสา", "เอกชัย", "รัตนา", "อาทิตย์",
              "มณีรัตน์", "วรากร", "ปิยะ", "กิตติ", "สายฝน", "ชัยวัฒน์", "นฤมล",
              "บุญมา", "ทองสุข", "ณรงค์", "เกษม", "วีระ", "ปราณี", "สุรศักดิ์", "ดวงดาว",
              "ฉัตรชัย", "สมบัติ", "ธนกร", "ปรียา", "ยุทธนา", "นิตยา", "จักรกฤษณ์"]
    lasts = ["ใจดี", "มีสุข", "ทองดี", "ศรีสุข", "สมบูรณ์", "รักษ์ดี", "ดวงดี", "แสงงาม",
             "บุญมา", "สาระ", "ชูชื่น", "มั่งมี", "สุขใจ", "เจริญสุข", "ดีงาม", "พิมพา",
             "ทองแดง", "สีทอง", "เพชรดี", "ดำรง", "มงคล", "โชคดี", "ฤทธิ์ไกร", "พลัง",
             "เกษตรดี", "ทรัพย์มา", "รุ่งโรจน์", "วงศ์งาม", "ดาวเรือง", "พันธ์ดี"]
    return f"{random.choice(firsts)} {random.choice(lasts)}"

def random_company_name():
    prefixes = ["อาหารไทย", "เกษตรก้าวหน้า", "ทองคำเขียว", "ไทยพืชผล", "ชัยภูมิค้าส่ง",
                "สยามฟู้ด", "ไทยอุตสาหกรรม", "เจริญผล", "ธรรมชาติไทย", "สุวรรณภูมิ",
                "อีสานค้าส่ง", "ใต้ดีผลไม้", "เหนือดีข้าว", "แม่โขงการเกษตร", "เจ้าพระยาผล",
                "ทิพย์ผลไทย", "บุญเพิ่มเกษตร", "ศรีไทยค้าส่ง", "รุ่งโรจน์ฟาร์ม", "วิบูลย์พืชผล"]
    return f"บริษัท {random.choice(prefixes)} จำกัด"

# ===========================================================
# 1. MASTER DATA — CROP
# ===========================================================
print("=== Generating Crop.csv ===")
crops = []
for i, (name, category, unit, pmin, pmax, months) in enumerate(CROPS_DATA, 1):
    crops.append({
        "crop_id": f"CRP-{i:03d}",
        "crop_name": name,
        "category": category,
        "unit": unit,
        "standard_price_per_unit": round2(random.uniform(pmin, pmax)),
        "season_months": ",".join(map(str, months)),
        "shelf_life_days": random.choice([7, 14, 30, 60, 180, 365]),
        "is_active": "Y",
    })

crop_fields = ["crop_id", "crop_name", "category", "unit", "standard_price_per_unit",
               "season_months", "shelf_life_days", "is_active"]
with open(os.path.join(MASTER_DIR, "Crop.csv"), "w", newline="", encoding="utf-8-sig") as f:
    w = csv.DictWriter(f, fieldnames=crop_fields)
    w.writeheader()
    w.writerows(crops)
print(f"  Crop.csv: {len(crops)} records ✓")

# ===========================================================
# 2. MASTER DATA — WAREHOUSE
# ===========================================================
print("=== Generating Warehouse.csv ===")
warehouse_provinces = [
    ("เชียงใหม่", "ภาคเหนือ"), ("ลำปาง", "ภาคเหนือ"), ("พิษณุโลก", "ภาคเหนือ"),
    ("ขอนแก่น", "ภาคตะวันออกเฉียงเหนือ"), ("นครราชสีมา", "ภาคตะวันออกเฉียงเหนือ"),
    ("อุบลราชธานี", "ภาคตะวันออกเฉียงเหนือ"), ("อุดรธานี", "ภาคตะวันออกเฉียงเหนือ"),
    ("กรุงเทพมหานคร", "ภาคกลาง"), ("สุพรรณบุรี", "ภาคกลาง"), ("อยุธยา", "ภาคกลาง"),
    ("ชลบุรี", "ภาคตะวันออก"), ("ระยอง", "ภาคตะวันออก"), ("จันทบุรี", "ภาคตะวันออก"),
    ("สุราษฎร์ธานี", "ภาคใต้"), ("สงขลา", "ภาคใต้"),
]
warehouses = []
for i, (prov, region) in enumerate(warehouse_provinces, 1):
    cap = random.choice([500, 1000, 1500, 2000, 3000, 5000])
    warehouses.append({
        "warehouse_id": f"WH-{i:03d}",
        "warehouse_name": f"คลังสินค้า{prov}",
        "province": prov,
        "region": region,
        "address": f"เลขที่ {random.randint(1,999)} ถ.เกษตรกลาง {prov}",
        "capacity_ton": cap,
        "current_utilization_pct": round2(random.uniform(40, 85)),
        "manager_name": random_thai_first_name(),
        "contact_phone": f"0{random.randint(800000000, 999999999)}",
        "is_active": "Y",
    })

wh_fields = ["warehouse_id", "warehouse_name", "province", "region", "address",
             "capacity_ton", "current_utilization_pct", "manager_name", "contact_phone", "is_active"]
with open(os.path.join(MASTER_DIR, "Warehouse.csv"), "w", newline="", encoding="utf-8-sig") as f:
    w = csv.DictWriter(f, fieldnames=wh_fields)
    w.writeheader()
    w.writerows(warehouses)
print(f"  Warehouse.csv: {len(warehouses)} records ✓")

# ===========================================================
# 3. MASTER DATA — FARMER
# ===========================================================
print("=== Generating Farmer.csv ===")
farmers = []
farmer_provinces = [p for p, r in PROVINCES]
for i in range(1, 301):
    prov = random.choice(farmer_provinces)
    region = next(r for p, r in PROVINCES if p == prov)
    reg_year = random.randint(2015, 2022)
    reg_date = date(reg_year, random.randint(1, 12), random.randint(1, 28))
    farmers.append({
        "farmer_id": f"FRM-{i:04d}",
        "farmer_name": random_thai_first_name(),
        "national_id": f"{random.randint(1000000000000, 9999999999999)}",
        "province": prov,
        "region": region,
        "district": f"อ.{random.choice(['เมือง','บ้านโฮ่ง','ป่าซาง','วังเหนือ','แม่ทะ'])}",
        "cooperative": random.choice(COOPERATIVES),
        "farm_size_rai": round2(random.uniform(5, 200)),
        "primary_crop": random.choice([c["crop_name"] for c in crops]),
        "registration_date": str(reg_date),
        "status": random.choices(["ใช้งาน", "ไม่ใช้งาน"], weights=[95, 5])[0],
        "phone": f"0{random.randint(800000000, 999999999)}",
    })

farmer_fields = ["farmer_id", "farmer_name", "national_id", "province", "region",
                 "district", "cooperative", "farm_size_rai", "primary_crop",
                 "registration_date", "status", "phone"]
with open(os.path.join(MASTER_DIR, "Farmer.csv"), "w", newline="", encoding="utf-8-sig") as f:
    w = csv.DictWriter(f, fieldnames=farmer_fields)
    w.writeheader()
    w.writerows(farmers)
print(f"  Farmer.csv: {len(farmers)} records ✓")

# ===========================================================
# 4. MASTER DATA — CUSTOMER
# ===========================================================
print("=== Generating Customer.csv ===")
customers = []
for i in range(1, 201):
    prov, region = random.choice(PROVINCES)
    ctype = random.choice(CUSTOMER_TYPES)
    customers.append({
        "customer_id": f"CUS-{i:04d}",
        "customer_name": random_company_name(),
        "customer_type": ctype,
        "province": prov,
        "region": region,
        "contact_person": random_thai_first_name(),
        "phone": f"0{random.randint(800000000, 999999999)}",
        "email": f"contact{i}@agri-buyer.co.th",
        "credit_limit_thb": random.choice([50000, 100000, 200000, 500000, 1000000]),
        "is_active": random.choices(["Y", "N"], weights=[92, 8])[0],
    })

cus_fields = ["customer_id", "customer_name", "customer_type", "province", "region",
              "contact_person", "phone", "email", "credit_limit_thb", "is_active"]
with open(os.path.join(MASTER_DIR, "Customer.csv"), "w", newline="", encoding="utf-8-sig") as f:
    w = csv.DictWriter(f, fieldnames=cus_fields)
    w.writeheader()
    w.writerows(customers)
print(f"  Customer.csv: {len(customers)} records ✓")

# ===========================================================
# PREPARE ID LISTS FOR FK
# ===========================================================
crop_ids = [c["crop_id"] for c in crops]
crop_by_id = {c["crop_id"]: c for c in crops}
farmer_ids = [f["farmer_id"] for f in farmers]
wh_ids = [w["warehouse_id"] for w in warehouses]
cus_ids = [c["customer_id"] for c in customers if c["is_active"] == "Y"]

# crop harvest months lookup
crop_months = {c["crop_id"]: list(map(int, c["season_months"].split(","))) for c in crops}
crop_price_range = {}
for i, (name, cat, unit, pmin, pmax, months) in enumerate(CROPS_DATA, 1):
    crop_price_range[f"CRP-{i:03d}"] = (pmin, pmax)

# ===========================================================
# 5. OPERATIONAL DATA — HARVEST
# ===========================================================
print("=== Generating Harvest.csv (50,000 records) ===")
harvests = []
for i in range(1, 50001):
    farmer_id = random.choice(farmer_ids)
    crop_id = random.choice(crop_ids)
    months = crop_months[crop_id]
    year = random.randint(2021, 2025)
    h_date = random_date_in_months(year, months)
    pmin, pmax = crop_price_range[crop_id]
    # quantity ขึ้นอยู่กับประเภทพืช
    category = crop_by_id[crop_id]["category"]
    if category == "ธัญพืช":
        qty = round2(random.uniform(500, 20000))
    elif category == "พืชยืนต้น":
        qty = round2(random.uniform(100, 5000))
    elif category == "ผลไม้":
        qty = round2(random.uniform(200, 8000))
    elif category == "พืชหัว":
        qty = round2(random.uniform(1000, 30000))
    elif category == "พืชอุตสาหกรรม":
        qty = round2(random.uniform(2000, 50000))
    else:
        qty = round2(random.uniform(200, 5000))
    price = round2(random.uniform(pmin, pmax))
    total = round2(qty * price)
    # รับเข้าคลังที่ใกล้จังหวัดเกษตรกร — เลือก warehouse แบบ random
    wh_id = random.choice(wh_ids)
    harvests.append({
        "harvest_id": f"HRV-{i:06d}",
        "farmer_id": farmer_id,
        "crop_id": crop_id,
        "warehouse_id": wh_id,
        "harvest_date": str(h_date),
        "quantity_kg": qty,
        "price_per_kg": price,
        "total_amount_thb": total,
        "quality_grade": random.choice(["A", "A", "A", "B", "B", "C"]),
        "inspector_note": random.choice(["ผ่านการตรวจสอบ", "ผ่านการตรวจสอบ", "ผ่านการตรวจสอบ",
                                         "คุณภาพดี", "คุณภาพปานกลาง", "ต้องตรวจซ้ำ"]),
    })

harvest_fields = ["harvest_id", "farmer_id", "crop_id", "warehouse_id", "harvest_date",
                  "quantity_kg", "price_per_kg", "total_amount_thb", "quality_grade", "inspector_note"]
with open(os.path.join(OPERATIONAL_DIR, "Harvest.csv"), "w", newline="", encoding="utf-8-sig") as f:
    w = csv.DictWriter(f, fieldnames=harvest_fields)
    w.writeheader()
    w.writerows(harvests)
print(f"  Harvest.csv: {len(harvests)} records ✓")

# ===========================================================
# 6. OPERATIONAL DATA — INVENTORY (Daily Snapshot)
# ===========================================================
print("=== Generating Inventory.csv (~65,000 records) ===")
# สร้าง daily snapshot: สุ่มเลือก crop-warehouse pairs แล้วสร้าง snapshot รายวัน
# เพื่อให้ได้ ~18,000 records: 15 WH × 10 crops × ~120 วัน/crop-wh pair
inventory_records = []
inv_id = 1

# สร้าง crop-warehouse combinations ที่สมเหตุสมผล
# แต่ละ warehouse จะเก็บ crop หลาย ๆ ชนิด
wh_crop_pairs = []
for wh in warehouses:
    # แต่ละคลังเก็บ 10-14 ชนิดพืช (เพิ่มจากเดิม)
    n_crops = random.randint(10, 14)
    selected_crops = random.sample(crop_ids, n_crops)
    for cid in selected_crops:
        wh_crop_pairs.append((wh["warehouse_id"], cid))

# สร้าง snapshot รายวัน ต่อ pair
# target: ~65,000 รายการ
# 15 WH × 12 crops avg = 180 pairs, ต้องการ 65000/180 ≈ 361 วัน ต่อ pair
target_per_pair = 65000 // len(wh_crop_pairs)
if target_per_pair < 100:
    target_per_pair = 100

total_days = (date(2025, 12, 31) - date(2021, 1, 1)).days
# ใช้ทุก 3 วัน (tri-daily) เพื่อให้ได้ records มากขึ้น
all_dates_pool = [date(2021, 1, 1) + timedelta(days=d) for d in range(0, total_days, 3)]

for wh_id, c_id in wh_crop_pairs:
    # สุ่มช่วงวันที่และสร้าง snapshot
    pmin, pmax = crop_price_range[c_id]
    beginning_stock = round2(random.uniform(0, 50000))
    snap_dates = sorted(random.sample(all_dates_pool, min(target_per_pair, len(all_dates_pool))))
    stock = beginning_stock
    for snap_date in snap_dates:
        received = round2(random.uniform(0, 10000))
        sold = round2(random.uniform(0, min(stock + received, 8000)))
        ending = round2(max(0, stock + received - sold))
        inventory_records.append({
            "inventory_id": f"INV-{inv_id:06d}",
            "warehouse_id": wh_id,
            "crop_id": c_id,
            "snapshot_date": str(snap_date),
            "beginning_stock_kg": round2(stock),
            "received_kg": received,
            "sold_kg": sold,
            "ending_stock_kg": ending,
            "unit_cost_thb": round2(random.uniform(pmin * 0.8, pmax * 0.9)),
            "stock_status": "ต่ำ" if ending < 500 else ("ปกติ" if ending < 20000 else "สูง"),
        })
        inv_id += 1
        stock = ending

inv_fields = ["inventory_id", "warehouse_id", "crop_id", "snapshot_date",
              "beginning_stock_kg", "received_kg", "sold_kg", "ending_stock_kg",
              "unit_cost_thb", "stock_status"]
with open(os.path.join(OPERATIONAL_DIR, "Inventory.csv"), "w", newline="", encoding="utf-8-sig") as f:
    w = csv.DictWriter(f, fieldnames=inv_fields)
    w.writeheader()
    w.writerows(inventory_records)
print(f"  Inventory.csv: {len(inventory_records)} records ✓")

# ===========================================================
# 7. OPERATIONAL DATA — SHIPMENT
# ===========================================================
print("=== Generating Shipment.csv (25,000 records) ===")
shipment_statuses = ["จัดส่งแล้ว", "จัดส่งแล้ว", "จัดส่งแล้ว", "กำลังขนส่ง", "รอดำเนินการ", "ยกเลิก"]
transport_modes = ["รถบรรทุก", "รถบรรทุก", "รถบรรทุก", "รถไฟ", "เรือ"]
shipments = []
for i in range(1, 25001):
    wh_id = random.choice(wh_ids)
    cus_id = random.choice(cus_ids)
    s_date = random_date(2021, 2025)
    # delivery date: 1-14 วันหลังจาก shipment date
    delivery_days = random.randint(1, 14)
    d_date = s_date + timedelta(days=delivery_days)
    status = random.choices(
        ["จัดส่งแล้ว", "กำลังขนส่ง", "รอดำเนินการ", "ยกเลิก"],
        weights=[70, 15, 10, 5]
    )[0]
    # ถ้าสถานะยังไม่ส่ง delivery_date อาจยังไม่มี
    if status in ["รอดำเนินการ"]:
        d_date = None
    weight = round2(random.uniform(500, 30000))
    cost = round2(weight * random.uniform(0.5, 2.5))
    # crop ที่จัดส่ง
    crop_id = random.choice(crop_ids)
    shipments.append({
        "shipment_id": f"SHP-{i:06d}",
        "warehouse_id": wh_id,
        "customer_id": cus_id,
        "crop_id": crop_id,
        "shipment_date": str(s_date),
        "delivery_date": str(d_date) if d_date else "",
        "status": status,
        "total_weight_kg": weight,
        "shipping_cost_thb": cost,
        "transport_mode": random.choice(transport_modes),
        "driver_name": random_thai_first_name(),
        "vehicle_plate": f"{random.choice(['กก','ขข','งง','ฉฉ','ชช'])}-{random.randint(1000,9999)} {random.choice(['กทม','ชม','ขก','สข','สง'])}",
    })

shp_fields = ["shipment_id", "warehouse_id", "customer_id", "crop_id",
              "shipment_date", "delivery_date", "status", "total_weight_kg",
              "shipping_cost_thb", "transport_mode", "driver_name", "vehicle_plate"]
with open(os.path.join(OPERATIONAL_DIR, "Shipment.csv"), "w", newline="", encoding="utf-8-sig") as f:
    w = csv.DictWriter(f, fieldnames=shp_fields)
    w.writeheader()
    w.writerows(shipments)
print(f"  Shipment.csv: {len(shipments)} records ✓")

# ===========================================================
# 8. OPERATIONAL DATA — SALES
# ===========================================================
print("=== Generating Sales.csv (30,000 records) ===")
sales = []
# สร้าง orders แต่ละ order มี 1-4 order lines (crops)
order_num = 1
sale_id = 1
while sale_id <= 30000:
    cus_id = random.choice(cus_ids)
    order_date = random_date(2021, 2025)
    order_id = f"ORD-{order_num:06d}"
    n_lines = random.randint(1, 4)
    chosen_crops = random.sample(crop_ids, min(n_lines, len(crop_ids)))
    for crop_id in chosen_crops:
        pmin, pmax = crop_price_range[crop_id]
        category = crop_by_id[crop_id]["category"]
        if category == "ธัญพืช":
            qty = round2(random.uniform(100, 10000))
        elif category == "ผลไม้":
            qty = round2(random.uniform(50, 3000))
        elif category == "พืชยืนต้น":
            qty = round2(random.uniform(50, 2000))
        else:
            qty = round2(random.uniform(100, 8000))
        unit_price = round2(random.uniform(pmin * 1.1, pmax * 1.3))  # ราคาขายสูงกว่าซื้อ
        total = round2(qty * unit_price)
        wh_id = random.choice(wh_ids)
        # payment status
        payment_status = random.choices(
            ["ชำระแล้ว", "ค้างชำระ", "บางส่วน"],
            weights=[75, 15, 10]
        )[0]
        sales.append({
            "sales_id": f"SAL-{sale_id:06d}",
            "order_id": order_id,
            "customer_id": cus_id,
            "crop_id": crop_id,
            "warehouse_id": wh_id,
            "sale_date": str(order_date),
            "quantity_kg": qty,
            "unit_price_thb": unit_price,
            "total_amount_thb": total,
            "discount_pct": round2(random.choices([0, 0, 0, 2, 5, 10], weights=[50,20,15,8,5,2])[0]),
            "payment_status": payment_status,
            "sale_channel": random.choice(["ตลาดกลาง", "สัญญาซื้อขาย", "ออนไลน์", "ตรงจากคลัง"]),
        })
        sale_id += 1
        if sale_id > 30000:
            break
    order_num += 1

sales_fields = ["sales_id", "order_id", "customer_id", "crop_id", "warehouse_id",
                "sale_date", "quantity_kg", "unit_price_thb", "total_amount_thb",
                "discount_pct", "payment_status", "sale_channel"]
with open(os.path.join(OPERATIONAL_DIR, "Sales.csv"), "w", newline="", encoding="utf-8-sig") as f:
    w = csv.DictWriter(f, fieldnames=sales_fields)
    w.writeheader()
    w.writerows(sales)
print(f"  Sales.csv: {len(sales)} records ✓")

# ===========================================================
# SUMMARY
# ===========================================================
total = len(crops) + len(farmers) + len(warehouses) + len(customers) + \
        len(harvests) + len(inventory_records) + len(shipments) + len(sales)
print()
print("=" * 50)
print("DATASET GENERATION COMPLETE")
print("=" * 50)
print(f"Output directory : {BASE_DIR}")
print()
print("Master Data:")
print(f"  Crop.csv      : {len(crops):>6,} records")
print(f"  Farmer.csv    : {len(farmers):>6,} records")
print(f"  Warehouse.csv : {len(warehouses):>6,} records")
print(f"  Customer.csv  : {len(customers):>6,} records")
print()
print("Operational Data:")
print(f"  Harvest.csv   : {len(harvests):>6,} records")
print(f"  Inventory.csv : {len(inventory_records):>6,} records")
print(f"  Shipment.csv  : {len(shipments):>6,} records")
print(f"  Sales.csv     : {len(sales):>6,} records")
print()
print(f"  TOTAL         : {total:>6,} records")
print("=" * 50)

# ===========================================================
# QUICK VALIDATION
# ===========================================================
print()
print("=== Quick Validation ===")
# Business Rule: harvest quantity > 0
invalid_harvest = [h for h in harvests if h["quantity_kg"] <= 0 or h["price_per_kg"] <= 0]
print(f"  Harvest (qty>0, price>0): {'PASS' if not invalid_harvest else f'FAIL ({len(invalid_harvest)} invalid)'}")

# Business Rule: inventory stock >= 0
invalid_inv = [r for r in inventory_records if r["ending_stock_kg"] < 0]
print(f"  Inventory (stock>=0): {'PASS' if not invalid_inv else f'FAIL ({len(invalid_inv)} negative stock)'}")

# Business Rule: delivery_date >= shipment_date
invalid_shp = []
for s in shipments:
    if s["delivery_date"] and s["shipment_date"]:
        if s["delivery_date"] < s["shipment_date"]:
            invalid_shp.append(s)
print(f"  Shipment (delivery>=shipment): {'PASS' if not invalid_shp else f'FAIL ({len(invalid_shp)} invalid dates)'}")

# Business Rule: sales quantity > 0, price > 0
invalid_sales = [s for s in sales if s["quantity_kg"] <= 0 or s["unit_price_thb"] <= 0]
print(f"  Sales (qty>0, price>0): {'PASS' if not invalid_sales else f'FAIL ({len(invalid_sales)} invalid)'}")

# FK check: all farmer_id in harvest exist in Farmer
farmer_set = set(farmer_ids)
fk_harvest = [h for h in harvests if h["farmer_id"] not in farmer_set]
print(f"  Harvest FK farmer_id: {'PASS' if not fk_harvest else f'FAIL ({len(fk_harvest)} invalid FK)'}")

# FK check: all warehouse_id in inventory exist in Warehouse
wh_set = set(wh_ids)
fk_inv = [r for r in inventory_records if r["warehouse_id"] not in wh_set]
print(f"  Inventory FK warehouse_id: {'PASS' if not fk_inv else f'FAIL ({len(fk_inv)} invalid FK)'}")

print()
print("Validation complete.")
