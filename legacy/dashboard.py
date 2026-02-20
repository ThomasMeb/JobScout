import sqlite3
from pathlib import Path

import pandas as pd
import plotly.express as px
import streamlit as st

DB_PATH = Path(__file__).parent / "data" / "jobs.db"
CLOUD_DB = Path(__file__).parent / "assets" / "demo.db"
FORCE_DEMO = not DB_PATH.exists() and CLOUD_DB.exists()
if FORCE_DEMO:
    DB_PATH = CLOUD_DB


def get_conn():
    return sqlite3.connect(str(DB_PATH), check_same_thread=False)


@st.cache_data(ttl=300)
def load_jobs():
    conn = get_conn()
    df = pd.read_sql_query(
        """SELECT *, ROW_NUMBER() OVER (PARTITION BY title, company ORDER BY id) as dup_rank
        FROM jobs WHERE match_score IS NOT NULL ORDER BY match_score DESC""",
        conn,
    )
    conn.close()
    # Deduplicate: keep only first occurrence of each title+company
    df = df[df["dup_rank"] == 1].drop(columns=["dup_rank"])
    # Clean "Unknown" companies
    df["company"] = df["company"].replace({"Unknown": "Non précisé", "Non précisé": "Non précisé"})
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


def format_salary(row):
    """Format salary range from salary_min/salary_max columns."""
    smin = row.get("salary_min")
    smax = row.get("salary_max")
    currency = row.get("salary_currency", "EUR")
    sym = "€" if currency in ("EUR", None, "") else "$" if currency == "USD" else currency
    if pd.notna(smin) and smin >= 1000 and pd.notna(smax) and smax >= 1000:
        return f"{int(smin/1000)}k-{int(smax/1000)}k {sym}"
    if pd.notna(smin) and smin >= 1000:
        return f"{int(smin/1000)}k+ {sym}"
    if pd.notna(smax) and smax >= 1000:
        return f"<{int(smax/1000)}k {sym}"
    return ""


# --- Page config ---
st.set_page_config(
    page_title="JobScout Dashboard",
    page_icon="🤖",
    layout="wide",
)

# --- Sidebar ---
st.sidebar.title("🔍 JobScout")
if FORCE_DEMO:
    demo_mode = True
    st.sidebar.info("Mode démo (données anonymisées)")
else:
    demo_mode = st.sidebar.toggle("Mode démo", value=False, help="Anonymise les données sensibles")
st.sidebar.divider()

jobs_df = load_jobs()
companies_df = load_companies()

# Filters
sources = ["Toutes"] + sorted(jobs_df["source"].unique().tolist())
selected_source = st.sidebar.selectbox("Source", sources)

min_score = st.sidebar.slider("Score minimum", 0, 100, 50, 5)

statuses = ["Tous"] + sorted(jobs_df["status"].dropna().unique().tolist())
selected_status = st.sidebar.selectbox("Statut", statuses)

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
if selected_status != "Tous":
    filtered = filtered[filtered["status"] == selected_status]
if selected_location != "Toutes":
    filtered = filtered[filtered["location"] == selected_location]

if demo_mode:
    filtered = anonymize(filtered, ["company"])
    filtered["source_url"] = ""
    companies_display = anonymize(companies_df, ["name"])
else:
    companies_display = companies_df

# --- KPIs ---
st.title("🔍 JobScout — Dashboard")

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

score_col1, score_col2 = st.columns([2, 1])

