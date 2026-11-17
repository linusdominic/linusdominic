# Linus Dominic Nathaniel

Lead data engineer. I build data platforms on AWS and Databricks, mostly for lending,
and most of my work comes down to reconciliation: getting several systems that each
think they own the customer to agree on one version.

Portfolio: [linusdominic.github.io](https://linusdominic.github.io) ·
LinkedIn: [linus-dominic](https://www.linkedin.com/in/linus-dominic)

## Projects

Four repositories, one domain (lending), each runnable from a clone. Every number in
their READMEs comes from a run on my own machine, and each README lists what was not
verified.

| Repository | What it is | Stack |
| --- | --- | --- |
| [lakehouse-cdc-streaming](https://github.com/linusdominic/lakehouse-cdc-streaming) | Change data capture from a loan-servicing Postgres into Iceberg, with a harness that proves the lakehouse still matches the source after duplicates, replays, a schema change and a job killed mid-batch | Debezium, Kafka API (Redpanda), Spark Structured Streaming, Iceberg, Trino, dbt, Terraform |
| [reconkit](https://github.com/linusdominic/reconkit) | A Python tool that diffs tables across databases by checksum bisection, so only disagreeing key ranges are downloaded, and checks tables against data contracts in CI | Python, PostgreSQL, DuckDB, warehouse SQL dialects, Airflow and Dagster hooks |
| [mortgage-metrics-platform](https://github.com/linusdominic/mortgage-metrics-platform) | Batch platform on public HMDA mortgage data: idempotent backfills, a Kimball star with enforced contracts, metrics defined once in a semantic layer, and an MCP server that lets AI agents query those metrics and nothing else | Airflow 3, dbt, MetricFlow, DuckDB, MCP |
| [serverless-webhook-ingestion](https://github.com/linusdominic/serverless-webhook-ingestion) | Serverless ingestion of vendor webhooks on AWS: verify the signature, archive before acknowledging, then process idempotently and in order, with a seeded load test and a verifier that checks 18 invariants. Runs on a local AWS emulator; not deployed to a real account | API Gateway, Lambda, SQS, DynamoDB, S3, Glue, Athena, Step Functions, Terraform |

### AI engineering

Two repositories on LLM systems, held to the same rule: what the README claims was run,
and what was not run is listed.

| Repository | What it is | Stack |
| --- | --- | --- |
| [agentic-docs-assistant](https://github.com/linusdominic/agentic-docs-assistant) | A support agent that answers questions from a documentation set and files a ticket only after a human approves it. Retrieval runs on pgvector, the agent's state is checkpointed to Postgres so a paused run can resume, and replies stream over HTTP. Run locally against a live model and in CI with a scripted one; the Cloud Run deployment is a reference and was not run | LangGraph, FastAPI, PostgreSQL + pgvector, Docker, Cloud Run |
| [vectorless-rag-benchmark](https://github.com/linusdominic/vectorless-rag-benchmark) | "Vectorless" RAG, where a model navigates a document's outline instead of searching a vector index, built and measured against BM25, dense and hybrid retrieval on Regulation Z (Truth in Lending). With index summaries it ranked the right paragraph first on 95% of 60 questions against 75% for hybrid search, at about three seconds a query; the answer-accuracy gap was not statistically significant. The questions are model-written and only ten were checked by hand | Python, Claude API, BM25, fastembed, eCFR, GitHub Actions |

## What I work with

Python, SQL · Redshift, Databricks (Delta Lake, Unity Catalog), Snowflake, BigQuery,
PostgreSQL · Airflow, dbt, Spark, Kafka, AWS Glue · Terraform, Docker, GitHub Actions ·
LangGraph, FastAPI, pgvector, LLM evaluation
