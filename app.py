import streamlit as st
import pandas as pd
import html
import plotly.express as px
import plotly.graph_objects as go
import plotly.io as pio
from supabase import create_client

# ============================================================
# 1. PAGE CONFIGURATION
# ============================================================

st.set_page_config(
    page_title="South African Banking Customer Churn",
    layout="wide"
)

# ------------------------------------------------------------
# Theme: cool blue-grey surfaces, navy and blue for structure,
# teal and green for healthy / retained customers.
# ------------------------------------------------------------

BACKGROUND = "#EAF0F5"
CARD = "#F8FAFC"
CARD_BORDER = "#CBD8E4"
NAVY = "#0B2A4A"
BLUE = "#1D5FA8"
STEEL = "#1D4E89"
TEAL = "#0F8B8D"
GREEN = "#2E9E6B"
INK = "#16263A"
MUTED = "#5B7189"

STATUS_COLOURS = {"Active": GREEN, "Churned": STEEL}
CHURN_SCALE = [GREEN, TEAL, "#2D7FC1", NAVY]   # low -> high churn

pio.templates["bank"] = go.layout.Template(
    layout=dict(
        font=dict(
            family="'IBM Plex Sans', 'Segoe UI', Helvetica, Arial, sans-serif",
            color=INK,
            size=13
        ),
        title=dict(
            font=dict(
                family="'IBM Plex Sans', 'Segoe UI', sans-serif",
                size=17,
                color=NAVY
            ),
            x=0.01
        ),
        paper_bgcolor=CARD,
        plot_bgcolor=CARD,
        colorway=[
            BLUE, TEAL, GREEN, NAVY,
            "#5B9BD5", "#7CC4A4", "#3B6E8F"
        ],
        xaxis=dict(
            gridcolor="#E1E9F1", linecolor="#A9BBCD",
            zeroline=False, ticks="outside", tickcolor="#A9BBCD"
        ),
        yaxis=dict(
            gridcolor="#E1E9F1", linecolor="#A9BBCD",
            zeroline=False
        ),
        legend=dict(bgcolor="rgba(0,0,0,0)"),
        hoverlabel=dict(
            bgcolor=NAVY,
            font=dict(color="#FFFFFF")
        ),
        margin=dict(l=40, r=20, t=60, b=40)
    )
)
pio.templates.default = "bank"


def show_chart(fig):
    """Render a Plotly chart using the dashboard theme."""
    fig.update_layout(coloraxis_showscale=False)
    fig.update_traces(
        selector=dict(type="bar"),
        marker_line_width=0,
        textposition="outside",
        cliponaxis=False
    )
    fig.update_traces(selector=dict(type="histogram"), opacity=0.78)
    fig.update_traces(
        selector=dict(type="pie"),
        marker=dict(line=dict(color=CARD, width=3))
    )
    # theme=None stops Streamlit overriding the custom colours.
    st.plotly_chart(fig, use_container_width=True, theme=None)


def insight_card(label, text, colour):
    """Show one business insight as a card."""
    st.markdown(
        f'<div class="insight" style="border-left-color:{colour};">'
        f'<div class="insight-label">{html.escape(label)}</div>'
        f'<div class="insight-text">{text}</div>'
        "</div>",
        unsafe_allow_html=True
    )


