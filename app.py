import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px

st.set_page_config(
    page_title="Vadības panelis — Pārdošana, Atgriezumi un Sūdzības",
    layout="wide"
)

@st.cache_data
def load_data(path="analysis_ready_dataset.csv"):
    df = pd.read_csv(path)
    df["order_date"] = pd.to_datetime(df["order_date"], errors="coerce")
    df["order_month"] = df["order_date"].dt.to_period("M").astype(str)
    return df

df = load_data()

st.sidebar.header("🔎 Filtri")

product_options = sorted(df["Product_Category"].dropna().unique().tolist())
selected_products = st.sidebar.multiselect(
    "Produktu kategorija",
    options=product_options,
    default=product_options
)

min_date = df["order_date"].min()
max_date = df["order_date"].max()

date_range = st.sidebar.date_input(
    "Laika periods",
    value=(min_date, max_date),
    min_value=min_date,
    max_value=max_date
)

df_filt = df[
    (df["Product_Category"].isin(selected_products)) &
    (df["order_date"] >= pd.to_datetime(date_range[0])) &
    (df["order_date"] <= pd.to_datetime(date_range[1]))
]

total_revenue = df_filt["paid_revenue"].sum()
total_refund = df_filt["refund_total_processed"].sum()
refund_rate = (total_refund / total_revenue * 100) if total_revenue > 0 else 0
complaint_count = int(df_filt["has_any_ticket"].sum())

st.title("📊 Pārdošanas, Atgriezumu un Sūdzību pārskats")

c1, c2, c3 = st.columns(3)
c1.metric("💰 Kopējie ieņēmumi", f"{total_revenue:,.0f} €")
c2.metric("↩️ Atgriezumi", f"{total_refund:,.0f} €", f"{refund_rate:.1f}%")
c3.metric("📩 Pasūtījumi ar sūdzībām", complaint_count)

st.markdown("---")

time_agg = (
    df_filt.groupby("order_month")
           .agg(
               orders=("Transaction_ID", "count"),
               complaints=("has_any_ticket", "sum")
           )
           .reset_index()
)

time_agg["complaints_per_100_orders"] = (
    time_agg["complaints"] / time_agg["orders"] * 100
)

fig_time = px.line(
    time_agg,
    x="order_month",
    y="complaints_per_100_orders",
    markers=True,
    labels={
        "order_month": "Mēnesis",
        "complaints_per_100_orders": "Sūdzības uz 100 pasūtījumiem"
    }
)

st.plotly_chart(fig_time, use_container_width=True)

cat_agg = (
    df_filt.groupby("Product_Category")
           .agg(
               orders=("Transaction_ID", "count"),
               complaints=("has_any_ticket", "sum")
           )
           .reset_index()
)

cat_agg["complaints_per_100_orders"] = (
    cat_agg["complaints"] / cat_agg["orders"] * 100
)

fig_cat = px.bar(
    cat_agg.sort_values("complaints_per_100_orders", ascending=False),
    x="Product_Category",
    y="complaints_per_100_orders",
    labels={
        "Product_Category": "Produktu kategorija",
        "complaints_per_100_orders": "Sūdzības uz 100 pasūtījumiem"
    }
)

st.plotly_chart(fig_cat, use_container_width=True)

top_problem_cases = (
    df_filt.groupby("Product_Name")
           .agg(
               orders=("Transaction_ID", "count"),
               complaints=("has_any_ticket", "sum"),
               refunds=("refund_total_processed", "sum")
           )
           .reset_index()
)

top_problem_cases["complaint_rate_%"] = (
    top_problem_cases["complaints"] /
    top_problem_cases["orders"] * 100
)

top_problem_cases = top_problem_cases.sort_values(
    ["refunds", "complaint_rate_%"],
    ascending=False
).head(10)

st.subheader("🚨 Top problemātiskie produkti")
st.dataframe(top_problem_cases, use_container_width=True)