with score_col1:
    # Group scores into meaningful categories
    bins = [0, 30, 50, 70, 100]
    labels_cat = ["Faible (0-30)", "Moyen (30-50)", "Bon (50-70)", "Excellent (70+)"]
    colors_cat = ["#E74C3C", "#F39C12", "#4A90D9", "#2ECC71"]
    score_cats = pd.cut(filtered["match_score"], bins=bins, labels=labels_cat, include_lowest=True)
    cat_counts = score_cats.value_counts().reindex(labels_cat).fillna(0).astype(int)

    fig_cat = px.bar(
        x=cat_counts.index,
        y=cat_counts.values,
        color=cat_counts.index,
        color_discrete_map=dict(zip(labels_cat, colors_cat)),
        text=cat_counts.values,
        labels={"x": "", "y": "Nombre d'offres"},
    )
    fig_cat.update_layout(
        showlegend=False,
        margin=dict(l=0, r=0, t=10, b=0),
        height=300,
        bargap=0.2,
    )
    fig_cat.update_traces(textposition="outside")
    st.plotly_chart(fig_cat, use_container_width=True)

with score_col2:
    total = len(filtered)
    st_colors = ["red", "orange", "blue", "green"]
    for label, st_color, count in zip(labels_cat, st_colors, cat_counts.values):
        pct = count / total * 100 if total > 0 else 0
        st.markdown(f":{st_color}[**{label}**]")
        st.progress(pct / 100, text=f"{count} offres ({pct:.0f}%)")

# --- Top jobs ---
st.subheader(f"Top offres ({len(filtered)} résultats)")

# Build salary column
filtered = filtered.copy()
filtered["salary"] = filtered.apply(format_salary, axis=1)

display_cols = ["title", "company", "match_score", "salary", "source", "location", "remote_type", "match_priority", "source_url"]
display_names = {
    "title": "Titre",
    "company": "Entreprise",
    "match_score": "Score",
    "salary": "Salaire",
    "source": "Source",
    "location": "Localisation",
    "remote_type": "Remote",
    "match_priority": "Priorité",
    "source_url": "Lien",
}

available_cols = [c for c in display_cols if c in filtered.columns]
jobs_table = filtered[available_cols].rename(columns=display_names)

col_config = {
    "Score": st.column_config.NumberColumn(format="%.0f /100"),
    "Lien": st.column_config.LinkColumn("Lien", display_text="Voir"),
}

st.dataframe(
    jobs_table,
    width="stretch",
    height=400,
    hide_index=True,
    column_config=col_config,
)

# --- Job detail expander ---
if not filtered.empty:
    with st.expander("Détail du scoring (cliquer pour déplier)"):
        detail_options = filtered[["title", "company", "match_score"]].copy()
        detail_options["label"] = detail_options.apply(
            lambda r: f"[{int(r['match_score'])}] {r['title']} — {r['company']}", axis=1
        )
        selected_job_label = st.selectbox("Choisir une offre", detail_options["label"].tolist()[:50])
        if selected_job_label:
            idx = detail_options[detail_options["label"] == selected_job_label].index[0]
            job = filtered.loc[idx]
            c1, c2 = st.columns(2)
            with c1:
                st.markdown("**Reasoning**")
                st.write(job.get("match_reasoning", "N/A"))
            with c2:
                st.markdown("**Keywords matchés**")
                st.write(job.get("match_keywords", "N/A"))
                st.markdown("**Keywords manquants**")
                st.write(job.get("missing_keywords", "N/A"))

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
        width="stretch",
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
        st.plotly_chart(fig_sources, width="stretch")

# --- LLM costs ---
if not llm_costs.empty:
    st.subheader("Coûts LLM")
    cost_k1, cost_k2, cost_k3, cost_k4 = st.columns(4)
    total_tokens = llm_costs["tokens"].sum()
    total_days = len(llm_costs)
    cost_per_job = total_cost / len(jobs_df) if len(jobs_df) > 0 else 0
    cost_k1.metric("Coût total", f"${total_cost:.2f}")
    cost_k2.metric("Coût / job", f"${cost_per_job:.4f}")
    cost_k3.metric("Tokens utilisés", f"{total_tokens / 1e6:.1f}M")
    cost_k4.metric("Jours actifs", total_days)

# --- Footer ---
st.divider()
st.caption("[JobScout](https://github.com/ThomasMeb/JobScout) — AI-Powered Job Search Automation")
