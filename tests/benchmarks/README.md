# Thai Text-to-SQL Benchmark

`text_to_sql_th.json` contains 30 project-specific questions for the agricultural cooperative
warehouse: 10 easy, 10 medium, and 10 hard cases. Every case includes a canonical PostgreSQL
query that passes the application's SQL guardrail.

## Evaluation dimensions

Score each generated answer on these dimensions rather than exact SQL string equality:

| Dimension | Score |
| --- | ---: |
| SQL parses successfully | 0-1 |
| Uses the correct tables | 0-1 |
| Uses the correct joins | 0-1 |
| Applies the correct filters and date scope | 0-1 |
| Uses the correct aggregation and calculation | 0-1 |
| Passes the application SQL guardrail | 0-1 |
| Executes successfully against the benchmark database | 0-1 |
| Produces the same result as the reference SQL | 0-2 |
| Final Thai summary is faithful to the returned rows | 0-1 |

Maximum score: 10 points per case, 300 points per provider/model.

## Benchmark rules

- Run every provider/model against the same schema context, prompts, database snapshot, and cases.
- Use temperature and retry settings consistently.
- Record model ID, provider, timestamp, latency, token usage, SQL, guardrail result, execution result,
  final answer, and score.
- Do not award result-correctness points when the SQL was not executed.
- Do not let the summarizer introduce numbers that are absent from the database result.
- Select the MVP model from this benchmark, not from a generic public leaderboard alone.