st.markdown(
    """
<style>
@import url('https://fonts.googleapis.com/css2?family=IBM+Plex+Sans:wght@400;500;600;700&display=swap');

/* ---------- Page ---------- */
.stApp {
    background-color: #EAF0F5;
    color: #16263A;
    font-family: 'IBM Plex Sans', 'Segoe UI', Helvetica, Arial, sans-serif;
}
header[data-testid="stHeader"] { background: transparent; }
.block-container {
    padding-top: 2rem;
    padding-bottom: 3rem;
    max-width: 1280px;
}
.stApp p, .stApp li, .stApp label, .stApp span { color: #16263A; }
.stApp [data-testid="stCaptionContainer"] { color: #5B7189; }

/* ---------- Header banner ---------- */
.hero {
    background: linear-gradient(110deg, #0B2A4A 0%, #12406E 55%, #0F7B8A 100%);
    border-radius: 10px;
    padding: 2rem 2.3rem 1.8rem 2.3rem;
    margin-bottom: 1.8rem;
    box-shadow: 0 4px 14px rgba(11, 42, 74, 0.22);
    position: relative;
    overflow: hidden;
}
.hero-eyebrow {
    color: #8FD3B6 !important;
    font-size: 0.76rem;
    font-weight: 600;
    letter-spacing: 0.18em;
    text-transform: uppercase;
    margin-bottom: 0.45rem;
}
.hero-title {
    color: #FFFFFF !important;
    font-size: 2.1rem;
    font-weight: 600;
    line-height: 1.25;
    margin: 0 0 0.6rem 0;
}
.hero-text {
    color: #D5E3F0 !important;
    font-size: 1rem;
    max-width: 760px;
    margin: 0 0 1rem 0;
}
.hero-tags {
    color: #9FB9D2 !important;
    font-size: 0.8rem;
    letter-spacing: 0.05em;
}
.hero-bar {
    position: absolute;
    left: 0; right: 0; bottom: 0;
    height: 5px;
    background: linear-gradient(90deg, #1D5FA8 0%, #0F8B8D 50%, #2E9E6B 100%);
}

/* ---------- Section headings ---------- */
.stApp h3 {
    color: #0B2A4A;
    font-weight: 600;
    font-size: 1.3rem;
    border-bottom: 1px solid #C2D1DF;
    padding-bottom: 0.5rem;
    margin-top: 0.8rem;
    position: relative;
}
.stApp h3::after {
    content: "";
    position: absolute;
    left: 0; bottom: -1px;
    width: 64px; height: 3px;
    background: #0F8B8D;
}
hr { border-color: #C2D1DF !important; }

/* ---------- KPI cards ---------- */
div[data-testid="stMetric"] {
    background-color: #F8FAFC;
    border: 1px solid #CBD8E4;
    border-left: 4px solid #1D5FA8;
    padding: 16px 18px;
    border-radius: 8px;
    box-shadow: 0 1px 3px rgba(11, 42, 74, 0.08);
}
div[data-testid="stHorizontalBlock"] > div:nth-child(2) div[data-testid="stMetric"] { border-left-color: #0F8B8D; }
div[data-testid="stHorizontalBlock"] > div:nth-child(3) div[data-testid="stMetric"] { border-left-color: #2E9E6B; }
div[data-testid="stHorizontalBlock"] > div:nth-child(4) div[data-testid="stMetric"] { border-left-color: #0B2A4A; }
div[data-testid="stMetricLabel"] p {
    color: #5B7189 !important;
    font-size: 0.78rem;
    font-weight: 600;
    letter-spacing: 0.07em;
    text-transform: uppercase;
}
div[data-testid="stMetricValue"] {
    color: #0B2A4A;
    font-weight: 600;
    font-variant-numeric: tabular-nums;
}

/* ---------- Chart panels ---------- */
div[data-testid="stPlotlyChart"] {
    background: #F8FAFC;
    border: 1px solid #CBD8E4;
    border-radius: 8px;
    padding: 6px;
    box-shadow: 0 1px 3px rgba(11, 42, 74, 0.08);
    overflow: hidden;
}

/* ---------- Insight cards ---------- */
.insight {
    background: #F8FAFC;
    border: 1px solid #CBD8E4;
    border-left: 5px solid #1D5FA8;
    border-radius: 8px;
    padding: 14px 18px;
    margin-bottom: 12px;
    box-shadow: 0 1px 3px rgba(11, 42, 74, 0.08);
}
.insight-label {
    color: #5B7189;
    font-size: 0.75rem;
    font-weight: 600;
    letter-spacing: 0.09em;
    text-transform: uppercase;
    margin-bottom: 4px;
}
.insight-text {
    color: #16263A;
    font-size: 0.98rem;
}

/* ---------- Sidebar ---------- */
section[data-testid="stSidebar"] {
    background-color: #DCE6F0;
    border-right: 1px solid #BCCCDC;
}
section[data-testid="stSidebar"] h2 {
    color: #0B2A4A;
    font-weight: 600;
    font-size: 1.25rem;
}
div[data-baseweb="select"] > div,
div[data-baseweb="base-input"],
div[data-baseweb="input"] {
    background-color: #F4F8FB !important;
    border-color: #B5C7D8 !important;
}
span[data-baseweb="tag"] { background-color: #1D5FA8 !important; }
span[data-baseweb="tag"] span { color: #FFFFFF !important; }
input { color: #16263A !important; }

/* ---------- Buttons ---------- */
.stDownloadButton button, .stButton button {
    background-color: #1D5FA8;
    color: #FFFFFF;
    border: 1px solid #174D88;
    border-radius: 6px;
    padding: 0.5rem 1.4rem;
    font-weight: 600;
}
.stDownloadButton button:hover, .stButton button:hover {
    background-color: #0B2A4A;
    border-color: #0B2A4A;
    color: #FFFFFF;
}
.stDownloadButton button p, .stButton button p { color: inherit !important; }

/* ---------- Alerts, tables, expander ---------- */
div[data-testid="stAlert"] {
    background-color: #E3EEF8;
    border: 1px solid #B9D0E6;
    border-radius: 8px;
}
div[data-testid="stDataFrame"] {
    border: 1px solid #CBD8E4;
    border-radius: 8px;
    overflow: hidden;
}
div[data-testid="stExpander"] {
    background-color: #F8FAFC;
    border: 1px solid #CBD8E4;
    border-radius: 8px;
}
</style>
""",
    unsafe_allow_html=True
)

