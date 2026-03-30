# 💼 Salary Intelligence Dashboard

A comprehensive, interactive data analysis dashboard built with **Streamlit** and **Plotly**, analysing salary patterns across 6,700+ professionals.

---

## 🚀 Quick Start

### 1. Install dependencies
```bash
pip install -r requirements.txt
```

### 2. Run the dashboard
```bash
streamlit run app.py
```

### 3. Open in browser
The dashboard will open automatically at `http://localhost:8501`

---

## 📊 Dashboard Sections

### Tab 1 — Overview
- Salary histogram with mean/median lines
- Avg salary by education level
- Salary tier donut chart
- Salary box plots by gender
- Auto-generated key insights

### Tab 2 — Salary Deep Dive
- Salary vs Experience scatter (coloured by education) with OLS trendline
- Salary vs Age scatter by department
- Avg & median salary by experience band with error bars
- Salary heatmap: Education × Experience
- Salary percentile table (P10 → P99)
- Salary violin plots: Education × Gender

### Tab 3 — Demographics
- Gender distribution donut
- Education distribution donut
- Salary tier donut
- Applicant count by age band
- Avg salary trend by age band
- Education × Gender stacked bar
- Experience distribution histogram by gender

### Tab 4 — Job & Department
- Avg salary by department (horizontal bar)
- Salary range box plots by department
- Top N job titles by avg salary (configurable in sidebar)
- Department × Education grouped bar
- Department × Gender pay comparison
- Sunburst: Department → Education → Gender hierarchy

### Tab 5 — Data Explorer
- Full searchable, sortable data table
- Statistical summary (numeric + categorical)
- Correlation matrix heatmap
- Experience vs Salary scatter
- CSV export button

---

## 🎛️ Sidebar Filters

All filters apply across every chart in real time:

| Filter | Type |
|--------|------|
| Gender | Multi-select |
| Education Level | Multi-select |
| Department | Multi-select |
| Salary Range | Range slider |
| Years of Experience | Range slider |
| Age Range | Range slider |
| Top N Job Titles | Number slider |

---

## 📁 Project Structure

```
salary_dashboard/
├── app.py                  ← Main Streamlit application
├── Salary_Data.csv         ← Dataset (6,704 records)
├── requirements.txt        ← Python dependencies
├── README.md
└── .streamlit/
    └── config.toml         ← Dark theme configuration
```

---

## 📦 Dataset

**Salary_Data.csv** — 6,704 records with 6 columns:

| Column | Description |
|--------|-------------|
| Age | Employee age (21–62) |
| Gender | Male / Female / Other |
| Education Level | High School / Bachelor's / Master's / PhD |
| Job Title | 193 unique titles |
| Years of Experience | 0–34 years |
| Salary | Annual salary ($350 – $250,000) |

**Derived columns** added by the app:
- `Age Band` — 10-year age groups
- `Exp Band` — experience brackets
- `Salary Tier` — Entry / Mid / Senior / Lead / Executive
- `Department` — auto-classified from job title

---

## 🛠️ Tech Stack

| Library | Purpose |
|---------|---------|
| Streamlit | Web framework & UI |
| Plotly Express | Interactive charts |
| Plotly Graph Objects | Custom charts & heatmaps |
| pandas | Data manipulation |
| numpy | Numerical operations |
