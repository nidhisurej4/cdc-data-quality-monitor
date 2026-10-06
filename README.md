# CDC Data Quality Monitor

Catches bad data in PostgreSQL the moment it is written. Every insert and update is captured through change data capture (CDC), checked against configurable rules, and any violations land on a dashboard.

Built from my experience validating CDC pipelines and running regression/UAT data checks on enterprise systems. All data here is synthetic.

## How it works

```
bookings table ──trigger──▶ change_log ──poll──▶ consumer ──rules.yml──▶ dq_violation ──▶ Streamlit dashboard
```

1. A PostgreSQL trigger writes every row change to `change_log` as JSONB (lightweight CDC, no extra infrastructure)
2. The consumer reads changes after its last checkpoint, in batches
3. Each row is checked against the rules in `rules.yml`
4. Violations and the new checkpoint are committed **in the same transaction**, so a crash never skips or double-counts a change
5. The dashboard shows totals, violations by rule and severity, and the latest failing records

## Rule types

| Type | Example |
|---|---|
| `not_null` | customer code must be present |
| `range` | container count between 1 and 500 |
| `allowed_values` | status in PENDING / CONFIRMED / SHIPPED / CANCELLED |
| `regex` | port codes match `^[A-Z]{5}$` (UN/LOCODE) |
| `date_order` | end date not before start date |
| `max_age_days` | record not older than N days |

Add a rule by editing `rules.yml`. No code changes needed.

## Tech stack

Python · PostgreSQL (triggers, JSONB) · psycopg 3 · PyYAML · pandas · Streamlit · pytest · Docker · GitHub Actions

## Run it

```bash
docker compose up -d                 # PostgreSQL with the schema pre-loaded
pip install -r requirements.txt
python -m dq_monitor.seed            # insert 200 sample bookings (~15% bad)
python -m dq_monitor.consumer        # validate all captured changes
streamlit run dashboard.py           # open http://localhost:8501
```

Keep it running with `python -m dq_monitor.consumer --watch 10`.

## Tests

```bash
pytest
```

## Roadmap (ideas to extend)

- [ ] Swap the trigger for logical replication (`wal2json` or Debezium)
- [ ] Cross-row rules (duplicates, referential checks)
- [ ] Slack/email alert when high-severity violations appear
- [ ] Trend chart of violation rate per day
- [ ] Integration test against a real Postgres with Testcontainers
