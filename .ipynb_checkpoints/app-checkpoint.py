import streamlit as st
import pandas as pd
import plotly.express as px
from supabase import create_client

# ============================================================
# 1. PAGE CONFIGURATION
# ============================================================

st.set_page_config(
    page_title="South African Banking Customer Churn",
    page_icon="🏦",
    layout="wide"
)

st.title("🏦 South African Banking Customer Churn Analysis")

st.markdown(
    """
    An interactive banking analytics dashboard exploring
    customer retention, churn patterns, account activity,
    customer balances and credit scores.
    """
)

st.divider()


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

st.sidebar.header("🔎 Customer Filters")

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

st.subheader("📊 Customer Retention Overview")

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
        hole=0.45,
        title="Active vs Churned Customers"
    )

    st.plotly_chart(
        fig_status,
        use_container_width=True
    )

with status_col2:
    fig_status_bar = px.bar(
        status_summary,
        x="churn_status",
        y="customers",
        color="churn_status",
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

    st.plotly_chart(
        fig_status_bar,
        use_container_width=True
    )


# ============================================================
# 9. CHURN BY PROVINCE
# ============================================================

st.subheader("📍 Customer Churn by Province")

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

st.plotly_chart(
    fig_province,
    use_container_width=True
)

with st.expander("View Province Summary Table"):
    st.dataframe(
        province_summary.round(2),
        use_container_width=True,
        hide_index=True
    )


# ============================================================
# 10. CHURN BY ACCOUNT TYPE
# ============================================================

st.subheader("🏦 Account Type Analysis")

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
        color="account_type",
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

    st.plotly_chart(
        fig_account_churn,
        use_container_width=True
    )

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

    st.plotly_chart(
        fig_account_count,
        use_container_width=True
    )


# ============================================================
# 11. CUSTOMER AGE ANALYSIS
# ============================================================

st.subheader("👥 Customer Age Analysis")

age_col1, age_col2 = st.columns(2)

with age_col1:
    fig_age = px.histogram(
        filtered_df,
        x="age",
        color="churn_status",
        nbins=20,
        barmode="overlay",
        title="Age Distribution by Customer Status",
        labels={
            "age": "Customer Age",
            "count": "Customers"
        }
    )

    st.plotly_chart(
        fig_age,
        use_container_width=True
    )

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
        title="Churn Rate by Age Group",
        labels={
            "customer_segment": "Age Group",
            "churn_rate": "Churn Rate (%)"
        },
        text=age_summary["churn_rate"].map(
            lambda value: f"{value:.1f}%"
        )
    )

    st.plotly_chart(
        fig_age_churn,
        use_container_width=True
    )


# ============================================================
# 12. TENURE ANALYSIS
# ============================================================

st.subheader("⏳ Customer Tenure Analysis")

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
        color="tenure_group",
        title="Churn Rate by Years with Bank",
        labels={
            "tenure_group": "Tenure",
            "churn_rate": "Churn Rate (%)"
        }
    )

    fig_tenure.update_layout(
        showlegend=False
    )

    st.plotly_chart(
        fig_tenure,
        use_container_width=True
    )

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

    st.plotly_chart(
        fig_tenure_count,
        use_container_width=True
    )


# ============================================================
# 13. TRANSACTION ACTIVITY ANALYSIS
# ============================================================

st.subheader("💳 Customer Transaction Activity")

activity_col1, activity_col2 = st.columns(2)

with activity_col1:
    fig_transactions = px.box(
        filtered_df,
        x="churn_status",
        y="monthly_transactions",
        color="churn_status",
        title="Monthly Transactions by Customer Status",
        labels={
            "churn_status": "Customer Status",
            "monthly_transactions": "Monthly Transactions"
        }
    )

    st.plotly_chart(
        fig_transactions,
        use_container_width=True
    )

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
        title="Average Monthly Transactions by Status",
        labels={
            "churn_status": "Customer Status",
            "average_transactions": "Average Transactions"
        }
    )

    fig_transaction_avg.update_layout(
        showlegend=False
    )

    st.plotly_chart(
        fig_transaction_avg,
        use_container_width=True
    )


# ============================================================
# 14. BALANCE ANALYSIS
# ============================================================

st.subheader("💰 Customer Balance Analysis")

balance_col1, balance_col2 = st.columns(2)

with balance_col1:
    fig_balance = px.box(
        filtered_df,
        x="churn_status",
        y="monthly_balance",
        color="churn_status",
        title="Monthly Balance by Customer Status",
        labels={
            "churn_status": "Customer Status",
            "monthly_balance": "Monthly Balance (ZAR)"
        }
    )

    st.plotly_chart(
        fig_balance,
        use_container_width=True
    )

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
        title="Average Balance by Customer Status",
        labels={
            "churn_status": "Customer Status",
            "average_balance": "Average Balance (ZAR)"
        }
    )

    fig_balance_avg.update_layout(
        showlegend=False
    )

    st.plotly_chart(
        fig_balance_avg,
        use_container_width=True
    )


# ============================================================
# 15. CREDIT SCORE ANALYSIS
# ============================================================

st.subheader("📈 Credit Score Analysis")

credit_col1, credit_col2 = st.columns(2)

with credit_col1:
    fig_credit = px.histogram(
        filtered_df,
        x="credit_score",
        color="churn_status",
        nbins=20,
        barmode="overlay",
        title="Credit Score Distribution by Status",
        labels={
            "credit_score": "Credit Score",
            "count": "Customers"
        }
    )

    st.plotly_chart(
        fig_credit,
        use_container_width=True
    )

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
        title="Average Credit Score by Status",
        labels={
            "churn_status": "Customer Status",
            "average_credit_score": "Average Credit Score"
        }
    )

    fig_credit_avg.update_layout(
        showlegend=False
    )

    st.plotly_chart(
        fig_credit_avg,
        use_container_width=True
    )


# ============================================================
# 16. BUSINESS INSIGHTS
# ============================================================

st.divider()
st.subheader("💡 Business Insights")

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
    st.markdown("**Province with Highest Churn Rate**")
    st.write(
        f"{highest_churn_province['province']}: "
        f"{highest_churn_province['churn_rate']:.2f}% "
        "of customers in this province are churned."
    )

    st.markdown("**Account Type with Highest Churn Rate**")
    st.write(
        f"{highest_churn_account['account_type']}: "
        f"{highest_churn_account['churn_rate']:.2f}% "
        "churn rate."
    )

with insight_col2:
    st.markdown("**Age Group with Highest Churn Rate**")
    st.write(
        f"{highest_churn_age['customer_segment']}: "
        f"{highest_churn_age['churn_rate']:.2f}% "
        "churn rate."
    )

    st.markdown("**Tenure Group with Highest Churn Rate**")
    st.write(
        f"{highest_churn_tenure['tenure_group']}: "
        f"{highest_churn_tenure['churn_rate']:.2f}% "
        "churn rate."
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
st.subheader("🧹 Data Quality Overview")

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
st.subheader("📋 Customer Records")

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
    label="⬇️ Download Filtered Customer Data",
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