import sqlite3
from pathlib import Path

import pandas as pd
import plotly.express as px
import streamlit as st

DB_PATH = Path(__file__).parent / "data" / "jobs.db"


def get_conn():
    return sqlite3.connect(str(DB_PATH), check_same_thread=False)


@st.cache_data(ttl=300)
def load_jobs():
    conn = get_conn()
    df = pd.read_sql_query(
        "SELECT * FROM jobs WHERE match_score IS NOT NULL ORDER BY match_score DESC",
        conn,
    )
    conn.close()
    return df


@st.cache_data(ttl=300)
def load_companies():
    conn = get_conn()
    df = pd.read_sql_query(
        "SELECT * FROM companies ORDER BY relevance_score DESC", conn
    )
    conn.close()
    return df


@st.cache_data(ttl=300)
def load_scrape_runs():
    conn = get_conn()
    df = pd.read_sql_query(
        "SELECT source, SUM(jobs_found) as found, SUM(jobs_new) as new, COUNT(*) as runs "
        "FROM scrape_runs WHERE status='success' GROUP BY source ORDER BY found DESC",
        conn,
    )
    conn.close()
    return df


@st.cache_data(ttl=300)
def load_llm_costs():
    conn = get_conn()
    df = pd.read_sql_query(
        "SELECT strftime('%Y-%m-%d', created_at) as date, "
        "SUM(cost_usd) as cost, SUM(input_tokens + output_tokens) as tokens "
        "FROM llm_usage GROUP BY date ORDER BY date",
        conn,
    )
    conn.close()
    return df


def anonymize(df, columns):
    """Replace values with anonymized placeholders for demo mode."""
    df = df.copy()
    for col in columns:
        if col in df.columns:
            unique = df[col].unique()
            mapping = {v: f"Company_{i+1}" for i, v in enumerate(unique)}
            df[col] = df[col].map(mapping)
    return df


# --- Page config ---
st.set_page_config(
    page_title="Job Agent Dashboard",
    page_icon="🤖",
    layout="wide",
)

# --- Sidebar ---
st.sidebar.title("🤖 Job Agent")
demo_mode = st.sidebar.toggle("Mode démo", value=False, help="Anonymise les données")
st.sidebar.divider()

jobs_df = load_jobs()
companies_df = load_companies()

# Filters
sources = ["Toutes"] + sorted(jobs_df["source"].unique().tolist())
selected_source = st.sidebar.selectbox("Source", sources)

min_score = st.sidebar.slider("Score minimum", 0, 100, 50, 5)

locations = ["Toutes"] + sorted(
    [loc for loc in jobs_df["location"].dropna().unique().tolist() if loc]
)
selected_location = st.sidebar.selectbox("Localisation", locations)

if st.sidebar.button("Rafraîchir"):
    st.cache_data.clear()
    st.rerun()

# Apply filters
filtered = jobs_df[jobs_df["match_score"] >= min_score]
if selected_source != "Toutes":
    filtered = filtered[filtered["source"] == selected_source]
if selected_location != "Toutes":
    filtered = filtered[filtered["location"] == selected_location]

if demo_mode:
    filtered = anonymize(filtered, ["company"])
    companies_display = anonymize(companies_df, ["name"])
else:
    companies_display = companies_df

# --- KPIs ---
st.title("🤖 Job Agent — Dashboard")

k1, k2, k3, k4, k5 = st.columns(5)
k1.metric("Total jobs", len(jobs_df))
k2.metric("Score >= 60", len(jobs_df[jobs_df["match_score"] >= 60]))
k3.metric("Score >= 70", len(jobs_df[jobs_df["match_score"] >= 70]))
k4.metric("Entreprises cibles", len(companies_df))

llm_costs = load_llm_costs()
total_cost = llm_costs["cost"].sum() if not llm_costs.empty else 0
k5.metric("Coût LLM", f"${total_cost:.2f}")

# --- Score distribution ---
st.subheader("Distribution des scores")

fig_hist = px.histogram(
    filtered,
    x="match_score",
    nbins=20,
    color_discrete_sequence=["#4A90D9"],
    labels={"match_score": "Score", "count": "Nombre"},
)
fig_hist.update_layout(
    showlegend=False,
    margin=dict(l=0, r=0, t=10, b=0),
    height=300,
    yaxis_title="Nombre d'offres",
    xaxis_title="Score de matching",
)
st.plotly_chart(fig_hist, use_container_width=True)

# --- Top jobs ---
st.subheader(f"Top offres ({len(filtered)} résultats)")

display_cols = ["title", "company", "match_score", "source", "location", "remote_type", "match_priority"]
display_names = {
    "title": "Titre",
    "company": "Entreprise",
    "match_score": "Score",
    "source": "Source",
    "location": "Localisation",
    "remote_type": "Remote",
    "match_priority": "Priorité",
}

available_cols = [c for c in display_cols if c in filtered.columns]
jobs_table = filtered[available_cols].rename(columns=display_names)

st.dataframe(
    jobs_table,
    use_container_width=True,
    height=400,
    column_config={
        "Score": st.column_config.ProgressColumn(
            min_value=0, max_value=100, format="%.0f"
        ),
    },
)

# --- Two columns: companies + sources ---
col_left, col_right = st.columns(2)

with col_left:
    st.subheader("Entreprises cibles")
    company_cols = ["name", "relevance_score", "sector", "location", "spontaneous_status"]
    company_names = {
        "name": "Nom",
        "relevance_score": "Score",
        "sector": "Secteur",
        "location": "Localisation",
        "spontaneous_status": "Statut",
    }
    available = [c for c in company_cols if c in companies_display.columns]
    st.dataframe(
        companies_display[available].rename(columns=company_names),
        use_container_width=True,
        hide_index=True,
    )

with col_right:
    st.subheader("Performance des sources")
    scrape_df = load_scrape_runs()
    if not scrape_df.empty:
        fig_sources = px.bar(
            scrape_df,
            x="source",
            y=["found", "new"],
            barmode="group",
            labels={"value": "Jobs", "source": "Source", "variable": ""},
            color_discrete_map={"found": "#4A90D9", "new": "#50C878"},
        )
        fig_sources.update_layout(
            margin=dict(l=0, r=0, t=10, b=0),
            height=300,
            legend=dict(orientation="h", y=1.1),
        )
        st.plotly_chart(fig_sources, use_container_width=True)

# --- LLM costs ---
if not llm_costs.empty:
    st.subheader("Coûts LLM")
    llm_costs["cumulative"] = llm_costs["cost"].cumsum()
    fig_cost = px.area(
        llm_costs,
        x="date",
        y="cumulative",
        labels={"cumulative": "Coût cumulé ($)", "date": "Date"},
        color_discrete_sequence=["#FF6B6B"],
    )
    fig_cost.update_layout(
        margin=dict(l=0, r=0, t=10, b=0),
        height=250,
    )
    st.plotly_chart(fig_cost, use_container_width=True)

# --- Footer ---
st.divider()
st.caption("Job Agent — AI-Powered Job Search Automation")
