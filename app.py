from datetime import date
from pathlib import Path

import pandas as pd
import plotly.express as px
import streamlit as st

st.set_page_config(page_title="SmartSpend", page_icon="💸", layout="wide")
st.title("💸 SmartSpend")
st.caption("Track expenses and understand your spending.")

DATA_FILE = Path(__file__).parent / "expenses.csv"

CATEGORIES = [
    "Food",
    "Transport",
    "Shopping",
    "Bills",
    "Health",
    "Entertainment",
    "Education",
    "Other",
]

KEYWORDS = {
    "Food": ["lunch", "dinner", "breakfast", "restaurant", "grocery", "coffee"],
    "Transport": ["bus", "train", "taxi", "uber", "fuel", "petrol", "metro"],
    "Shopping": ["clothes", "shoes", "mall", "amazon", "purchase"],
    "Bills": ["electricity", "water bill", "internet", "recharge", "rent"],
    "Health": ["doctor", "medicine", "hospital", "pharmacy"],
    "Entertainment": ["movie", "game", "concert", "music"],
    "Education": ["book", "course", "college", "tuition", "stationery"],
}


def categorize(description):
    description = description.lower()

    for category, words in KEYWORDS.items():
        if any(word in description for word in words):
            return category

    return "Other"


def load_expenses():
    columns = ["Date", "Description", "Category", "Amount"]

    if not DATA_FILE.exists():
        return pd.DataFrame(columns=columns)

    try:
        expenses = pd.read_csv(DATA_FILE)

        if not all(column in expenses.columns for column in columns):
            return pd.DataFrame(columns=columns)

        expenses["Date"] = pd.to_datetime(
            expenses["Date"], errors="coerce"
        ).dt.date
        expenses["Amount"] = pd.to_numeric(
            expenses["Amount"], errors="coerce"
        )
        expenses = expenses.dropna(subset=["Date", "Amount"])
        return expenses[columns]

    except (OSError, pd.errors.ParserError, UnicodeDecodeError):
        return pd.DataFrame(columns=columns)


expenses = load_expenses()

st.subheader("Add an expense")

with st.form("expense_form", clear_on_submit=True):
    col1, col2 = st.columns(2)

    with col1:
        expense_date = st.date_input("Date", value=date.today())
        description = st.text_input(
            "Description",
            placeholder="Example: bus ticket",
        )

    with col2:
        amount = st.number_input(
            "Amount (₹)",
            min_value=0.0,
            value=0.0,
            step=10.0,
        )
        category_choice = st.selectbox(
            "Category",
            ["Auto-detect"] + CATEGORIES,
        )

    submitted = st.form_submit_button("Add expense")

if submitted:
    if not description.strip():
        st.error("Please enter a description.")
    elif amount <= 0:
        st.error("Amount must be greater than zero.")
    else:
        if category_choice == "Auto-detect":
            category = categorize(description)
        else:
            category = category_choice

        new_expense = pd.DataFrame(
            [{
                "Date": expense_date,
                "Description": description.strip(),
                "Category": category,
                "Amount": float(amount),
            }]
        )

        expenses = pd.concat([expenses, new_expense], ignore_index=True)
        expenses.to_csv(DATA_FILE, index=False)

        st.success(f"Expense added under {category}.")
        st.rerun()

if expenses.empty:
    st.info("No expenses yet. Add your first expense above.")
else:
    st.divider()
    st.subheader("Spending summary")

    total = expenses["Amount"].sum()
    st.metric("Total expenses", f"₹{total:,.2f}")

    left, right = st.columns(2)

    with left:
        category_totals = (
            expenses.groupby("Category", as_index=False)["Amount"]
            .sum()
        )

        category_chart = px.pie(
            category_totals,
            names="Category",
            values="Amount",
            title="Spending by category",
        )
        st.plotly_chart(category_chart, use_container_width=True)

    with right:
        monthly_expenses = expenses.copy()
        monthly_expenses["Month"] = (
            pd.to_datetime(monthly_expenses["Date"])
            .dt.to_period("M")
            .astype(str)
        )
        monthly_totals = (
            monthly_expenses.groupby("Month", as_index=False)["Amount"]
            .sum()
            .sort_values("Month")
        )

        monthly_chart = px.bar(
            monthly_totals,
            x="Month",
            y="Amount",
            title="Monthly spending",
            labels={"Amount": "Amount (₹)"},
        )
        st.plotly_chart(monthly_chart, use_container_width=True)

    st.subheader("Expense history")
    st.dataframe(
        expenses.sort_values("Date", ascending=False),
        use_container_width=True,
        hide_index=True,
    )

    csv_data = expenses.to_csv(index=False).encode("utf-8")
    st.download_button(
        "Download expenses as CSV",
        data=csv_data,
        file_name="my_expenses.csv",
        mime="text/csv",
    )