st.markdown(
    '<div class="hero">'
    '<div class="hero-eyebrow">Customer Retention Analytics</div>'
    '<div class="hero-title">South African Banking Customer Churn Analysis</div>'
    '<p class="hero-text">An interactive banking analytics dashboard exploring '
    'customer retention, churn patterns, account activity, customer balances '
    'and credit scores.</p>'
    '<div class="hero-tags">Python &bull; Pandas &bull; Plotly &bull; '
    'Streamlit &bull; Supabase</div>'
    '<div class="hero-bar"></div>'
    '</div>',
    unsafe_allow_html=True
)


# ============================================================
# 2. SUPABASE CONNECTION
# ============================================================

@st.cache_resource
def connect_to_supabase():
    url = st.secrets["SUPABASE_URL"]
    key = st.secrets["SUPABASE_KEY"]

    return create_client(url, key)


# ============================================================
# 3. LOAD DATA FROM SUPABASE OR CSV
# ============================================================

@st.cache_data(ttl=300)
def load_data():
    try:
        supabase = connect_to_supabase()

        response = (
            supabase.table("banking_customer_churn")
            .select("*")
            .order("customer_id")
            .limit(1000)
            .execute()
        )

        if response.data:
            return pd.DataFrame(response.data)

        st.warning(
            "The Supabase table is empty. "
            "Loading the local CSV instead."
        )

    except Exception as error:
        st.warning(
            "Could not load data from Supabase. "
            "Attempting to load the local CSV instead."
        )
        st.caption(f"Connection detail: {error}")

    return pd.read_csv(
        "south_african_banking_customer_churn.csv"
    )


try:
    df = load_data()

except FileNotFoundError:
    st.error(
        "Dataset not found. Place "
        "'south_african_banking_customer_churn.csv' "
        "in the same folder as app.py."
    )
    st.stop()

except Exception as error:
    st.error(f"Unable to load the dataset: {error}")
    st.stop()


# ============================================================
# 4. DATA CLEANING AND VALIDATION
# ============================================================

required_columns = [
    "customer_id",
    "age",
    "gender",
    "province",
    "account_type",
    "tenure_years",
    "monthly_transactions",
    "monthly_balance",
    "credit_score",
    "churn_status"
]

