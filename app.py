import streamlit as st
import pandas as pd
from db import SessionLocal, User, Transaction
from categorize import categorize_transaction
from report import generate_reports
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime, timedelta
from prophet import Prophet
import plotly.express as px
import plotly.graph_objects as go

session = SessionLocal()
st.set_page_config(page_title="Budget Wise AI", layout="wide")

st.title(" BudgetWise AI - Expense Tracker & Forecasting")
menu = st.sidebar.radio("Navigation", ["Register", "Login", "Dashboard", "AI Forecasting"])

if "user" not in st.session_state:
    st.session_state.user = None

# ---------------- Registration ----------------
if menu == "Register":
    st.subheader("Create an Account")
    email = st.text_input("Email")
    password = st.text_input("Password", type="password")
    if st.button("Register"):
        existing = session.query(User).filter_by(email=email).first()
        if existing:
            st.error("User already exists.")
        else:
            hashed_pw = generate_password_hash(password)
            user = User(email=email, password=hashed_pw)
            session.add(user)
            session.commit()
            st.success("✅ Registration successful! Please login.")

# ---------------- Login ----------------
elif menu == "Login":
    st.subheader("User Login")
    email = st.text_input("Email")
    password = st.text_input("Password", type="password")
    if st.button("Login"):
        user = session.query(User).filter_by(email=email).first()
        if user and check_password_hash(user.password, password):
            st.session_state.user = user.email
            st.success(f"Welcome {user.email}!")
        else:
            st.error("Invalid credentials.")

# ---------------- Dashboard ----------------
elif menu == "Dashboard":
    if not st.session_state.user:
        st.warning("Please login first.")
    else:
        user = session.query(User).filter_by(email=st.session_state.user).first()
        st.success(f"Logged in as {user.email}")

        # -------- Logout --------
        if st.button("Logout"):
            st.session_state.user = None
            st.success("Logged out successfully!")
            #st.experimental_rerun()

        # -------- Manual Transaction --------
        st.subheader("➕ Add Transaction Manually")
        desc = st.text_input("Description")
        amt = st.number_input("Amount", min_value=0.0, step=0.01)
        ttype = st.selectbox("Type", ["income", "expense"])
        if st.button("Add Transaction"):
            category = categorize_transaction(desc)
            txn = Transaction(user_id=user.id, description=desc, amount=amt, type=ttype, category=category)
            session.add(txn)
            session.commit()
            st.success(f"Transaction added under '{category}' category!")

        # -------- Bulk CSV Import --------
        st.subheader("📂 Import Transactions from CSV")
        uploaded_file = st.file_uploader("Upload CSV", type=["csv"])
        if uploaded_file:
            df = pd.read_csv(uploaded_file)
            added_count = 0
            for idx, row in df.iterrows():
                desc = str(row.get("Description", ""))
                amt = float(row.get("Amount", 0))
                ttype = str(row.get("Type", "expense")).lower()
                date_str = row.get("Date")
                if date_str:
                    try:
                        date = datetime.strptime(str(date_str), "%Y-%m-%d")
                    except:
                        date = datetime.utcnow()
                else:
                    date = datetime.utcnow()
                category = categorize_transaction(desc)
                txn = Transaction(user_id=user.id, description=desc, amount=amt, type=ttype, date=date, category=category)
                session.add(txn)
                added_count += 1
            session.commit()
            st.success(f"✅ Imported {added_count} transactions successfully!")

        # -------- Recent Transactions --------
        st.subheader("🧾 Recent Transactions")
        transactions = session.query(Transaction).filter_by(user_id=user.id).order_by(Transaction.date.desc()).all()
        if transactions:
            for t in transactions[:10]:
                st.write(f"{t.date.date()} | {t.description} | ₹{t.amount} | {t.category}")
        else:
            st.info("No transactions yet.")

        # -------- Reports --------
        st.subheader("📈 Reports & Insights")
        generate_reports(transactions)

# ---------------- AI Forecasting ----------------
elif menu == "AI Forecasting":
    st.title("🤖 AI Expense Forecasting Tool")
    st.markdown("Upload your expense CSV with `Date` and `Amount` columns (optional `Category`)")

    uploaded_file = st.file_uploader("Upload Expense CSV for AI Forecasting", type=["csv"])
    if uploaded_file:
        data = pd.read_csv(uploaded_file)
        st.subheader("Expense Data Preview")
        st.dataframe(data.head())

        if "Date" not in data.columns or "Amount" not in data.columns:
            st.error("CSV must have 'Date' and 'Amount' columns!")
            st.stop()

        data["Date"] = pd.to_datetime(data["Date"])
        df = data.groupby("Date")["Amount"].sum().reset_index()
        df.columns = ["ds", "y"]

        st.sidebar.subheader("Forecast Settings")
        periods_input = st.sidebar.slider("Months to forecast:", 1, 12, 3)

        with st.spinner("Training AI Model..."):
            model = Prophet()
            model.fit(df)
            future = model.make_future_dataframe(periods=periods_input * 30)
            forecast = model.predict(future)

        st.subheader("Expense Forecast")
        fig1 = go.Figure()
        fig1.add_trace(go.Scatter(x=df['ds'], y=df['y'], name="Actual", mode='lines+markers'))
        fig1.add_trace(go.Scatter(x=forecast['ds'], y=forecast['yhat'], name="Forecast", mode='lines'))
        fig1.update_layout(title="Monthly Expense Forecast", xaxis_title="Date", yaxis_title="Amount")
        st.plotly_chart(fig1, use_container_width=True)

        if "Category" in data.columns:
            st.subheader("Spending by Category")
            cat_fig = px.pie(data, values="Amount", names="Category", title="Expense Distribution by Category")
            st.plotly_chart(cat_fig, use_container_width=True)

        st.subheader("Budget Alert System")
        monthly_budget = st.number_input("Set your monthly budget (₹)", value=50000)
        next_month_expense = forecast["yhat"].iloc[-1]

        if next_month_expense > monthly_budget:
            st.error(f"Alert: You may overshoot your budget by ₹{next_month_expense - monthly_budget:,.0f}")
        else:
            st.success(f"You're under budget by ₹{monthly_budget - next_month_expense:,.0f}")

        st.subheader("Scenario Analysis")
        rent_change = st.slider("What if my rent increases by (%)", -50, 100, 0)
        adjusted_forecast = next_month_expense * (1 + rent_change / 100)
        st.info(f"Adjusted Forecast (after {rent_change}% rent change): ₹{adjusted_forecast:,.0f}")

    else:
        st.info("Upload your expense CSV file to start forecasting.")
        st.caption("CSV format: Date, Amount, [optional: Category]")

st.markdown("---")
st.markdown(
    "**Security Note:** Your data stays local. No external upload. "
    "This AI model uses Prophet for time-series forecasting."
)
