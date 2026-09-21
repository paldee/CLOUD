# Data Warehouse Context

สรุปจากเอกสารรายละเอียดระบบเพื่อใช้เป็น context ของ AI Agent

## Source systems

- Harvest.csv
- Sales.csv
- Shipment.csv
- Inventory.csv
- Farmer.csv
- Customer.csv
- Crop.csv
- Warehouse.csv

## Fact tables

- `fact_harvest`: การรับซื้อผลผลิต
- `fact_sales`: การขาย
- `fact_shipment`: การจัดส่ง
- `fact_inventory`: สินค้าคงคลัง

## Dimension tables

- `dim_crop`
- `dim_warehouse`
- `dim_farmer`
- `dim_customer`
- `dim_date`

## Dashboard-oriented metrics

- Total Harvest Amount
- Total Quantity Harvested
- Average Price per Kg
- Total Sales Amount / Net Sales
- Total Quantity Sold
- Total Shipping Cost
- Ending Stock
- Inventory Turnover
- Stock Level Alert

