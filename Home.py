import streamlit as st
from PIL import Image
import pandas as pd
import plotly.express as px
from database.db_connector import get_cached_data, create_connection
from login import *


# check login state
if "logged_in" not in st.session_state or not st.session_state["logged_in"]:
    login()
    st.stop()


# Set page config
st.set_page_config(
    page_title="Insurance Management System",
    page_icon="🏥",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
<style>
    .main-header {
        font-size: 36px;
        font-weight: bold;
        color: #1E3A8A;
        text-align: center;
        margin-bottom: 20px;
    }
    .sub-header {
        font-size: 24px;
        font-weight: bold;
        color: #2563EB;
        margin-top: 20px;
        margin-bottom: 10px;
    }
    .card {
        background-color: #EFF6FF;
        border-radius: 10px;
        padding: 20px;
        margin-bottom: 15px;
    }
    .success-msg {
        background-color: #DCFCE7;
        color: #166534;
        padding: 10px;
        border-radius: 5px;
        text-align: center;
    }
    .error-msg {
        background-color: #FEE2E2;
        color: #991B1B;
        padding: 10px;
        border-radius: 5px;
        text-align: center;
    }
    .metric-value {
        font-size: 24px;
        font-weight: bold;
        color: #1E3A8A;
    }
    .metric-label {
        font-size: 16px;
        color: #6B7280;
    }
    .stButton button {
        background-color: #3B82F6;
        color: white;
        border-radius: 4px;
        padding: 0.5rem 1rem;
        border: none;
    }
    .stButton button:hover {
        background-color: #2563EB;
    }
</style>
""", unsafe_allow_html=True)

# Main header
st.markdown('<div class="main-header">Insurance Management System</div>', unsafe_allow_html=True)

# Check the current user's role
role = st.session_state.get("role", "")
if role == "Insurance Agent":
    st.write("""You are logged in as an **Insurance Agent**. You have limited access to the system.
    You cannot view Payouts and Assessments.""")
elif role == "Claim Assessor":
    st.write("""You are logged in as a **Claim Assessor**. You have limited access to the system.
    You cannot view Customers Management, Insurance Types, and Contracts Management.""")
elif role == "Admin":
    st.write("""You are logged in as an **Admin**. You have full access to the system.""")

st.markdown("""
Welcome to the Insurance Management System. This application helps you manage insurance customers, 
contracts, assessments, and payouts in an efficient way.

Use the menu in the sidebar to access different sections of the application:

- **Dashboard**: Overview of key metrics and recent activities
- **Customer Management**: Add, view, and edit customer information
- **Insurance Types**: Manage different types of insurance products
- **Contract Management**: Create and manage insurance contracts
- **Claims & Assessments**: Process and track insurance claims
- **Payouts Management**: Handle payouts for approved claims
- **Reports**: Generate reports and analytics
""")