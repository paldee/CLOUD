from app.services.query_workflow import run_query_workflow


def answer_question(question: str, user_role: str | None = None) -> dict:
    result = run_query_workflow(question=question, user_role=user_role)
    return {
        "answer": result.answer,
        "sql": result.sql,
        "sources": result.sources,
        "status": result.status,
        "guardrail_violations": result.guardrail_violations,
    }