missing_columns = [
    column for column in required_columns
    if column not in df.columns
]

if missing_columns:
    st.error(
        "The dataset is missing these columns: "
        + ", ".join(missing_columns)
    )
    st.stop()

df = df[required_columns].copy()

original_row_count = len(df)

# Convert numeric fields
numeric_columns = [
    "customer_id",
    "age",
    "tenure_years",
    "monthly_transactions",
    "monthly_balance",
    "credit_score"
]

for column in numeric_columns:
    df[column] = pd.to_numeric(
        df[column], errors="coerce"
    )

# Standardise text fields
text_columns = [
    "gender",
    "province",
    "account_type",
    "churn_status"
]

for column in text_columns:
    df[column] = (
        df[column]
        .astype("string")
        .str.strip()
    )

# Remove records missing essential fields
df = df.dropna(subset=required_columns).copy()

# Remove duplicate customer IDs
before_duplicates = len(df)

df = df.drop_duplicates(
    subset=["customer_id"],
    keep="first"
).copy()

duplicates_removed = before_duplicates - len(df)

# Validate numeric ranges
df = df[
    (df["age"] >= 18)
    & (df["age"] <= 120)
    & (df["tenure_years"] >= 0)
    & (df["monthly_transactions"] >= 0)
    & (df["monthly_balance"] >= 0)
    & (df["credit_score"] >= 300)
    & (df["credit_score"] <= 850)
].copy()

# Standardise category labels
for column in text_columns:
    df[column] = df[column].str.title()

# Only allow known churn labels
df = df[
    df["churn_status"].isin(["Active", "Churned"])
].copy()

if df.empty:
    st.error(
        "No valid customer records remain after cleaning."
    )
    st.stop()

# Create useful analysis columns
df["customer_segment"] = pd.cut(
    df["age"],
    bins=[17, 25, 35, 45, 55, 120],
    labels=[
        "18–25",
        "26–35",
        "36–45",
        "46–55",
        "56+"
    ]
)

df["tenure_group"] = pd.cut(
    df["tenure_years"],
    bins=[-1, 2, 5, 10, float("inf")],
    labels=[
        "0–2 Years",
        "3–5 Years",
        "6–10 Years",
        "Over 10 Years"
    ]
)

df["churn_flag"] = (
    df["churn_status"] == "Churned"
).astype(int)


# ============================================================
# 5. SIDEBAR FILTERS
# ============================================================

st.sidebar.header("Customer Filters")

st.sidebar.caption(
    "Filter the dashboard to investigate different "
    "customer groups."
)

selected_provinces = st.sidebar.multiselect(
    "Province",
    options=sorted(df["province"].unique()),
    default=sorted(df["province"].unique())
)

selected_genders = st.sidebar.multiselect(
    "Gender",
    options=sorted(df["gender"].unique()),
    default=sorted(df["gender"].unique())
)

selected_accounts = st.sidebar.multiselect(
    "Account Type",
    options=sorted(df["account_type"].unique()),
    default=sorted(df["account_type"].unique())
)

selected_statuses = st.sidebar.multiselect(
    "Customer Status",
    options=["Active", "Churned"],
    default=["Active", "Churned"]
)

age_min = int(df["age"].min())
age_max = int(df["age"].max())

age_range = st.sidebar.slider(
    "Customer Age",
    min_value=age_min,
    max_value=age_max,
    value=(age_min, age_max)
)

tenure_min = int(df["tenure_years"].min())
tenure_max = int(df["tenure_years"].max())

tenure_range = st.sidebar.slider(
    "Years with Bank",
    min_value=tenure_min,
    max_value=tenure_max,
    value=(tenure_min, tenure_max)
)


# ============================================================
# 6. APPLY FILTERS
# ============================================================

filtered_df = df[
    df["province"].isin(selected_provinces)
    & df["gender"].isin(selected_genders)
    & df["account_type"].isin(selected_accounts)
    & df["churn_status"].isin(selected_statuses)
    & df["age"].between(
        age_range[0], age_range[1]
    )
    & df["tenure_years"].between(
        tenure_range[0], tenure_range[1]
    )
].copy()

