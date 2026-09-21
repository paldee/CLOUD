# AWS EC2 Deployment Notes

## Recommended runtime

- EC2: Ubuntu LTS
- Process: Docker หรือ systemd + uvicorn
- Network: EC2 อยู่ใน VPC ที่ connect ถึง Amazon RDS ได้
- Secrets: ใช้ AWS Systems Manager Parameter Store หรือ Secrets Manager แทนการวาง key ในไฟล์

## Environment variables

ตั้งค่าตาม `.env.example`

```bash
APP_ENV=production
DATABASE_URL=postgresql+psycopg://...
LLM_PROVIDER=openai
LLM_MODEL=gpt-4o-mini
OPENAI_API_KEY=...
```

## Docker run example

```bash
docker build -t agri-dw-llm-agent .
docker run --env-file .env -p 8000:8000 agri-dw-llm-agent
```

## Security checklist

- Security Group เปิด inbound เฉพาะ port ที่จำเป็น
- RDS ไม่ควร public ถ้าไม่จำเป็น
- DB user ของ agent ควรเป็น read-only
- เก็บ prompt, SQL, latency และ error logs สำหรับ audit
- เพิ่ม rate limit ที่ API gateway หรือ reverse proxy

