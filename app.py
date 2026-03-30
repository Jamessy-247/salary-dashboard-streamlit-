
import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots

# ── Page config 
st.set_page_config(
    page_title="Salary Intelligence Dashboard",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Custom CSS ──────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&family=JetBrains+Mono:wght@400;500&display=swap');

html, body, [class*="css"] { font-family: 'Inter', sans-serif; }

/* Hide streamlit branding */
#MainMenu, footer, header { visibility: hidden; }
.block-container { padding-top: 1.5rem; padding-bottom: 2rem; }

/* KPI Cards */
.kpi-container {
    background: linear-gradient(135deg, #1e1e2e 0%, #252535 100%);
    border: 1px solid #3d3d5c;
    border-radius: 16px;
    padding: 1.2rem 1.4rem;
    text-align: center;
    transition: transform 0.2s, box-shadow 0.2s;
    position: relative;
    overflow: hidden;
}
.kpi-container::before {
    content: '';
    position: absolute;
    top: 0; left: 0; right: 0;
    height: 3px;
    border-radius: 16px 16px 0 0;
}
.kpi-container.violet::before { background: #7C3AED; }
.kpi-container.teal::before   { background: #0D9488; }
.kpi-container.rose::before   { background: #E11D48; }
.kpi-container.amber::before  { background: #D97706; }
.kpi-container.blue::before   { background: #2563EB; }
.kpi-container.green::before  { background: #16A34A; }

.kpi-label  { font-size: 0.7rem; font-weight: 600; letter-spacing: 0.08em;
               text-transform: uppercase; color: #9ca3af; margin-bottom: 6px; }
.kpi-value  { font-size: 1.9rem; font-weight: 700; font-family: 'JetBrains Mono', monospace;
               color: #f1f5f9; line-height: 1; }
.kpi-delta  { font-size: 0.72rem; color: #6b7280; margin-top: 4px; }

/* Section headers */
.section-header {
    font-size: 1rem; font-weight: 600; color: #e2e8f0;
    padding: 0.5rem 0; margin: 0.5rem 0 1rem 0;
    border-bottom: 1px solid #2d2d44;
    display: flex; align-items: center; gap: 8px;
}
.section-icon { font-size: 1.1rem; }

/* Sidebar styling */
.css-1d391kg, [data-testid="stSidebar"] {
    background: #12121f !important;
}
[data-testid="stSidebar"] .stSelectbox label,
[data-testid="stSidebar"] .stMultiSelect label,
[data-testid="stSidebar"] .stSlider label {
    color: #9ca3af !important;
    font-size: 0.8rem !important;
    font-weight: 500 !important;
    text-transform: uppercase !important;
    letter-spacing: 0.05em !important;
}

/* Insight boxes */
.insight-box {
    background: #1a1a2e;
    border-left: 3px solid #7C3AED;
    border-radius: 0 8px 8px 0;
    padding: 0.8rem 1rem;
    margin: 0.4rem 0;
    font-size: 0.85rem;
    color: #d1d5db;
}
.insight-box.teal   { border-left-color: #0D9488; }
.insight-box.rose   { border-left-color: #E11D48; }
.insight-box.amber  { border-left-color: #D97706; }

/* Dataframe */
.stDataFrame { border-radius: 12px; overflow: hidden; }

/* Tab styling */
.stTabs [data-baseweb="tab-list"] {
    gap: 4px;
    background: #1a1a2e;
    border-radius: 10px;
    padding: 4px;
}
.stTabs [data-baseweb="tab"] {
    border-radius: 7px;
    padding: 6px 20px;
    font-size: 0.85rem;
    font-weight: 500;
}
</style>
""", unsafe_allow_html=True)



# DATA LOADING & CLEANING


@st.cache_data
def load_data(path: str) -> pd.DataFrame:
    df = pd.read_csv(path)

    # Normalize column names
    df.columns = df.columns.str.strip()

    # Education normalization
    edu_map = {
        "Bachelor's":        "Bachelor's",
        "Bachelor's Degree": "Bachelor's",
        "Master's":          "Master's",
        "Master's Degree":   "Master's",
        "PhD":               "PhD",
        "phD":               "PhD",
        "High School":       "High School",
    }
    df["Education Level"] = df["Education Level"].str.strip().map(edu_map)

    # Drop rows missing critical fields
    df = df.dropna(subset=["Salary", "Gender", "Education Level", "Job Title"])
    df = df[df["Salary"] > 1000]  # remove data entry errors

    # Derived columns
    df["Age"] = df["Age"].round(0).astype("Int64")
    df["Years of Experience"] = df["Years of Experience"].round(1)

    # Age bands
    bins   = [20, 25, 30, 35, 40, 45, 50, 55, 65]
    labels = ["21-25", "26-30", "31-35", "36-40", "41-45", "46-50", "51-55", "56+"]
    df["Age Band"] = pd.cut(df["Age"], bins=bins, labels=labels, right=True)

    # Exp bands
    ebins   = [-0.1, 2, 5, 10, 15, 20, 35]
    elabels = ["0-2 yrs", "3-5 yrs", "6-10 yrs", "11-15 yrs", "16-20 yrs", "20+ yrs"]
    df["Exp Band"] = pd.cut(df["Years of Experience"], bins=ebins, labels=elabels, right=True)

    # Salary tier
    def salary_tier(s):
        if s < 60000:   return "Entry (<$60k)"
        if s < 100000:  return "Mid ($60k-$100k)"
        if s < 150000:  return "Senior ($100k-$150k)"
        if s < 200000:  return "Lead ($150k-$200k)"
        return "Executive ($200k+)"

    df["Salary Tier"] = df["Salary"].apply(salary_tier)

    # Department (broad)
    def get_dept(title):
        t = str(title).lower()
        if any(x in t for x in ["software", "engineer", "developer", "devops", "fullstack", "back end", "front end", "mobile", "cloud"]):
            return "Engineering"
        if any(x in t for x in ["data", "analyst", "scientist", "ml", "machine learning", "ai", "business intelligence"]):
            return "Data & Analytics"
        if any(x in t for x in ["product", "project"]):
            return "Product"
        if any(x in t for x in ["marketing", "sales", "growth", "brand"]):
            return "Sales & Marketing"
        if any(x in t for x in ["hr", "human resource", "recruiter", "talent", "people"]):
            return "HR & People"
        if any(x in t for x in ["finance", "accounting", "financial", "cfo"]):
            return "Finance"
        if any(x in t for x in ["manager", "director", "vp ", "vice", "head ", "chief", "cto", "ceo", "coo"]):
            return "Leadership"
        if any(x in t for x in ["operations", "supply", "logistics"]):
            return "Operations"
        return "Other"

    df["Department"] = df["Job Title"].apply(get_dept)

    return df.reset_index(drop=True)



# PLOTLY THEME


COLORS = {
    "violet": "#7C3AED", "teal":  "#0D9488", "rose":  "#E11D48",
    "amber":  "#D97706", "blue":  "#2563EB", "green": "#16A34A",
    "sky":    "#0EA5E9", "pink":  "#DB2777", "lime":  "#65A30D",
    "orange": "#EA580C",
}
PALETTE = list(COLORS.values())

def themed_fig(fig, height=400, margin=dict(l=20, r=20, t=40, b=20)):
    fig.update_layout(
        height=height,
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="#1a1a2e",
        font=dict(family="Inter, sans-serif", color="#9ca3af", size=11),
        title_font=dict(color="#e2e8f0", size=13, family="Inter"),
        legend=dict(
            bgcolor="rgba(0,0,0,0)", font=dict(color="#9ca3af", size=10),
            orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1
        ),
        margin=margin,
        xaxis=dict(gridcolor="#2d2d44", linecolor="#2d2d44", tickfont=dict(color="#6b7280")),
        yaxis=dict(gridcolor="#2d2d44", linecolor="#2d2d44", tickfont=dict(color="#6b7280")),
        hoverlabel=dict(bgcolor="#1e1e2e", font_color="#f1f5f9", bordercolor="#3d3d5c"),
    )
    return fig



# KPI CARD HELPER


def kpi(label, value, delta="", color="violet"):
    st.markdown(f"""
    <div class="kpi-container {color}">
        <div class="kpi-label">{label}</div>
        <div class="kpi-value">{value}</div>
        <div class="kpi-delta">{delta}</div>
    </div>""", unsafe_allow_html=True)


def section(title   , icon=""):
    st.markdown(f'<div class="section-header"><span class="section-icon">{icon}</span>{title}</div>',
                unsafe_allow_html=True)


def insight(text, style=""):
    st.markdown(f'<div class="insight-box {style}">{text}</div>', unsafe_allow_html=True)





df_full = load_data("Salary_Data.csv")



# SIDEBAR FILTERS


with st.sidebar:
    st.markdown("## Filters")
    st.markdown("---")

    gender_opts = ["All"] + sorted(df_full["Gender"].dropna().unique().tolist())
    sel_gender = st.multiselect("Gender", options=df_full["Gender"].dropna().unique().tolist(),
                                 default=df_full["Gender"].dropna().unique().tolist())

    edu_order = ["High School", "Bachelor's", "Master's", "PhD"]
    sel_edu = st.multiselect("Education Level", options=edu_order, default=edu_order)

    dept_opts = sorted(df_full["Department"].unique().tolist())
    sel_dept = st.multiselect("Department", options=dept_opts, default=dept_opts)

    sal_min, sal_max = int(df_full["Salary"].min()), int(df_full["Salary"].max())
    sel_salary = st.slider("Salary Range ($)", min_value=sal_min, max_value=sal_max,
                            value=(sal_min, sal_max), step=5000,
                            format="$%d")

    exp_min, exp_max = 0, int(df_full["Years of Experience"].max())
    sel_exp = st.slider("Years of Experience", min_value=exp_min, max_value=exp_max,
                         value=(exp_min, exp_max), step=1)

    age_min, age_max = int(df_full["Age"].min()), int(df_full["Age"].max())
    sel_age = st.slider("Age Range", min_value=age_min, max_value=age_max,
                         value=(age_min, age_max), step=1)

    st.markdown("---")
    top_n = st.slider("Top N Job Titles", min_value=5, max_value=30, value=15, step=5)

    st.markdown("---")
    if st.button(" Reset Filters", use_container_width=True):
        st.rerun()

# Apply filters
df = df_full.copy()
if sel_gender:
    df = df[df["Gender"].isin(sel_gender)]
if sel_edu:
    df = df[df["Education Level"].isin(sel_edu)]
if sel_dept:
    df = df[df["Department"].isin(sel_dept)]
df = df[
    (df["Salary"] >= sel_salary[0]) & (df["Salary"] <= sel_salary[1]) &
    (df["Years of Experience"] >= sel_exp[0]) & (df["Years of Experience"] <= sel_exp[1]) &
    (df["Age"] >= sel_age[0]) & (df["Age"] <= sel_age[1])
]

pct_of_total = len(df) / len(df_full) * 100



# HEADER


col_h1, col_h2 = st.columns([3, 1])
with col_h1:
    st.markdown("## Salary Intelligence Dashboard")
    st.caption(f"Showing **{len(df):,}** of **{len(df_full):,}** records ({pct_of_total:.1f}%) · "
               f"Salary Dataset · {df_full['Job Title'].nunique()} unique job titles")
with col_h2:
    st.markdown("")
    if len(df) < len(df_full):
        st.info(f"{len(df):,} records filtered")



# KPI ROW


c1, c2, c3, c4, c5, c6 = st.columns(6)
with c1: kpi("Total Records",    f"{len(df):,}",                     f"{pct_of_total:.0f}% of dataset",  "violet")
with c2: kpi("Avg Salary",       f"${df['Salary'].mean():,.0f}",     f"Median ${df['Salary'].median():,.0f}", "teal")
with c3: kpi("Max Salary",       f"${df['Salary'].max():,.0f}",     df[df['Salary']==df['Salary'].max()]['Job Title'].iloc[0][:20] if len(df) else "—", "rose")
with c4: kpi("Avg Experience",   f"{df['Years of Experience'].mean():.1f} yrs", f"Range: {df['Years of Experience'].min():.0f}–{df['Years of Experience'].max():.0f} yrs", "amber")
with c5: kpi("Avg Age",          f"{df['Age'].mean():.1f}",          f"Range: {df['Age'].min()}–{df['Age'].max()}", "blue")
with c6:
    gender_counts = df["Gender"].value_counts()
    f_pct = gender_counts.get("Female", 0) / len(df) * 100 if len(df) else 0
    kpi("Female %",   f"{f_pct:.1f}%",  f"{gender_counts.get('Female', 0):,} of {len(df):,}", "green")

st.markdown("<br>", unsafe_allow_html=True)


# TABS
# 

tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "Overview",
    "Salary Deep Dive",
    "Demographics",
    "Job & Department",
    "Data Explorer",
])


# TAB 1: OVERVIEW


with tab1:
    section("Salary Distribution by Key Dimensions")

    col1, col2 = st.columns(2)

    # Salary histogram
    with col1:
        fig = px.histogram(
            df, x="Salary", nbins=60, color_discrete_sequence=[COLORS["violet"]],
            title="Salary Distribution",
            labels={"Salary": "Annual Salary ($)"},
        )
        fig.update_traces(marker_line_color="#3d3d5c", marker_line_width=0.5, opacity=0.85)
        fig.add_vline(x=df["Salary"].mean(), line_dash="dash", line_color=COLORS["teal"],
                      annotation_text=f"Mean ${df['Salary'].mean():,.0f}",
                      annotation_font_color=COLORS["teal"])
        fig.add_vline(x=df["Salary"].median(), line_dash="dot", line_color=COLORS["amber"],
                      annotation_text=f"Median ${df['Salary'].median():,.0f}",
                      annotation_font_color=COLORS["amber"], annotation_position="top left")
        st.plotly_chart(themed_fig(fig), use_container_width=True)

    # Salary by Education
    with col2:
        edu_stats = (df.groupby("Education Level", observed=True)["Salary"]
                     .agg(["mean", "median", "count"]).reset_index()
                     .sort_values("mean", ascending=True))
        edu_order_idx = ["High School", "Bachelor's", "Master's", "PhD"]
        edu_stats["Education Level"] = pd.Categorical(edu_stats["Education Level"],
                                                       categories=edu_order_idx, ordered=True)
        edu_stats = edu_stats.sort_values("Education Level")

        fig = go.Figure()
        fig.add_trace(go.Bar(
            y=edu_stats["Education Level"], x=edu_stats["mean"],
            orientation="h", name="Avg Salary",
            marker_color=[COLORS["violet"], COLORS["teal"], COLORS["amber"], COLORS["rose"]],
            text=[f"${v:,.0f}" for v in edu_stats["mean"]],
            textposition="outside", textfont=dict(color="#9ca3af", size=11),
            hovertemplate="<b>%{y}</b><br>Avg: $%{x:,.0f}<br>Count: %{customdata}<extra></extra>",
            customdata=edu_stats["count"]
        ))
        fig.update_layout(title="Avg Salary by Education Level", showlegend=False,
                          xaxis_title="Average Salary ($)")
        st.plotly_chart(themed_fig(fig), use_container_width=True)

    col3, col4 = st.columns(2)

    # Salary tier donut
    with col3:
        tier_order = ["Entry (<$60k)", "Mid ($60k-$100k)", "Senior ($100k-$150k)",
                      "Lead ($150k-$200k)", "Executive ($200k+)"]
        tier_counts = df["Salary Tier"].value_counts().reindex(tier_order, fill_value=0)
        fig = go.Figure(go.Pie(
            labels=tier_counts.index, values=tier_counts.values,
            hole=0.55,
            marker=dict(colors=[COLORS["blue"], COLORS["teal"], COLORS["violet"],
                                 COLORS["amber"], COLORS["rose"]],
                        line=dict(color="#1a1a2e", width=2)),
            textinfo="label+percent", textfont=dict(size=11),
        ))
        fig.update_layout(title="Salary Tier Distribution",
                          annotations=[dict(text=f"{len(df):,}<br>total", x=0.5, y=0.5,
                                            font_size=13, font_color="#e2e8f0", showarrow=False)])
        st.plotly_chart(themed_fig(fig, height=380), use_container_width=True)

    # Salary by Gender box
    with col4:
        fig = px.box(
            df, x="Gender", y="Salary", color="Gender",
            color_discrete_map={"Male": COLORS["blue"], "Female": COLORS["rose"], "Other": COLORS["amber"]},
            title="Salary Distribution by Gender",
            points="outliers",
        )
        fig.update_traces(marker=dict(size=3, opacity=0.5))
        st.plotly_chart(themed_fig(fig), use_container_width=True)

    # Key insights
    section("Key Insights")
    c1, c2 = st.columns(2)
    with c1:
        avg_m = df[df["Gender"] == "Male"]["Salary"].mean()
        avg_f = df[df["Gender"] == "Female"]["Salary"].mean()
        gap = (avg_m - avg_f) / avg_f * 100 if avg_f > 0 else 0
        insight(f"<strong>Gender pay gap:</strong> Male avg ${avg_m:,.0f} vs Female avg ${avg_f:,.0f} — a {gap:.1f}% difference", "rose")
        phd_avg = df[df["Education Level"] == "PhD"]["Salary"].mean()
        hs_avg  = df[df["Education Level"] == "High School"]["Salary"].mean()
        insight(f"<strong>Education premium:</strong> PhD holders earn {(phd_avg/hs_avg-1)*100:.0f}% more than High School graduates (${phd_avg:,.0f} vs ${hs_avg:,.0f})")
    with c2:
        corr = df[["Salary", "Years of Experience"]].corr().iloc[0, 1]
        insight(f"<strong>Experience correlation:</strong> Pearson r = {corr:.3f} — strong positive relationship between experience and salary", "teal")
        top_dept = df.groupby("Department")["Salary"].mean().idxmax()
        top_dept_sal = df.groupby("Department")["Salary"].mean().max()
        insight(f"<strong>Highest-paying dept:</strong> {top_dept} with avg salary ${top_dept_sal:,.0f}", "amber")


# TAB 2: SALARY DEEP DIVE


with tab2:
    section("Salary vs Experience & Age")
    col1, col2 = st.columns(2)

    with col1:
        # Scatter: Experience vs Salary coloured by Education
        sample = df.sample(min(2000, len(df)), random_state=42) if len(df) > 2000 else df
        fig = px.scatter(
            sample, x="Years of Experience", y="Salary",
            color="Education Level", trendline="ols",
            color_discrete_map={"High School": COLORS["blue"], "Bachelor's": COLORS["teal"],
                                 "Master's": COLORS["violet"], "PhD": COLORS["rose"]},
            title="Salary vs Years of Experience",
            hover_data=["Job Title", "Gender", "Age"],
            opacity=0.65, size_max=8,
        )
        fig.update_traces(marker=dict(size=5))
        st.plotly_chart(themed_fig(fig, height=420), use_container_width=True)

    with col2:
        # Scatter: Age vs Salary
        fig = px.scatter(
            sample, x="Age", y="Salary",
            color="Department",
            color_discrete_sequence=PALETTE,
            title="Salary vs Age by Department",
            hover_data=["Job Title", "Gender", "Years of Experience"],
            opacity=0.65,
        )
        fig.update_traces(marker=dict(size=5))
        st.plotly_chart(themed_fig(fig, height=420), use_container_width=True)

    section("Experience Band Analysis")
    col3, col4 = st.columns(2)

    with col3:
        exp_stats = (df.groupby("Exp Band", observed=True)["Salary"]
                     .agg(["mean", "median", "std", "count"]).reset_index())
        exp_stats.columns = ["Exp Band", "Mean", "Median", "Std Dev", "Count"]

        fig = go.Figure()
        fig.add_trace(go.Bar(
            x=exp_stats["Exp Band"], y=exp_stats["Mean"],
            name="Avg Salary", marker_color=COLORS["violet"],
            error_y=dict(type="data", array=exp_stats["Std Dev"] / 2,
                         color="#4a4a6a", thickness=1.5),
            hovertemplate="<b>%{x}</b><br>Avg: $%{y:,.0f}<br>Count: %{customdata}<extra></extra>",
            customdata=exp_stats["Count"],
        ))
        fig.add_trace(go.Scatter(
            x=exp_stats["Exp Band"], y=exp_stats["Median"],
            mode="lines+markers", name="Median",
            line=dict(color=COLORS["teal"], width=2, dash="dot"),
            marker=dict(size=8, color=COLORS["teal"]),
        ))
        fig.update_layout(title="Avg & Median Salary by Experience Band", barmode="group")
        st.plotly_chart(themed_fig(fig), use_container_width=True)

    with col4:
        # Heatmap: Edu x Exp Band avg salary
        heatmap_data = (df.groupby(["Education Level", "Exp Band"], observed=True)["Salary"]
                        .mean().reset_index())
        edu_order2 = ["High School", "Bachelor's", "Master's", "PhD"]
        heatmap_pivot = (heatmap_data
                         .pivot(index="Education Level", columns="Exp Band", values="Salary")
                         .reindex(edu_order2))

        fig = go.Figure(go.Heatmap(
            z=heatmap_pivot.values,
            x=[str(c) for c in heatmap_pivot.columns],
            y=heatmap_pivot.index.tolist(),
            colorscale=[[0, "#1e1e2e"], [0.5, "#7C3AED"], [1, "#f1f5f9"]],
            hovertemplate="Edu: %{y}<br>Exp: %{x}<br>Avg Salary: $%{z:,.0f}<extra></extra>",
            text=[[f"${v:,.0f}" if not np.isnan(v) else "—"
                   for v in row] for row in heatmap_pivot.values],
            texttemplate="%{text}",
            textfont=dict(size=10, color="#f1f5f9"),
        ))
        fig.update_layout(title="Avg Salary Heatmap: Education × Experience",
                          xaxis_title="Experience Band", yaxis_title="")
        st.plotly_chart(themed_fig(fig), use_container_width=True)

    section("Salary Percentiles")
    col5, col6 = st.columns([1, 2])

    with col5:
        pct_data = {
            "Percentile": ["P10", "P25", "P50", "P75", "P90", "P95", "P99"],
            "Salary": [
                df["Salary"].quantile(0.10), df["Salary"].quantile(0.25),
                df["Salary"].quantile(0.50), df["Salary"].quantile(0.75),
                df["Salary"].quantile(0.90), df["Salary"].quantile(0.95),
                df["Salary"].quantile(0.99),
            ]
        }
        pct_df = pd.DataFrame(pct_data)
        pct_df["Salary"] = pct_df["Salary"].map("${:,.0f}".format)
        st.dataframe(pct_df, use_container_width=True, hide_index=True,
                     column_config={"Percentile": st.column_config.TextColumn("Percentile"),
                                    "Salary": st.column_config.TextColumn("Salary")})

    with col6:
        # Gender salary distribution ridge / violin
        fig = px.violin(
            df[df["Gender"].isin(["Male", "Female"])],
            x="Education Level", y="Salary", color="Gender",
            category_orders={"Education Level": edu_order_idx},
            color_discrete_map={"Male": COLORS["blue"], "Female": COLORS["rose"]},
            box=True, points=False,
            title="Salary Violin: Education × Gender",
        )
        st.plotly_chart(themed_fig(fig, height=360), use_container_width=True)



# TAB 3: DEMOGRAPHICS


with tab3:
    section("Age & Gender Analysis")
    col1, col2, col3 = st.columns(3)

    with col1:
        gender_counts = df["Gender"].value_counts().reset_index()
        fig = go.Figure(go.Pie(
            labels=gender_counts["Gender"], values=gender_counts["count"],
            hole=0.5,
            marker=dict(colors=[COLORS["blue"], COLORS["rose"], COLORS["amber"]],
                        line=dict(color="#1a1a2e", width=2)),
            textinfo="label+percent",
        ))
        fig.update_layout(title="Gender Distribution")
        st.plotly_chart(themed_fig(fig, height=300), use_container_width=True)

    with col2:
        edu_counts = df["Education Level"].value_counts().reset_index()
        fig = go.Figure(go.Pie(
            labels=edu_counts["Education Level"], values=edu_counts["count"],
            hole=0.5,
            marker=dict(colors=[COLORS["violet"], COLORS["teal"], COLORS["amber"], COLORS["rose"]],
                        line=dict(color="#1a1a2e", width=2)),
            textinfo="label+percent",
        ))
        fig.update_layout(title="Education Distribution")
        st.plotly_chart(themed_fig(fig, height=300), use_container_width=True)

    with col3:
        tier_counts2 = df["Salary Tier"].value_counts().reset_index()
        fig = go.Figure(go.Pie(
            labels=tier_counts2["Salary Tier"], values=tier_counts2["count"],
            hole=0.5,
            marker=dict(colors=PALETTE[:5], line=dict(color="#1a1a2e", width=2)),
            textinfo="label+percent",
        ))
        fig.update_layout(title="Salary Tier Distribution")
        st.plotly_chart(themed_fig(fig, height=300), use_container_width=True)

    section("Age Distribution & Bands")
    col4, col5 = st.columns(2)

    with col4:
        age_band_counts = df.groupby("Age Band", observed=True).size().reset_index(name="Count")
        fig = px.bar(
            age_band_counts, x="Age Band", y="Count",
            color="Count", color_continuous_scale=["#3d3d5c", "#7C3AED", "#e879f9"],
            title="Applicant Count by Age Band",
        )
        fig.update_coloraxes(showscale=False)
        st.plotly_chart(themed_fig(fig), use_container_width=True)

    with col5:
        age_sal = df.groupby("Age Band", observed=True)["Salary"].mean().reset_index()
        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=age_sal["Age Band"], y=age_sal["Salary"],
            mode="lines+markers",
            line=dict(color=COLORS["teal"], width=2.5),
            marker=dict(size=10, color=COLORS["violet"],
                        line=dict(color=COLORS["teal"], width=2)),
            fill="tozeroy", fillcolor="rgba(13,148,136,0.08)",
            hovertemplate="Age %{x}<br>Avg Salary: $%{y:,.0f}<extra></extra>",
        ))
        fig.update_layout(title="Avg Salary by Age Band")
        st.plotly_chart(themed_fig(fig), use_container_width=True)

    section("Education & Experience Breakdown")
    col6, col7 = st.columns(2)

    with col6:
        # Stacked bar: gender x education
        cross = pd.crosstab(df["Education Level"], df["Gender"])
        cross = cross.reindex(edu_order_idx)
        fig = go.Figure()
        gender_colors = {"Male": COLORS["blue"], "Female": COLORS["rose"], "Other": COLORS["amber"]}
        for g in cross.columns:
            fig.add_trace(go.Bar(
                name=g, x=cross.index, y=cross[g],
                marker_color=gender_colors.get(g, COLORS["violet"]),
            ))
        fig.update_layout(barmode="stack", title="Education × Gender (Stacked)")
        st.plotly_chart(themed_fig(fig), use_container_width=True)

    with col7:
        # Exp distribution histogram by gender
        fig = px.histogram(
            df[df["Gender"].isin(["Male", "Female"])],
            x="Years of Experience", color="Gender", nbins=35, barmode="overlay",
            color_discrete_map={"Male": COLORS["blue"], "Female": COLORS["rose"]},
            opacity=0.75, title="Experience Distribution by Gender",
        )
        st.plotly_chart(themed_fig(fig), use_container_width=True)



# TAB 4: JOB & DEPARTMENT


with tab4:
    section("Department Overview")
    col1, col2 = st.columns(2)

    with col1:
        dept_stats = (df.groupby("Department")["Salary"]
                      .agg(["mean", "count"]).reset_index()
                      .sort_values("mean", ascending=True)
                      .rename(columns={"mean": "Avg Salary", "count": "Headcount"}))
        fig = go.Figure()
        fig.add_trace(go.Bar(
            y=dept_stats["Department"], x=dept_stats["Avg Salary"],
            orientation="h",
            marker=dict(
                color=dept_stats["Avg Salary"],
                colorscale=[[0, "#3d3d5c"], [0.5, "#7C3AED"], [1, "#e879f9"]],
                showscale=False,
            ),
            text=[f"${v:,.0f}  ({c:,})" for v, c in zip(dept_stats["Avg Salary"], dept_stats["Headcount"])],
            textposition="outside", textfont=dict(color="#9ca3af", size=10),
            hovertemplate="<b>%{y}</b><br>Avg: $%{x:,.0f}<br>Count: %{text}<extra></extra>",
        ))
        fig.update_layout(title="Avg Salary by Department", xaxis_title="Average Salary ($)")
        st.plotly_chart(themed_fig(fig, height=420), use_container_width=True)

    with col2:
        dept_box = df[df["Department"].isin(dept_stats["Department"].tolist())]
        fig = px.box(
            dept_box, y="Department", x="Salary", color="Department",
            color_discrete_sequence=PALETTE,
            title="Salary Range by Department",
            orientation="h", points=False,
        )
        fig.update_layout(showlegend=False, yaxis_title="")
        st.plotly_chart(themed_fig(fig, height=420), use_container_width=True)

    section(f"Top {top_n} Job Titles by Avg Salary")
    col3, col4 = st.columns([2, 1])

    with col3:
        top_titles = (df.groupby("Job Title")["Salary"]
                      .agg(["mean", "count"]).reset_index()
                      .query("count >= 3")
                      .sort_values("mean", ascending=False)
                      .head(top_n)
                      .rename(columns={"mean": "Avg Salary", "count": "Count"}))
        fig = px.bar(
            top_titles.sort_values("Avg Salary"),
            y="Job Title", x="Avg Salary", orientation="h",
            color="Avg Salary",
            color_continuous_scale=["#3d3d5c", "#7C3AED", "#f0abfc"],
            text=[f"${v:,.0f}" for v in top_titles.sort_values("Avg Salary")["Avg Salary"]],
            title=f"Top {top_n} Job Titles — Avg Salary",
            hover_data={"Count": True, "Avg Salary": ":.0f"},
        )
        fig.update_traces(textposition="outside", textfont_size=10)
        fig.update_coloraxes(showscale=False)
        fig.update_layout(yaxis_title="", xaxis_title="Avg Salary ($)")
        st.plotly_chart(themed_fig(fig, height=max(350, top_n * 28)), use_container_width=True)

    with col4:
        top_titles_display = top_titles.copy()
        top_titles_display["Avg Salary"] = top_titles_display["Avg Salary"].map("${:,.0f}".format)
        st.dataframe(
            top_titles_display[["Job Title", "Avg Salary", "Count"]],
            use_container_width=True,
            hide_index=True,
            height=max(350, top_n * 28),
        )

    section("Department × Education × Gender")
    col5, col6 = st.columns(2)

    with col5:
        dept_edu = (df.groupby(["Department", "Education Level"], observed=True)["Salary"]
                    .mean().reset_index()
                    .rename(columns={"Salary": "Avg Salary"}))
        dept_edu["Education Level"] = pd.Categorical(dept_edu["Education Level"],
                                                       categories=edu_order_idx, ordered=True)
        fig = px.bar(
            dept_edu, x="Department", y="Avg Salary", color="Education Level",
            barmode="group",
            color_discrete_map={"High School": COLORS["blue"], "Bachelor's": COLORS["teal"],
                                 "Master's": COLORS["violet"], "PhD": COLORS["rose"]},
            title="Avg Salary by Department & Education",
        )
        fig.update_layout(xaxis_tickangle=-30)
        st.plotly_chart(themed_fig(fig, height=380), use_container_width=True)

    with col6:
        dept_gender = (df[df["Gender"].isin(["Male", "Female"])]
                       .groupby(["Department", "Gender"], observed=True)["Salary"]
                       .mean().reset_index()
                       .rename(columns={"Salary": "Avg Salary"}))
        fig = px.bar(
            dept_gender, x="Department", y="Avg Salary", color="Gender",
            barmode="group",
            color_discrete_map={"Male": COLORS["blue"], "Female": COLORS["rose"]},
            title="Avg Salary by Department & Gender",
        )
        fig.update_layout(xaxis_tickangle=-30)
        st.plotly_chart(themed_fig(fig, height=380), use_container_width=True)

    # Sunburst
    section("Department → Education → Gender Hierarchy")
    sunburst_data = (df.groupby(["Department", "Education Level", "Gender"], observed=True)["Salary"]
                     .agg(["mean", "count"]).reset_index()
                     .rename(columns={"mean": "Avg Salary", "count": "Count"}))
    fig = px.sunburst(
        sunburst_data,
        path=["Department", "Education Level", "Gender"],
        values="Count",
        color="Avg Salary",
        color_continuous_scale=["#1e1e2e", "#7C3AED", "#f0abfc"],
        title="Salary Hierarchy: Department → Education → Gender",
        hover_data={"Avg Salary": ":.0f"},
    )
    fig.update_layout(height=550)
    st.plotly_chart(themed_fig(fig, height=550), use_container_width=True)



# TAB 5: DATA EXPLORER


with tab5:
    section("Raw Data Explorer")

    sub_col1, sub_col2, sub_col3 = st.columns(3)
    with sub_col1:
        search_title = st.text_input("Search Job Title", placeholder="e.g. Engineer, Manager...")
    with sub_col2:
        sort_col = st.selectbox("Sort By", ["Salary", "Age", "Years of Experience"])
    with sub_col3:
        sort_order = st.radio("Order", ["Descending", "Ascending"], horizontal=True)

    display_df = df.copy()
    if search_title:
        display_df = display_df[display_df["Job Title"].str.contains(search_title, case=False, na=False)]

    display_df = display_df.sort_values(sort_col, ascending=(sort_order == "Ascending"))

    st.caption(f"Showing {len(display_df):,} records")

    display_cols = ["Age", "Gender", "Education Level", "Job Title", "Department",
                    "Years of Experience", "Salary", "Age Band", "Exp Band", "Salary Tier"]

    st.dataframe(
        display_df[display_cols].reset_index(drop=True),
        use_container_width=True,
        height=450,
        column_config={
            "Salary": st.column_config.NumberColumn("Salary", format="$%d"),
            "Years of Experience": st.column_config.NumberColumn("Exp (yrs)", format="%.1f"),
            "Age": st.column_config.NumberColumn("Age"),
        }
    )

    section("Statistical Summary")
    col1, col2 = st.columns(2)
    with col1:
        st.markdown("**Numeric columns**")
        num_summary = display_df[["Age", "Years of Experience", "Salary"]].describe().round(2)
        num_summary_display = num_summary.copy()
        num_summary_display.loc["mean"].apply(lambda x: f"{x:.1f}")
       

    with col2:
        st.markdown("**Categorical breakdown**")
        cat_data = []
        for col_name in ["Gender", "Education Level", "Department", "Salary Tier"]:
            vc = display_df[col_name].value_counts()
            top = vc.index[0] if len(vc) else "—"
            cat_data.append({"Column": col_name, "Unique": display_df[col_name].nunique(),
                              "Most Common": top, "Count": vc.iloc[0] if len(vc) else 0})
        st.dataframe(pd.DataFrame(cat_data), use_container_width=True, hide_index=True)

    section("Correlation Analysis")
    col3, col4 = st.columns(2)

    with col3:
        corr_matrix = display_df[["Age", "Years of Experience", "Salary"]].corr()
        fig = go.Figure(go.Heatmap(
            z=corr_matrix.values,
            x=corr_matrix.columns.tolist(),
            y=corr_matrix.index.tolist(),
            colorscale=[[0, "#1e1e2e"], [0.5, "#7C3AED"], [1, "#f0abfc"]],
            zmin=-1, zmax=1,
            text=[[f"{v:.3f}" for v in row] for row in corr_matrix.values],
            texttemplate="%{text}",
            textfont=dict(size=13, color="#f1f5f9"),
            hovertemplate="%{x} vs %{y}: %{z:.3f}<extra></extra>",
        ))
        fig.update_layout(title="Correlation Matrix")
        st.plotly_chart(themed_fig(fig, height=300), use_container_width=True)

    with col4:
        # Pair-wise scatter: Exp vs Salary coloured by Tier
        sample2 = display_df.sample(min(1500, len(display_df)), random_state=1)
        fig = px.scatter(
            sample2, x="Years of Experience", y="Salary",
            color="Salary Tier",
            color_discrete_sequence=PALETTE,
            title="Experience vs Salary (filtered data)",
            opacity=0.7,
            hover_data=["Job Title", "Gender", "Education Level"],
        )
        fig.update_traces(marker=dict(size=5))
        st.plotly_chart(themed_fig(fig, height=300), use_container_width=True)

    # Download
    section("Export Data")
    csv_export = display_df[display_cols].to_csv(index=False)
    st.download_button(
        label="Download filtered data as CSV",
        data=csv_export,
        file_name="salary_data_filtered.csv",
        mime="text/csv",
        use_container_width=False,
    )