if filtered_df.empty:
    st.warning(
        "No customers match the selected filters. "
        "Please adjust your selections."
    )
    st.stop()


# ============================================================
# 7. KEY PERFORMANCE INDICATORS
# ============================================================

total_customers = filtered_df["customer_id"].nunique()

churned_customers = filtered_df.loc[
    filtered_df["churn_status"] == "Churned",
    "customer_id"
].nunique()

active_customers = filtered_df.loc[
    filtered_df["churn_status"] == "Active",
    "customer_id"
].nunique()

churn_rate = (
    churned_customers / total_customers * 100
    if total_customers > 0
    else 0
)

average_balance = filtered_df["monthly_balance"].mean()
average_credit_score = filtered_df["credit_score"].mean()
average_transactions = filtered_df[
    "monthly_transactions"
].mean()

col1, col2, col3, col4 = st.columns(4)

col1.metric(
    "Total Customers",
    f"{total_customers:,}"
)

col2.metric(
    "Churn Rate",
    f"{churn_rate:.2f}%"
)

col3.metric(
    "Average Balance",
    f"R {average_balance:,.2f}"
)

col4.metric(
    "Average Credit Score",
    f"{average_credit_score:.0f}"
)

col5, col6 = st.columns(2)

col5.metric(
    "Active Customers",
    f"{active_customers:,}"
)

col6.metric(
    "Churned Customers",
    f"{churned_customers:,}"
)

st.caption(
    "All KPIs reflect the customers selected by your filters."
)

st.divider()


# ============================================================
# 8. CUSTOMER STATUS ANALYSIS
# ============================================================

st.subheader("Customer Retention Overview")

status_col1, status_col2 = st.columns(2)

status_summary = (
    filtered_df["churn_status"]
    .value_counts()
    .rename_axis("churn_status")
    .reset_index(name="customers")
)

with status_col1:
    fig_status = px.pie(
        status_summary,
        names="churn_status",
        values="customers",
        color="churn_status",
        color_discrete_map=STATUS_COLOURS,
        hole=0.45,
        title="Active vs Churned Customers"
    )

    show_chart(fig_status)

with status_col2:
    fig_status_bar = px.bar(
        status_summary,
        x="churn_status",
        y="customers",
        color="churn_status",
        color_discrete_map=STATUS_COLOURS,
        text="customers",
        title="Customer Count by Status",
        labels={
            "churn_status": "Customer Status",
            "customers": "Number of Customers"
        }
    )

    fig_status_bar.update_layout(
        showlegend=False
    )

    show_chart(fig_status_bar)


# ============================================================
# 9. CHURN BY PROVINCE
# ============================================================

st.subheader("Customer Churn by Province")

province_summary = (
    filtered_df.groupby("province", as_index=False)
    .agg(
        total_customers=("customer_id", "nunique"),
        churned_customers=("churn_flag", "sum")
    )
)

province_summary["churn_rate"] = (
    province_summary["churned_customers"]
    / province_summary["total_customers"] * 100
)

province_summary = province_summary.sort_values(
    "churn_rate",
    ascending=False
)

fig_province = px.bar(
    province_summary,
    x="province",
    y="churn_rate",
    color="churn_rate",
    color_continuous_scale=CHURN_SCALE,
    text=province_summary["churn_rate"].map(
        lambda value: f"{value:.1f}%"
    ),
    title="Churn Rate by Province",
    labels={
        "province": "Province",
        "churn_rate": "Churn Rate (%)"
    },
    hover_data=[
        "total_customers",
        "churned_customers"
    ]
)

fig_province.update_layout(
    xaxis_tickangle=-35
)

show_chart(fig_province)

with st.expander("View Province Summary Table"):
    st.dataframe(
        province_summary.round(2),
        use_container_width=True,
        hide_index=True
    )


