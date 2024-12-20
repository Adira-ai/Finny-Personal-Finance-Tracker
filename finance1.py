import streamlit as st
import pandas as pd
import sqlite3
import plotly.graph_objects as go
from PIL import Image
import base64

# Load the mascot image
mascot_path = "finny.png"
mascot_image = Image.open(mascot_path)

# Database Connection
conn = sqlite3.connect("finance_data.db")
c = conn.cursor()

# Create Tables if Not Exists
c.execute('''CREATE TABLE IF NOT EXISTS transactions (
             id INTEGER PRIMARY KEY, 
             username TEXT NOT NULL, 
             Date TEXT, 
             Category TEXT, 
             Type TEXT, 
             Amount REAL,
             FOREIGN KEY (username) REFERENCES users (username))''')

c.execute('''CREATE TABLE IF NOT EXISTS users (
             username TEXT PRIMARY KEY, 
             passkey TEXT)''')

c.execute('''CREATE TABLE IF NOT EXISTS budget (
             username TEXT PRIMARY KEY, 
             budget REAL)''')

c.execute('''CREATE TABLE IF NOT EXISTS bill_reminders (
             id INTEGER PRIMARY KEY,
             username TEXT NOT NULL,
             bill_name TEXT,
             amount REAL,
             due_date TEXT,
             frequency TEXT,
             FOREIGN KEY (username) REFERENCES users (username))''')

conn.commit()

# Initialize session state
if 'logged_in' not in st.session_state:
    st.session_state['logged_in'] = False
if 'username' not in st.session_state:
    st.session_state['username'] = ""
if 'data' not in st.session_state:
    st.session_state['data'] = pd.DataFrame()
if 'budget' not in st.session_state:
    st.session_state['budget'] = 0.0

# Display Welcome Message
if not st.session_state['logged_in']:
    with open(mascot_path, "rb") as image_file:
        base64_image = base64.b64encode(image_file.read()).decode()
    st.markdown(f"""
        <h1 style='font-size: 2.5em;'>Welcome to <span style='color: #0078D7;'>Finny</span></h1>
        <div style="text-align: center;">
            <img src="data:image/png;base64,{base64_image}" alt="Finny" style="width: 300px;">
            <p>Hi, I'm Finny! 🐟</p>
        </div>
    """, unsafe_allow_html=True)

# Login and Registration
if not st.session_state['logged_in']:
    st.sidebar.title("Login or Register")
    username = st.sidebar.text_input("Username")
    passkey = st.sidebar.text_input("4-digit Passkey", type="password")

    if st.sidebar.button("Login", key="login_btn"):
        user_query = c.execute("SELECT * FROM users WHERE username = ? AND passkey = ?", (username, passkey)).fetchone()
        if user_query:
            st.session_state['logged_in'] = True
            st.session_state['username'] = username
            st.session_state['data'] = pd.read_sql_query(
                "SELECT * FROM transactions WHERE username = ?", conn, params=(username,))
            budget_result = c.execute("SELECT budget FROM budget WHERE username = ?", (username,)).fetchone()
            st.session_state['budget'] = budget_result[0] if budget_result else 0.0
            st.success("Login successful!")
        else:
            st.sidebar.error("Invalid username or passkey.")
        st.experimental_rerun()

    if st.sidebar.button("Register", key="register_btn"):
        user_query = c.execute("SELECT * FROM users WHERE username = ?", (username,)).fetchone()
        if user_query:
            st.sidebar.error("Username already exists.")
        elif len(passkey) != 4 or not passkey.isdigit():
            st.sidebar.error("Passkey must be a 4-digit number.")
        else:
            c.execute("INSERT INTO users (username, passkey) VALUES (?, ?)", (username, passkey))
            conn.commit()
            st.sidebar.success("Registration successful! You can now log in.")

# Logged-In Features
if st.session_state['logged_in']:
    st.sidebar.title(f"Welcome, {st.session_state['username']}!")
    if st.sidebar.button("Logout", key="logout_btn"):
        st.session_state['logged_in'] = False
        st.session_state['username'] = ""
        st.session_state['data'] = pd.DataFrame()
        st.session_state['budget'] = 0.0
        st.success("Logged out successfully!")
        st.experimental_rerun()

    # Navigation Tabs
    tab1, tab2, tab3, tab4 = st.tabs(["Dashboard", "Add Transaction", "Bill Reminders", "Transaction History"])

    # Add Transaction Tab
    with tab2:
        st.header("Add a Transaction")
        date = st.date_input("Date", key="transaction_date")
        category = st.text_input("Category", key="transaction_category")
        type_option = st.radio("Type", ["Income", "Expense"], key="transaction_type")
        amount = st.number_input("Amount", min_value=0.0, step=0.01, key="transaction_amount")
        
        if st.button("Add Transaction", key="add_transaction_btn"):
            if category and amount > 0:
                c.execute("INSERT INTO transactions (username, Date, Category, Type, Amount) VALUES (?, ?, ?, ?, ?)",
                          (st.session_state['username'], date, category, type_option, amount))
                conn.commit()
                st.session_state['data'] = pd.read_sql_query(
                    "SELECT * FROM transactions WHERE username = ?", conn, params=(st.session_state['username'],))
                st.success("Transaction added!")
                st.experimental_rerun()
            else:
                st.error("Please provide valid inputs.")

    # Bill Reminders Tab
    with tab3:
        st.header("Bill Reminders")
        bill_name = st.text_input("Bill Name", key="bill_name")
        bill_amount = st.number_input("Amount", min_value=0.0, step=0.01, key="bill_amount")
        due_date = st.date_input("Due Date", key="bill_due_date")
        frequency = st.selectbox("Frequency", ["Monthly", "Weekly", "Yearly"], key="bill_frequency")
        
        if st.button("Add Bill Reminder", key="add_bill_btn"):
            if bill_name and bill_amount > 0:
                c.execute(
                    "INSERT INTO bill_reminders (username, bill_name, amount, due_date, frequency) VALUES (?, ?, ?, ?, ?)",
                    (st.session_state['username'], bill_name, bill_amount, due_date, frequency))
                conn.commit()
                st.success("Bill Reminder Added!")
                st.experimental_rerun()
            else:
                st.error("Please provide valid inputs.")
