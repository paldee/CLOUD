# Frontend Handoff

โฟลเดอร์นี้เป็น integration starter สำหรับทีม Web Development โดยยังไม่ล็อกว่า
ต้องใช้ React, Next.js, Vue หรือ framework ใด

## สิ่งที่มีให้

- `index.html`, `styles.css`, `app.js` หน้าแชตต้นแบบที่เปิดใช้งานได้ทันที
- `src/types/agent.ts` TypeScript types ที่ตรงกับ FastAPI response
- `src/lib/agent-api.ts` API client ที่ใช้กับ browser framework ใดก็ได้
- `docs/API_CONTRACT.md` request, response, status และ error contract
- `.env.example` ตัวอย่าง backend URL

## หน้าจอขั้นต่ำที่แนะนำ

1. ช่องกรอกคำถามและปุ่มส่ง
2. loading, empty และ network-error state
3. แสดงคำตอบหลักจาก `answer`
4. แสดง badge จาก `status`
5. แสดง SQL แบบ collapsed panel เมื่อ `sql` ไม่เป็น `null`
6. แสดง `guardrail_violations` เมื่อ status เป็น `rejected`
7. แสดงรายการ `sources`

## การนำไปใช้

ทีม Web Dev สามารถสร้างโปรเจกต์ในโฟลเดอร์นี้ด้วย stack ที่ทีมเลือก แล้วเก็บไฟล์
`src/types/agent.ts` และ `src/lib/agent-api.ts` ไว้ หรือย้ายโค้ดสองส่วนนี้เข้าโครงของทีม

เปิดหน้าต้นแบบที่พอร์ตซึ่ง Backend อนุญาตผ่าน CORS:

```powershell
python -m http.server 5173 --directory frontend
```

แล้วเปิด `http://localhost:5173`

ตัวอย่างการเรียก:

```ts
import { createAgentApi } from "./src/lib/agent-api";

const api = createAgentApi({ baseUrl: "http://localhost:8000" });
const result = await api.ask({
  question: "ยอดขายรวมรายเดือนเป็นเท่าไร",
  user_role: "analyst",
});
```

ห้ามใส่ LLM API key หรือ database credential ใน frontend environment variables
เพราะค่าที่ bundle ฝั่ง browser สามารถถูกผู้ใช้มองเห็นได้
