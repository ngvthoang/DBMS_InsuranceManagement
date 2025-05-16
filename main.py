import streamlit as st
import os
from dotenv import load_dotenv
from PIL import Image
from st_aggrid import AgGrid

# Set page config
st.set_page_config(
    page_title="Insurance Management System",
    page_icon="🏥",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Load environment variables
load_dotenv() 

# Import modules
from models.login import login
from models.dashboard import display_dashboard
from models.customer import display_customer_management
from models.insurance_type import display_insurance_types
from models.contract import display_contract_management
from models.assessment import display_claims_management
from models.payout import display_payouts_management
from models.report import display_reports

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
</style>
""", unsafe_allow_html=True)

# Sidebar navigation
st.sidebar.markdown("# Insurance Management System 🏥")
st.sidebar.markdown("---")

# Navigation options
nav_option = st.sidebar.radio(
    "Navigate to:",
    [
        "Dashboard",
        "Customer Management",
        "Insurance Types",
        "Contract Management",
        "Claims & Assessments",
        "Payouts Management",
        "Reports"
    ]
)

# Main header
st.markdown('<div class="main-header">Insurance Management System</div>', unsafe_allow_html=True)

# Handle navigation with role-based restrictions
if nav_option == "Dashboard":
    display_dashboard()
elif nav_option == "Customer Management":
    if st.session_state.get("role") == "Claim Assessor":
        st.error("Access restricted: You cannot view Customer Management.")
    else:
        display_customer_management()
elif nav_option == "Insurance Types":
    if st.session_state.get("role") == "Claim Assessor":
        st.error("Access restricted: You cannot view Insurance Types.")
    else:
        display_insurance_types()
elif nav_option == "Contract Management":
    if st.session_state.get("role") == "Claim Assessor":
        st.error("Access restricted: You cannot view Contract Management.")
    else:
        display_contract_management()
elif nav_option == "Claims & Assessments":
    if st.session_state.get("role") == "Insurance Agent":
        st.error("Access restricted: You cannot view Claims and Assessments.")
    else:
        display_claims_management()
elif nav_option == "Payouts Management":
    if st.session_state.get("role") == "Insurance Agent":
        st.error("Access restricted: You cannot view Payouts Management.")
    else:
        display_payouts_management()
elif nav_option == "Reports":
    display_reports()