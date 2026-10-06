"""Streamlit dashboard: streamlit run dashboard.py"""
import os

import pandas as pd
import psycopg
import streamlit as st

DSN = os.getenv("DATABASE_URL", "postgresql://dq:dq@localhost:5432/dq")

st.set_page_config(page_title="Data Quality Monitor", layout="wide")
st.title("Data Quality Monitor")


@st.cache_data(ttl=30)
def query(sql: str) -> pd.DataFrame:
    with psycopg.connect(DSN) as conn:
        return pd.read_sql(sql, conn)


runs = query("SELECT COALESCE(SUM(changes_checked),0) AS checked, "
             "COALESCE(SUM(violations_found),0) AS found FROM dq_run")
checked, found = int(runs.checked[0]), int(runs.found[0])
bad_records = query("SELECT COUNT(DISTINCT change_id) AS n FROM dq_violation").n[0]

c1, c2, c3 = st.columns(3)
c1.metric("Changes checked", f"{checked:,}")
c2.metric("Violations", f"{found:,}")
c3.metric("Clean-change rate", f"{(1 - bad_records / checked):.1%}" if checked else "n/a")

left, right = st.columns(2)
with left:
    st.subheader("Violations by rule")
    st.bar_chart(query("SELECT rule_name, COUNT(*) AS n FROM dq_violation "
                       "GROUP BY rule_name ORDER BY n DESC").set_index("rule_name"))
with right:
    st.subheader("Violations by severity")
    st.bar_chart(query("SELECT severity, COUNT(*) AS n FROM dq_violation "
                       "GROUP BY severity").set_index("severity"))

st.subheader("Latest violations")
st.dataframe(query("SELECT detected_at, table_name, record_key, rule_name, severity, message "
                   "FROM dq_violation ORDER BY id DESC LIMIT 200"), use_container_width=True)
