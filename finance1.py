import streamlit as st
import pandas as pd
import sqlite3
import plotly.graph_objects as go
from PIL import Image  # Import for mascot image

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

import base64

# Convert the image to base64
with open("finny.png", "rb") as image_file:
    base64_image = base64.b64encode(image_file.read()).decode()

# Display the welcome message and Finny image only if the user is not logged in
if not st.session_state.get('logged_in', False):
    st.markdown(f"""
        <h1 style='font-size: 2.5em; line-height: 1.2;'>
            <small>Welcome to</small><br>
            <span style='color: #0078D7;'>Finny - Your Personal Finance Tracker</span>
        </h1>
        <div style="text-align: center;">
            <img src="data:image/png;base64,{base64_image}" alt="Finny" style="width: 300px;">
            <p>Hi, I'm Finny! 🐟</p>
        </div>
    """, unsafe_allow_html=True)


# Initialize session state
if 'logged_in' not in st.session_state:
    st.session_state['logged_in'] = False

if 'username' not in st.session_state:
    st.session_state['username'] = ""

if 'data' not in st.session_state:
    st.session_state['data'] = pd.DataFrame()

if 'budget' not in st.session_state:
    st.session_state['budget'] = 0.0

# Login and Registration
if not st.session_state['logged_in']:
    st.sidebar.title("Login or Register")
    username = st.sidebar.text_input("Username")
    passkey = st.sidebar.text_input("4-digit Passkey", type="password")

    if st.sidebar.button("Login"):
        user_query = c.execute("SELECT * FROM users WHERE username = ? AND passkey = ?", (username, passkey)).fetchone()
        if user_query:
            st.session_state['logged_in'] = True
            st.session_state['username'] = username
            st.success("Login successful!")
            st.session_state['data'] = pd.read_sql_query(
                "SELECT * FROM transactions WHERE username = ?", 
                conn, params=(username,))
            budget_result = c.execute("SELECT budget FROM budget WHERE username = ?", (username,)).fetchone()
            st.session_state['budget'] = budget_result[0] if budget_result else 0.0
        else:
            st.sidebar.error("Invalid username or passkey.")

    if st.sidebar.button("Register"):
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

    
    # Convert the image to base64 for HTML embedding
    import base64
    with open("finny.png", "rb") as image_file:
        base64_image = base64.b64encode(image_file.read()).decode()

    # Use HTML to display the image in the sidebar
    st.sidebar.markdown(f"""
        <div style="text-align: center; margin-top: 50px;">
            <img src="data:image/png;base64,{base64_image}" alt="Finny" style="width: 300px; border-radius: 50%;">
            <p style="font-size: 1em; font-style: italic;">Hi, I'm Finny! Here to help you manage your finances.  lets goooo!!! </p>
        </div>
    """, unsafe_allow_html=True)
    
    # Navigation Tabs
    tab1, tab2, tab3, tab4 = st.tabs(["Dashboard", "Add Transaction", "Bill Reminders", "Transaction History"])

    # Dashboard Tab
    with tab1:
        st.header("Dashboard")
    
        # Total Income and Expenses
        total_income = st.session_state['data'][st.session_state['data']['Type'] == 'Income']['Amount'].sum()
        total_expenses = st.session_state['data'][st.session_state['data']['Type'] == 'Expense']['Amount'].sum()
    
        # Bar Chart: Budget Overview
        categories = ['Net Income', 'Remaining Budget', 'Expenses']
        values = [total_income, st.session_state['budget'] - total_expenses, total_expenses]
        colors = ['#A8E6CF', '#FFEB3B', '#FF7043']
    
        fig_bar = go.Figure(data=[go.Bar(
            x=values,
            y=categories,
            orientation='h',
            marker=dict(color=colors, line=dict(color='black', width=0.1)),
            width=0.4
        )])
        fig_bar.update_layout(
            title="Budget & Expenses Overview",
            xaxis_title="Amount (₹)",
            yaxis_title="Categories",
            template="plotly_dark",
            plot_bgcolor='rgba(0, 0, 0, 0)',
            paper_bgcolor='rgba(0, 0, 0, 0)',
            height=300,
            width=600
        )
        st.plotly_chart(fig_bar)
    
        st.header("Bill Reminders")
        bill_reminders = pd.read_sql_query("SELECT * FROM bill_reminders WHERE username = ?", conn, params=(st.session_state['username'],))
        if not bill_reminders.empty:
            st.write(bill_reminders)
        else:
            st.info("No upcoming bills. Add some to track.")
    
    
        # Pie Chart: Income and Expense Distribution
        income_expense_categories = st.session_state['data'][['Category', 'Type', 'Amount']]
        grouped = income_expense_categories.groupby(['Type', 'Category']).sum().reset_index()
        for chart_type in ['Income', 'Expense']:
            filtered = grouped[grouped['Type'] == chart_type]
            fig_pie = go.Figure(data=[go.Pie(labels=filtered['Category'], values=filtered['Amount'], hole=0.4)])
            fig_pie.update_layout(
                title=f"{chart_type} Distribution by Category",
                template="plotly_dark",
                plot_bgcolor='rgba(0, 0, 0, 0)',
                paper_bgcolor='rgba(0, 0, 0, 0)'
            )
            st.plotly_chart(fig_pie)
    
        # Line Chart: Cumulative Spending Trend Over Time
        spending_trend = st.session_state['data'][st.session_state['data']['Type'] == 'Expense']
        spending_trend['Date'] = pd.to_datetime(spending_trend['Date'])
        spending_trend = spending_trend.sort_values('Date')
        spending_trend['Cumulative Spending'] = spending_trend['Amount'].cumsum()
        fig_line = go.Figure(data=go.Scatter(x=spending_trend['Date'], y=spending_trend['Cumulative Spending'], mode='lines+markers'))
        fig_line.update_layout(
            title="Cumulative Spending Over Time",
            xaxis_title="Date",
            yaxis_title="Cumulative Spending (₹)",
            template="plotly_dark",
            plot_bgcolor='rgba(0, 0, 0, 0)',
            paper_bgcolor='rgba(0, 0, 0, 0)'
        )
        st.plotly_chart(fig_line)
    
       
    
        # Alert if over budget
        if total_expenses > st.session_state['budget']:
            st.warning(f"Warning: Expenses exceed the allocated budget by ₹{total_expenses - st.session_state['budget']:.2f}", icon="⚠️")

    # Add Transaction Tab
    with tab2:
        st.header("Add a Transaction")
        
        # Add Transaction Inputs
        date = st.date_input("Date", key="transaction_date")
        category = st.text_input("Category (e.g., Food, Rent)", key="transaction_category")
        type_option = st.radio("Type", ["Income", "Expense"], key="transaction_type")
        amount = st.number_input("Amount", min_value=0.0, step=0.01, key="transaction_amount")
    
        if st.button("Add Transaction", key="add_transaction_btn"):
            if not category or amount <= 0:
                st.error("Please provide a valid category and amount.")
            else:
                c.execute("INSERT INTO transactions (username, Date, Category, Type, Amount) VALUES (?, ?, ?, ?, ?)", 
                          (st.session_state['username'], date, category, type_option, amount))
                conn.commit()
                st.session_state['data'] = pd.read_sql_query(
                    "SELECT * FROM transactions WHERE username = ?", 
                    conn, params=(st.session_state['username'],))
                st.success("Transaction added!")
    
        st.markdown("---")  # Separator line
    
        # Set Budget Section
        st.header("Set Budget")
        current_budget = st.session_state.get('budget', 0.0)
        st.write(f"Current Budget: ₹{current_budget:.2f}")
        
        new_budget = st.number_input("Set a new budget", min_value=0.0, step=0.01, key="set_budget")
        
        if st.button("Update Budget", key="update_budget_btn"):
            if new_budget <= 0:
                st.error("Please provide a valid budget amount.")
            else:
                st.session_state['budget'] = new_budget
                st.success(f"Budget updated to ₹{new_budget:.2f}!")


    # Bill Reminders Tab
    with tab3:
        st.header("Bill Reminders")
    
        # Fetch existing bill reminders from the database
        bill_reminders = pd.read_sql_query(
            "SELECT id, bill_name, amount, due_date, frequency FROM bill_reminders WHERE username = ?",
            conn,
            params=(st.session_state['username'],)
        )
    
        # Display reminders or info if no reminders exist
        if not bill_reminders.empty:
            st.write("Upcoming Bills:")
            # Add a "Delete" button in each row
            for i, row in bill_reminders.iterrows():
                col1, col2, col3, col4, col5, col6 = st.columns(6)
                col1.write(row['bill_name'])
                col2.write(f"₹{row['amount']:.2f}")
                col3.write(row['due_date'])
                col4.write(row['frequency'])
                delete_button = col5.button("Delete", key=f"delete_{row['id']}_{i}")  # Ensures unique key
                
                # Handle delete button click
                if delete_button:
                    c.execute("DELETE FROM bill_reminders WHERE id = ?", (row['id'],))
                    conn.commit()
                    st.success(f"Deleted reminder for '{row['bill_name']}'!")
                    st.experimental_rerun()  # Refresh the page after deletion
        else:
            st.info("No upcoming bills. Add some to track.")
    
        # Input fields for adding new bill reminders
        bill_name = st.text_input("Bill Name (e.g., Electricity, Rent)", key="bill_name")
        bill_amount = st.number_input("Amount", min_value=0.0, step=0.01, key="bill_amount")
        due_date = st.date_input("Due Date", key="bill_due_date")
        frequency = st.selectbox("Frequency", ["Monthly", "Weekly", "Yearly"], key="bill_frequency")
    
        # Add button to create new reminders
        if st.button("Add Bill Reminder", key="add_bill_btn"):
            if not bill_name or bill_amount <= 0:
                st.error("Please provide valid bill name and amount.")
            else:
                c.execute(
                    "INSERT INTO bill_reminders (username, bill_name, amount, due_date, frequency) VALUES (?, ?, ?, ?, ?)",
                    (st.session_state['username'], bill_name, bill_amount, due_date, frequency)
                )
                conn.commit()
                st.success("Bill Reminder Added!")
                st.experimental_rerun()  # Refresh the page after adding a new bill



    # Transaction History Tab
    with tab4:
        st.header("Transaction History")
        transactions = st.session_state['data']
        if not transactions.empty:
            for i, row in transactions.iterrows():
                col1, col2, col3, col4, col5, col6 = st.columns(6)
                col1.write(row['Date'])
                col2.write(row['Category'])
                col3.write(row['Type'])
                col4.write(f"₹{row['Amount']:.2f}")
                if col5.button("Delete", key=f"delete_{row['id']}"):
                    c.execute("DELETE FROM transactions WHERE id = ?", (row['id'],))
                    conn.commit()
                    st.session_state['data'] = pd.read_sql_query(
                        "SELECT * FROM transactions WHERE username = ?", 
                        conn, params=(st.session_state['username'],))
                    st.success(f"Transaction {row['id']} deleted.")
        else:
            st.info("No transactions recorded yet.")
