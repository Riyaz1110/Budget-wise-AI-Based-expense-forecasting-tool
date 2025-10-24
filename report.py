import pandas as pd
import streamlit as st

def generate_reports(transactions):
    if not transactions:
        st.warning("No transactions to display.")
        return

    df = pd.DataFrame([{
        "Date": t.date,
        "Description": t.description,
        "Amount": t.amount,
        "Type": t.type,
        "Category": t.category
    } for t in transactions])

    st.subheader("📊 Spending by Category")
    expense_df = df[df["Type"] == "expense"]
    if not expense_df.empty:
        cat_summary = expense_df.groupby("Category")["Amount"].sum()
        st.bar_chart(cat_summary)
    else:
        st.info("No expense data yet.")

    st.subheader("🗓 Monthly Summary")
    df["Month"] = pd.to_datetime(df["Date"]).dt.to_period("M")
    monthly_summary = df.groupby(["Month", "Type"])["Amount"].sum().unstack().fillna(0)
    st.line_chart(monthly_summary)

    st.subheader("💰 Income vs Expense")
    st.dataframe(monthly_summary)
