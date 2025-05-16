import streamlit as st
from PIL import Image
import pandas as pd
import plotly.express as px
from database.db_connector import get_cached_data, create_connection

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

# Check database connection
conn = create_connection()
if not conn:
    st.error("Could not connect to the database. Please check your connection settings.")
    st.info("Use the Database Configuration settings in the sidebar of the Dashboard page to update your connection details.")
else:
    conn.close()
    st.success("Connected to the database successfully!")

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

# # Display key metrics
# st.markdown("## 📊 Key Metrics")

# # Get dashboard metrics
# @st.cache_data(ttl=300)
# def get_dashboard_metrics():
#     """Get key metrics for the dashboard"""
#     metrics = {}
    
#     # Total Customers
#     customer_count = get_cached_data("SELECT COUNT(*) AS count FROM Customers")
#     metrics['customer_count'] = customer_count[0]['count'] if customer_count else 0
    
#     # Active Contracts
#     contract_count = get_cached_data("SELECT COUNT(*) AS count FROM InsuranceContracts WHERE Status = 'Active'")
#     metrics['contract_count'] = contract_count[0]['count'] if contract_count else 0
    
#     # Pending Claims
#     pending_claims = get_cached_data("SELECT COUNT(*) AS count FROM Assessments WHERE Result = 'Pending'")
#     metrics['pending_claims'] = pending_claims[0]['count'] if pending_claims else 0
    
#     # Total Payouts
#     total_payouts = get_cached_data("SELECT SUM(Amount) AS total FROM Payouts WHERE Status = 'Approved'")
#     metrics['total_payouts'] = total_payouts[0]['total'] if total_payouts and total_payouts[0]['total'] else 0
    
#     return metrics

# metrics = get_dashboard_metrics()

# # Create metric cards
# col1, col2, col3, col4 = st.columns(4)

# with col1:
#     st.markdown(f"""
#     <div class="card">
#         <div class="metric-label">Total Customers</div>
#         <div class="metric-value">{metrics['customer_count']}</div>
#     </div>
#     """, unsafe_allow_html=True)

# with col2:
#     st.markdown(f"""
#     <div class="card">
#         <div class="metric-label">Active Contracts</div>
#         <div class="metric-value">{metrics['contract_count']}</div>
#     </div>
#     """, unsafe_allow_html=True)

# with col3:
#     st.markdown(f"""
#     <div class="card">
#         <div class="metric-label">Pending Claims</div>
#         <div class="metric-value">{metrics['pending_claims']}</div>
#     </div>
#     """, unsafe_allow_html=True)

# with col4:
#     st.markdown(f"""
#     <div class="card">
#         <div class="metric-label">Total Payouts</div>
#         <div class="metric-value">${metrics['total_payouts']:,.2f}</div>
#     </div>
#     """, unsafe_allow_html=True)

# # Refresh button for metrics
# if st.button("🔄 Refresh Metrics"):
#     get_dashboard_metrics.clear()
#     st.experimental_rerun()