# ============================================================
# 10. CHURN BY ACCOUNT TYPE
# ============================================================

st.subheader("Account Type Analysis")

account_summary = (
    filtered_df.groupby("account_type", as_index=False)
    .agg(
        total_customers=("customer_id", "nunique"),
        churned_customers=("churn_flag", "sum"),
        average_balance=("monthly_balance", "mean"),
        average_transactions=(
            "monthly_transactions", "mean"
        )
    )
)

account_summary["churn_rate"] = (
    account_summary["churned_customers"]
    / account_summary["total_customers"] * 100
)

account_col1, account_col2 = st.columns(2)

with account_col1:
    fig_account_churn = px.bar(
        account_summary.sort_values(
            "churn_rate", ascending=False
        ),
        x="account_type",
        y="churn_rate",
        color="churn_rate",
        color_continuous_scale=CHURN_SCALE,
        title="Churn Rate by Account Type",
        labels={
            "account_type": "Account Type",
            "churn_rate": "Churn Rate (%)"
        },
        text=account_summary.sort_values(
            "churn_rate", ascending=False
        )["churn_rate"].map(
            lambda value: f"{value:.1f}%"
        )
    )

    fig_account_churn.update_layout(
        showlegend=False
    )

    show_chart(fig_account_churn)

with account_col2:
    fig_account_count = px.bar(
        account_summary,
        x="account_type",
        y="total_customers",
        color="account_type",
        title="Customers by Account Type",
        labels={
            "account_type": "Account Type",
            "total_customers": "Customers"
        }
    )

    fig_account_count.update_layout(
        showlegend=False
    )

    show_chart(fig_account_count)


# ============================================================
# 11. CUSTOMER AGE ANALYSIS
# ============================================================

st.subheader("Customer Age Analysis")

age_col1, age_col2 = st.columns(2)

with age_col1:
    fig_age = px.histogram(
        filtered_df,
        x="age",
        color="churn_status",
        color_discrete_map=STATUS_COLOURS,
        nbins=20,
        barmode="overlay",
        title="Age Distribution by Customer Status",
        labels={
            "age": "Customer Age",
            "count": "Customers"
        }
    )

    show_chart(fig_age)

with age_col2:
    age_summary = (
        filtered_df.groupby(
            "customer_segment",
            observed=True
        )
        .agg(
            total_customers=("customer_id", "nunique"),
            churned_customers=("churn_flag", "sum")
        )
        .reset_index()
    )

    age_summary["churn_rate"] = (
        age_summary["churned_customers"]
        / age_summary["total_customers"] * 100
    )

    fig_age_churn = px.bar(
        age_summary,
        x="customer_segment",
        y="churn_rate",
        color="churn_rate",
        color_continuous_scale=CHURN_SCALE,
        title="Churn Rate by Age Group",
        labels={
            "customer_segment": "Age Group",
            "churn_rate": "Churn Rate (%)"
        },
        text=age_summary["churn_rate"].map(
            lambda value: f"{value:.1f}%"
        )
    )

    show_chart(fig_age_churn)


# ============================================================
# 12. TENURE ANALYSIS
# ============================================================

st.subheader("Customer Tenure Analysis")

tenure_summary = (
    filtered_df.groupby(
        "tenure_group",
        observed=True
    )
    .agg(
        total_customers=("customer_id", "nunique"),
        churned_customers=("churn_flag", "sum")
    )
    .reset_index()
)

tenure_summary["churn_rate"] = (
    tenure_summary["churned_customers"]
    / tenure_summary["total_customers"] * 100
)

tenure_col1, tenure_col2 = st.columns(2)

with tenure_col1:
    fig_tenure = px.bar(
        tenure_summary,
        x="tenure_group",
        y="churn_rate",
        color="churn_rate",
        color_continuous_scale=CHURN_SCALE,
        title="Churn Rate by Years with Bank",
        labels={
            "tenure_group": "Tenure",
            "churn_rate": "Churn Rate (%)"
        }
    )

    fig_tenure.update_layout(
        showlegend=False
    )

    show_chart(fig_tenure)

