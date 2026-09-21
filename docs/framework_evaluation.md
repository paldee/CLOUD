# Framework Evaluation

สถานะ: ยังไม่เลือก framework และ production code ยังไม่ผูกกับตัวใด

## สิ่งที่ระบบนี้ต้องการจริง

1. รองรับ OpenAI, Gemini, Claude หรือโมเดล open-source โดยเปลี่ยน provider ได้
2. บังคับ structured output สำหรับ SQL plan, intent และคำตอบพร้อมแหล่งข้อมูล
3. คุม flow แบบ deterministic: classify -> retrieve schema -> generate SQL -> validate -> execute -> summarize
4. วาง SQL guardrails นอก LLM และใช้ RDS user แบบ read-only
5. รองรับ RAG จาก data dictionary, business rules และ dashboard definitions
6. trace prompt, model call, SQL, latency, token usage และ error ได้
7. ดูแลและ deploy บน EC2 ได้โดยผู้รับผิดชอบหนึ่งคน

## Shortlist

| ตัวเลือก | จุดแข็งกับโปรเจกต์นี้ | ข้อควรระวัง | เหมาะเมื่อ |
|---|---|---|---|
| PydanticAI | Python API กระชับ, typed tools/output, dependency injection, รองรับหลาย provider และ OpenTelemetry | ecosystem/ตัวอย่างเฉพาะ Text-to-SQL ยังน้อยกว่า LangChain/LlamaIndex | ต้องการ MVP ที่โค้ดอ่านง่ายและ validation ชัด |
| LangGraph | คุม state machine, retry, checkpoint, streaming และ human approval ได้ละเอียด | boilerplate และ operational complexity สูงกว่าความต้องการ MVP | flow มีหลายรอบ, resume งาน, approval หรือ long-running agent |
| LlamaIndex | เด่นเรื่อง data/RAG, schema retrieval และมีแนวทาง Text-to-SQL สำเร็จรูป | abstraction หลายชั้น; ต้องเสริม SQL security เอง และ API บางส่วนเปลี่ยนเร็ว | RAG และการเลือก schema/table เป็นแกนหลักของระบบ |
| Haystack | pipeline และ RAG components ชัด เหมาะกับ document-heavy workflow | community/integration สำหรับ agent ทั่วไปเล็กกว่า LangChain และอาจหนักเกิน MVP | ingestion/search pipeline ซับซ้อนกว่างาน SQL |
| LangChain | integrations และตัวอย่างจำนวนมาก เริ่ม prototype ได้เร็ว | abstraction/dependency surface ใหญ่ และ agent สำเร็จรูปอาจคุม SQL flow ยาก | ทีมคุ้นเคย ecosystem หรือจำเป็นต้องใช้ integration ที่มีอยู่แล้ว |
| Provider SDK โดยตรง | dependency น้อย, behavior โปร่งใส, คุม security boundary ง่าย | ต้องเขียน provider adapter, retry, tracing และ tool loop เอง | flow สั้นและต้องการลด framework lock-in สูงสุด |

AutoGen และ Semantic Kernel ยังไม่อยู่ใน shortlist รอบแรก เพราะจุดเด่นหลักอยู่ที่
multi-agent/distributed agent และ Microsoft ecosystem ซึ่งยังไม่ใช่ requirement ของระบบนี้

## คำแนะนำปัจจุบัน

ยังไม่ควรติดตั้ง framework ใน production skeleton ให้ทำ spike ขนาดเล็กด้วยคำถามและ
เกณฑ์ทดสอบชุดเดียวกันก่อน โดยเปรียบเทียบ 3 แนวทาง:

1. PydanticAI เป็นตัวเต็งสำหรับ MVP เพราะ typed output และ tools เข้ากับ FastAPI/Pydantic เดิม
2. LangGraph เป็นตัวเลือกเมื่อพิสูจน์แล้วว่าต้องมี checkpoint, approval หรือ repair loop หลายขั้น
3. LlamaIndex ใช้เป็น data/RAG component ได้ แม้ orchestration หลักจะเป็น PydanticAI หรือโค้ดปกติ

ไม่แนะนำให้เริ่มด้วย autonomous multi-agent สำหรับงานนี้ เพราะขั้นตอน query ข้อมูลมีลำดับชัด
และ SQL ต้องผ่าน policy ที่เขียนด้วยโค้ดก่อน execute เสมอ

## Comparison Spike

ให้แต่ละตัวเลือกทำ flow เดียวกันโดยใช้ provider, prompt, schema และ test set ชุดเดียวกัน:

```text
question
  -> classify intent
  -> retrieve relevant tables/business rules
  -> generate structured SQL plan
  -> validate allowlist + read-only + row limit
  -> execute with restricted RDS role
  -> summarize result with cited source
```

ให้คะแนน 1-5 ในหัวข้อต่อไปนี้:

| เกณฑ์ | น้ำหนัก |
|---|---:|
| ความถูกต้องของ SQL และคำตอบ | 30% |
| การบังคับ guardrails และ structured output | 25% |
| ความง่ายในการ debug/trace/test | 15% |
| ความง่ายในการเปลี่ยน LLM provider | 10% |
| latency และ token cost | 10% |
| ปริมาณโค้ดและภาระดูแลโดยคนเดียว | 10% |

เกณฑ์ผ่านขั้นต่ำ: ห้ามมี write query หลุด, ห้าม query ตารางนอก allowlist, ทุก query ต้องมี
row limit/time limit, และคำตอบต้องระบุว่าไม่มีข้อมูลเมื่อ result ว่างแทนการแต่งคำตอบ

## Decision Gate

เลือก framework หลังมีอย่างน้อย 30-50 test questions ครอบคลุมยอดขาย, ผลผลิต,
การจัดส่ง, คงคลัง, คำถามกำกวม, คำถามนอกขอบเขต และ prompt-injection แล้วบันทึกผลเป็น ADR
พร้อมเวอร์ชัน library/model ที่ใช้ทดสอบ

## Official References

- PydanticAI overview: https://pydantic.dev/docs/ai/overview/
- LangGraph reference: https://langchain-ai.github.io/langgraph/reference/
- LlamaIndex Text-to-SQL example: https://docs.llamaindex.ai/en/stable/examples/pipeline/query_pipeline_sql/
- Haystack pipelines: https://docs.haystack.deepset.ai/docs/pipelines
- AutoGen AgentChat: https://microsoft.github.io/autogen/dev/user-guide/agentchat-user-guide/tutorial/index.html
- Semantic Kernel agents: https://learn.microsoft.com/en-us/semantic-kernel/frameworks/agent/
