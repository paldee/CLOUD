# Agriculture Supply Chain Data Warehouse Platform 🌾🚜

**Project Concept:** Single Source of Truth (SSOT) สำหรับ Data Warehouse เพื่อการวิเคราะห์ข้อมูล supply chain ของสหกรณ์การเกษตร

![AWS Architecture](cloud_archetec_lastversion.png)

## 📌 Project Overview
โปรเจคนี้คือการสร้างต้นแบบ Data Warehouse บนระบบคลาวด์ (AWS) สำหรับสหกรณ์การเกษตรที่มีการรับซื้อผลผลิตจากเกษตรกรและส่งต่อให้ลูกค้า โดยการรวบรวมข้อมูลจากหลายส่วน (Operational Data) นำมาทำ ETL (Extract, Transform, Load) และเก็บไว้ในคลังข้อมูลส่วนกลางเพื่อสร้าง Dashboard สำหรับผู้บริหารผ่าน Power BI

### เป้าหมายหลัก
- ออกแบบและสร้าง **ETL Pipeline** อย่างสมบูรณ์
- จัดเก็บข้อมูลในรูปแบบ **Star Schema Data Warehouse**
- Deploy ระบบบน **AWS Cloud Infrastructure**
- สร้าง **Business Intelligence (BI) Dashboard** เพื่อวิเคราะห์ข้อมูล

---

## 📊 Dataset (ข้อมูลจำลอง)
ข้อมูลถูกจำลองขึ้นโดยอ้างอิงจากราคา, ฤดูกาล, และพื้นที่เกษตรกรรมจริงของประเทศไทย (อ้างอิงช่วงปี 2021-2025) มีปริมาณข้อมูลรวมประมาณ **170,000+ records**

แบ่งออกเป็น 2 กลุ่มหลัก ได้แก่:

### 1. Master Data (ข้อมูลหลัก)
| ไฟล์ | จำนวน (Records) | คำอธิบาย |
|------|-----------------|----------|
| `Crop.csv` | 15 | ข้อมูลผลผลิตทางการเกษตร หมวดหมู่ และราคามาตรฐาน |
| `Farmer.csv` | 300 | ข้อมูลเกษตรกรที่ลงทะเบียน และสหกรณ์ต้นสังกัด |
| `Warehouse.csv` | 15 | ข้อมูลคลังสินค้ากระจายทั่ว 5 ภูมิภาค |
| `Customer.csv` | 200 | ข้อมูลลูกค้า (โรงงาน, ผู้ส่งออก, ตลาดค้าส่ง ฯลฯ) |

### 2. Operational Data (ข้อมูลการดำเนินงาน)
| ไฟล์ | จำนวน (Records) | คำอธิบาย |
|------|-----------------|----------|
| `Harvest.csv` | ~50,000 | ข้อมูลการรับซื้อผลผลิตจากเกษตรกร (1 row = 1 ธุรกรรม) |
| `Inventory.csv` | ~65,000 | ข้อมูลสถานะสินค้าคงคลัง (Daily Snapshot) |
| `Shipment.csv` | ~25,000 | ข้อมูลการจัดส่งสินค้าไปยังลูกค้า |
| `Sales.csv` | ~30,000 | ข้อมูลธุรกรรมการขายสินค้า (Order lines) |

---

## 🛠 Technology Stack
- **Data Engineering:** Python, SQL, ETL Pipeline, Star Schema
- **Cloud Infrastructure:** AWS (EC2, RDS, S3, Application Load Balancer, Auto Scaling)
- **Database:** PostgreSQL
- **Business Intelligence:** Power BI