with tenure_col2:
    fig_tenure_count = px.bar(
        tenure_summary,
        x="tenure_group",
        y="total_customers",
        color="tenure_group",
        title="Customers by Tenure Group",
        labels={
            "tenure_group": "Tenure",
            "total_customers": "Customers"
        }
    )

    fig_tenure_count.update_layout(
        showlegend=False
    )

    show_chart(fig_tenure_count)


# ============================================================
# 13. TRANSACTION ACTIVITY ANALYSIS
# ============================================================

st.subheader("Customer Transaction Activity")

activity_col1, activity_col2 = st.columns(2)

with activity_col1:
    fig_transactions = px.box(
        filtered_df,
        x="churn_status",
        y="monthly_transactions",
        color="churn_status",
        color_discrete_map=STATUS_COLOURS,
        title="Monthly Transactions by Customer Status",
        labels={
            "churn_status": "Customer Status",
            "monthly_transactions": "Monthly Transactions"
        }
    )

    show_chart(fig_transactions)

with activity_col2:
    transaction_summary = (
        filtered_df.groupby("churn_status", as_index=False)
        .agg(
            average_transactions=(
                "monthly_transactions", "mean"
            )
        )
    )

    fig_transaction_avg = px.bar(
        transaction_summary,
        x="churn_status",
        y="average_transactions",
        color="churn_status",
        color_discrete_map=STATUS_COLOURS,
        title="Average Monthly Transactions by Status",
        labels={
            "churn_status": "Customer Status",
            "average_transactions": "Average Transactions"
        }
    )

    fig_transaction_avg.update_layout(
        showlegend=False
    )

    show_chart(fig_transaction_avg)


# ============================================================
# 14. BALANCE ANALYSIS
# ============================================================

st.subheader("Customer Balance Analysis")

balance_col1, balance_col2 = st.columns(2)

with balance_col1:
    fig_balance = px.box(
        filtered_df,
        x="churn_status",
        y="monthly_balance",
        color="churn_status",
        color_discrete_map=STATUS_COLOURS,
        title="Monthly Balance by Customer Status",
        labels={
            "churn_status": "Customer Status",
            "monthly_balance": "Monthly Balance (ZAR)"
        }
    )

    show_chart(fig_balance)

with balance_col2:
    balance_summary = (
        filtered_df.groupby("churn_status", as_index=False)
        .agg(
            average_balance=("monthly_balance", "mean"),
            median_balance=("monthly_balance", "median")
        )
    )

    fig_balance_avg = px.bar(
        balance_summary,
        x="churn_status",
        y="average_balance",
        color="churn_status",
        color_discrete_map=STATUS_COLOURS,
        title="Average Balance by Customer Status",
        labels={
            "churn_status": "Customer Status",
            "average_balance": "Average Balance (ZAR)"
        }
    )

    fig_balance_avg.update_layout(
        showlegend=False
    )

    show_chart(fig_balance_avg)


# ============================================================
# 15. CREDIT SCORE ANALYSIS
# ============================================================

st.subheader("Credit Score Analysis")

credit_col1, credit_col2 = st.columns(2)

with credit_col1:
    fig_credit = px.histogram(
        filtered_df,
        x="credit_score",
        color="churn_status",
        color_discrete_map=STATUS_COLOURS,
        nbins=20,
        barmode="overlay",
        title="Credit Score Distribution by Status",
        labels={
            "credit_score": "Credit Score",
            "count": "Customers"
        }
    )

    show_chart(fig_credit)

with credit_col2:
    credit_summary = (
        filtered_df.groupby("churn_status", as_index=False)
        .agg(
            average_credit_score=("credit_score", "mean")
        )
    )

    fig_credit_avg = px.bar(
        credit_summary,
        x="churn_status",
        y="average_credit_score",
        color="churn_status",
        color_discrete_map=STATUS_COLOURS,
        title="Average Credit Score by Status",
        labels={
            "churn_status": "Customer Status",
            "average_credit_score": "Average Credit Score"
        }
    )

    fig_credit_avg.update_layout(
        showlegend=False
    )

    show_chart(fig_credit_avg)


# ============================================================
# 16. BUSINESS INSIGHTS
# ============================================================

st.divider()
st.subheader("Business Insights")

insight_col1, insight_col2 = st.columns(2)

highest_churn_province = province_summary.sort_values(
    "churn_rate", ascending=False
).iloc[0]

highest_churn_account = account_summary.sort_values(
    "churn_rate", ascending=False
).iloc[0]

highest_churn_age = age_summary.sort_values(
    "churn_rate", ascending=False
).iloc[0]

highest_churn_tenure = tenure_summary.sort_values(
    "churn_rate", ascending=False
).iloc[0]

with insight_col1:
    insight_card(
        "Province with Highest Churn Rate",
        f"<b>{html.escape(str(highest_churn_province['province']))}</b>: "
        f"{highest_churn_province['churn_rate']:.2f}% of customers in this "
        "province are churned.",
        BLUE
    )

    insight_card(
        "Account Type with Highest Churn Rate",
        f"<b>{html.escape(str(highest_churn_account['account_type']))}</b>: "
        f"{highest_churn_account['churn_rate']:.2f}% churn rate.",
        TEAL
    )

with insight_col2:
    insight_card(
        "Age Group with Highest Churn Rate",
        f"<b>{html.escape(str(highest_churn_age['customer_segment']))}</b>: "
        f"{highest_churn_age['churn_rate']:.2f}% churn rate.",
        GREEN
    )

    insight_card(
        "Tenure Group with Highest Churn Rate",
        f"<b>{html.escape(str(highest_churn_tenure['tenure_group']))}</b>: "
        f"{highest_churn_tenure['churn_rate']:.2f}% churn rate.",
        NAVY
    )

st.info(
    "These findings describe patterns in the available data. "
    "They do not establish why customers leave or prove "
    "that a particular factor causes churn."
)


# ============================================================
# 17. DATA QUALITY OVERVIEW
# ============================================================

st.divider()
st.subheader("Data Quality Overview")

quality_col1, quality_col2, quality_col3 = st.columns(3)

quality_col1.metric(
    "Records Loaded",
    f"{original_row_count:,}"
)

quality_col2.metric(
    "Duplicate IDs Removed",
    f"{duplicates_removed:,}"
)

quality_col3.metric(
    "Valid Records Remaining",
    f"{len(df):,}"
)

with st.expander("View Data Quality Details"):
    st.write("Missing values remaining after cleaning:")

    st.dataframe(
        df[required_columns]
        .isna()
        .sum()
        .rename("missing_values"),
        use_container_width=True
    )

    st.write("Customer records used for analysis:")

    st.dataframe(
        df.head(100),
        use_container_width=True,
        hide_index=True
    )


# ============================================================
# 18. CUSTOMER DATA TABLE
# ============================================================

st.divider()
st.subheader("Customer Records")

display_columns = [
    "customer_id",
    "age",
    "gender",
    "province",
    "account_type",
    "tenure_years",
    "monthly_transactions",
    "monthly_balance",
    "credit_score",
    "churn_status"
]

st.caption(
    f"Showing {len(filtered_df):,} customers matching your filters."
)

st.dataframe(
    filtered_df[display_columns].sort_values(
        "customer_id"
    ),
    use_container_width=True,
    hide_index=True
)


# ============================================================
# 19. DOWNLOAD FILTERED DATA
# ============================================================

csv_data = filtered_df[display_columns].to_csv(
    index=False
)

st.download_button(
    label="Download Filtered Customer Data",
    data=csv_data,
    file_name="filtered_banking_customer_churn.csv",
    mime="text/csv"
)


# ============================================================
# 20. FOOTER
# ============================================================

st.divider()

st.caption(
    "South African Banking Customer Churn Analysis | "
    "Built with Python, Pandas, Plotly, Streamlit and Supabase."
)