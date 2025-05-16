import streamlit as st
import pandas as pd
import plotly.express as px
import io
from database.db_connector import create_connection
from models.report import (
    get_contracts_by_type,
    get_contracts_by_status,
    get_contracts_by_month,
    get_active_contracts_summary,
    get_claims_by_status,
    get_claims_by_type,
    get_claims_by_month,
    get_claim_amounts_by_type,
    get_claims_metrics,
    get_payouts_by_type,
    get_payouts_by_month,
    get_payouts_by_status,
    get_payout_metrics,
    get_top_customers_by_contracts,
    get_top_customers_by_payout,
    get_top_customers_by_claims,
    get_customer_overview
)

# Check the curent user role if they are allowed to access this page
if "logged_in" not in st.session_state or not st.session_state["logged_in"]:
    st.error("Access denied. Please log in to view this page.")
    st.stop()

st.set_page_config(page_title="Reports & Analytics", page_icon="📊", layout="wide")

# Reports page
st.markdown('# Reports & Analytics')
st.markdown('Generate reports and data visualizations')
st.markdown('---')

# Check database connection
conn = create_connection()
if not conn:
    st.error("Could not connect to the database. Please check your connection settings.")
    st.stop()
else:
    conn.close()

# Create report type selection
report_type = st.selectbox(
    "Select Report Type",
    [
        "Contracts Summary", 
        "Claims Analysis", 
        "Payout Summary", 
        "Customer Activity"
    ]
)

# Refresh button
if st.button("🔄 Refresh Data"):
    st.cache_data.clear()
    st.experimental_rerun()

# Add a download option for each report
download_format = st.radio("Download Format", ["CSV", "Excel"], horizontal=True)

# Contracts Summary Report
if report_type == "Contracts Summary":
    st.subheader("Contracts Summary Report")
    
    # Display metrics
    active_summary = get_active_contracts_summary()
    if active_summary and active_summary[0]['TotalActive'] is not None:
        col1, col2, col3 = st.columns(3)
        with col1:
            # Convert Decimal to int
            total_active = int(active_summary[0]['TotalActive'])
            st.metric("Total Active Contracts", total_active)
        with col2:
            # Convert Decimal to int
            expiring = int(active_summary[0]['ExpiringIn30Days'])
            st.metric("Expiring in 30 Days", expiring)
        with col3:
            earliest = active_summary[0]['EarliestExpiration']
            latest = active_summary[0]['LatestExpiration']
            st.metric("Earliest Expiration", earliest.strftime('%Y-%m-%d') if earliest else "N/A")
            st.metric("Latest Expiration", latest.strftime('%Y-%m-%d') if latest else "N/A")
    
    # Contracts by insurance type
    contracts_by_type = get_contracts_by_type()
    if contracts_by_type:
        st.subheader("Contracts by Insurance Type")
        df_type = pd.DataFrame(contracts_by_type)
        
        # Create a bar chart
        fig1 = px.bar(
            df_type, 
            x='InsuranceName', 
            y='Count', 
            title='Contract Distribution by Insurance Type',
            color='InsuranceName',
            color_discrete_sequence=px.colors.qualitative.Plotly
        )
        fig1.update_layout(xaxis_title='Insurance Type', yaxis_title='Number of Contracts')
        st.plotly_chart(fig1, use_container_width=True)
        
        # Allow download
        if download_format == "CSV":
            csv = df_type.to_csv(index=False)
            st.download_button(
                f"Download Contracts by Type (CSV)",
                data=csv,
                file_name="contracts_by_type.csv",
                mime="text/csv"
            )
        else:
            buffer = io.BytesIO()
            with pd.ExcelWriter(buffer, engine='xlsxwriter') as writer:
                df_type.to_excel(writer, sheet_name='Contracts by Type', index=False)
            buffer.seek(0)
            st.download_button(
                f"Download Contracts by Type (Excel)",
                data=buffer,
                file_name="contracts_by_type.xlsx",
                mime="application/vnd.ms-excel"
            )
    
    # Contracts by status
    contracts_by_status = get_contracts_by_status()
    if contracts_by_status:
        st.subheader("Contracts by Status")
        df_status = pd.DataFrame(contracts_by_status)
        
        # Create a pie chart
        fig2 = px.pie(
            df_status, 
            values='Count', 
            names='Status', 
            title='Contract Status Distribution',
            color_discrete_sequence=px.colors.qualitative.Set2
        )
        st.plotly_chart(fig2, use_container_width=True)
        
        # Allow download
        if download_format == "CSV":
            csv = df_status.to_csv(index=False)
            st.download_button(
                f"Download Contracts by Status (CSV)",
                data=csv,
                file_name="contracts_by_status.csv",
                mime="text/csv"
            )
        else:
            buffer = io.BytesIO()
            with pd.ExcelWriter(buffer, engine='xlsxwriter') as writer:
                df_status.to_excel(writer, sheet_name='Contracts by Status', index=False)
            buffer.seek(0)
            st.download_button(
                f"Download Contracts by Status (Excel)",
                data=buffer,
                file_name="contracts_by_status.xlsx",
                mime="application/vnd.ms-excel"
            )
    
    # Monthly contract trends
    contracts_by_month = get_contracts_by_month()
    if contracts_by_month:
        st.subheader("Monthly Contract Trends")
        df_month = pd.DataFrame(contracts_by_month)
        
        # Create a line chart
        fig3 = px.line(
            df_month, 
            x='Month', 
            y='Count', 
            title='Monthly Contract Trend',
            markers=True,
            line_shape='linear',
            color_discrete_sequence=['#2563EB']
        )
        fig3.update_layout(xaxis_title='Month', yaxis_title='Number of Contracts')
        st.plotly_chart(fig3, use_container_width=True)
        
        # Allow download
        if download_format == "CSV":
            csv = df_month.to_csv(index=False)
            st.download_button(
                f"Download Monthly Contract Trends (CSV)",
                data=csv,
                file_name="contracts_by_month.csv",
                mime="text/csv"
            )
        else:
            buffer = io.BytesIO()
            with pd.ExcelWriter(buffer, engine='xlsxwriter') as writer:
                df_month.to_excel(writer, sheet_name='Monthly Contracts', index=False)
            buffer.seek(0)
            st.download_button(
                f"Download Monthly Contract Trends (Excel)",
                data=buffer,
                file_name="contracts_by_month.xlsx",
                mime="application/vnd.ms-excel"
            )

# Claims Analysis Report
elif report_type == "Claims Analysis":
    st.subheader("Claims Analysis Report")
    
    # Display overall claims metrics
    metrics = get_claims_metrics()
    if metrics and metrics[0]['TotalClaims'] > 0:
        col1, col2, col3 = st.columns(3)
        
        with col1:
            # Convert Decimal to int
            total_claims = int(metrics[0]['TotalClaims'])
            st.metric("Total Claims", total_claims)
        with col2:
            # Convert Decimal values to float for calculations
            approved = float(metrics[0]['ApprovedClaims'])
            total = float(metrics[0]['TotalClaims'])
            approval_rate = (approved / total) * 100 if total > 0 else 0
            st.metric("Approval Rate", f"{approval_rate:.1f}%")
        with col3:
            # Convert Decimal to float
            avg_amount = float(metrics[0]['AverageClaimAmount'] or 0)
            st.metric("Average Claim Amount", f"${avg_amount:,.2f}")
        
        col1, col2, col3 = st.columns(3)
        with col1:
            # Convert Decimal to int
            approved = int(metrics[0]['ApprovedClaims'])
            st.metric("Approved Claims", approved)
        with col2:
            # Convert Decimal to int
            rejected = int(metrics[0]['RejectedClaims'])
            st.metric("Rejected Claims", rejected)
        with col3:
            # Convert Decimal to int
            pending = int(metrics[0]['PendingClaims'])
            st.metric("Pending Claims", pending)
    
    # Claims by status
    claims_by_status = get_claims_by_status()
    if claims_by_status:
        st.subheader("Claims by Status")
        df_status = pd.DataFrame(claims_by_status)
        
        # Create a pie chart
        fig1 = px.pie(
            df_status, 
            values='Count', 
            names='Result', 
            title='Claim Status Distribution',
            color_discrete_sequence=px.colors.qualitative.Safe
        )
        st.plotly_chart(fig1, use_container_width=True)
        
        # Allow download
        if download_format == "CSV":
            csv = df_status.to_csv(index=False)
            st.download_button(
                f"Download Claims by Status (CSV)",
                data=csv,
                file_name="claims_by_status.csv",
                mime="text/csv"
            )
        else:
            buffer = io.BytesIO()
            with pd.ExcelWriter(buffer, engine='xlsxwriter') as writer:
                df_status.to_excel(writer, sheet_name='Claims by Status', index=False)
            buffer.seek(0)
            st.download_button(
                f"Download Claims by Status (Excel)",
                data=buffer,
                file_name="claims_by_status.xlsx",
                mime="application/vnd.ms-excel"
            )
    
    # Claims by insurance type
    claims_by_type = get_claims_by_type()
    claim_amounts = get_claim_amounts_by_type()
    
    if claims_by_type and claim_amounts:
        st.subheader("Claims Analysis by Insurance Type")
        
        # Merge the data
        df_type = pd.DataFrame(claims_by_type)
        df_amounts = pd.DataFrame(claim_amounts)
        df_combined = pd.merge(df_type, df_amounts, on='InsuranceName')
        
        # Format for display
        df_display = df_combined.copy()
        df_display['TotalAmount'] = df_display['TotalAmount'].apply(lambda x: f"${x:,.2f}" if x else "$0.00")
        df_display['AverageAmount'] = df_display['AverageAmount'].apply(lambda x: f"${x:,.2f}" if x else "$0.00")
        
        # Display the data as a table
        st.dataframe(df_display, use_container_width=True)
        
        # Create a bar chart for claim counts
        fig2 = px.bar(
            df_type, 
            x='InsuranceName', 
            y='Count', 
            title='Claims Count by Insurance Type',
            color='InsuranceName',
            color_discrete_sequence=px.colors.qualitative.Bold
        )
        fig2.update_layout(xaxis_title='Insurance Type', yaxis_title='Number of Claims')
        st.plotly_chart(fig2, use_container_width=True)
        
        # Allow download
        if download_format == "CSV":
            csv = df_combined.to_csv(index=False)
            st.download_button(
                f"Download Claims by Insurance Type (CSV)",
                data=csv,
                file_name="claims_by_type.csv",
                mime="text/csv"
            )
        else:
            buffer = io.BytesIO()
            with pd.ExcelWriter(buffer, engine='xlsxwriter') as writer:
                df_combined.to_excel(writer, sheet_name='Claims by Type', index=False)
            buffer.seek(0)
            st.download_button(
                f"Download Claims by Insurance Type (Excel)",
                data=buffer,
                file_name="claims_by_type.xlsx",
                mime="application/vnd.ms-excel"
            )
    
    # Monthly claim trends
    claims_by_month = get_claims_by_month()
    if claims_by_month:
        st.subheader("Monthly Claims Trends")
        df_month = pd.DataFrame(claims_by_month)
        
        # Create a line chart
        fig3 = px.line(
            df_month, 
            x='Month', 
            y='Count', 
            title='Monthly Claims Trend',
            markers=True,
            line_shape='linear',
            color_discrete_sequence=['#10B981']
        )
        fig3.update_layout(xaxis_title='Month', yaxis_title='Number of Claims')
        st.plotly_chart(fig3, use_container_width=True)
        
        # Allow download
        if download_format == "CSV":
            csv = df_month.to_csv(index=False)
            st.download_button(
                f"Download Monthly Claims Trends (CSV)",
                data=csv,
                file_name="claims_by_month.csv",
                mime="text/csv"
            )
        else:
            buffer = io.BytesIO()
            with pd.ExcelWriter(buffer, engine='xlsxwriter') as writer:
                df_month.to_excel(writer, sheet_name='Monthly Claims', index=False)
            buffer.seek(0)
            st.download_button(
                f"Download Monthly Claims Trends (Excel)",
                data=buffer,
                file_name="claims_by_month.xlsx",
                mime="application/vnd.ms-excel"
            )

# Payout Summary Report
elif report_type == "Payout Summary":
    st.subheader("Payout Summary Report")
    
    # Display overall payout metrics
    metrics = get_payout_metrics()
    if metrics and metrics[0]['TotalPayouts'] > 0:
        col1, col2, col3 = st.columns(3)
        
        with col1:
            # Convert Decimal to int
            total_payouts = int(metrics[0]['TotalPayouts'])
            st.metric("Total Payouts", total_payouts)
        with col2:
            # Convert Decimal to float
            total_amount = float(metrics[0]['TotalApprovedAmount'] or 0)
            st.metric("Total Approved Amount", f"${total_amount:,.2f}")
        with col3:
            # Convert Decimal to float
            avg_amount = float(metrics[0]['AveragePayoutAmount'] or 0)
            st.metric("Average Payout Amount", f"${avg_amount:,.2f}")
    
    # Payouts by status
    payouts_by_status = get_payouts_by_status()
    if payouts_by_status:
        st.subheader("Payouts by Status")
        df_status = pd.DataFrame(payouts_by_status)
        
        # Format the amounts for display
        df_display = df_status.copy()
        if 'TotalAmount' in df_display.columns:
            df_display['TotalAmount'] = df_display['TotalAmount'].apply(lambda x: f"${x:,.2f}" if x else "$0.00")
        
        # Display the data as a table
        st.dataframe(df_display, use_container_width=True)
        
        # Create a pie chart for payout counts
        fig1 = px.pie(
            df_status, 
            values='Count', 
            names='Status', 
            title='Payout Status Distribution',
            color_discrete_sequence=px.colors.qualitative.Pastel
        )
        st.plotly_chart(fig1, use_container_width=True)
        
        # Allow download
        if download_format == "CSV":
            csv = df_status.to_csv(index=False)
            st.download_button(
                f"Download Payouts by Status (CSV)",
                data=csv,
                file_name="payouts_by_status.csv",
                mime="text/csv"
            )
        else:
            buffer = io.BytesIO()
            with pd.ExcelWriter(buffer, engine='xlsxwriter') as writer:
                df_status.to_excel(writer, sheet_name='Payouts by Status', index=False)
            buffer.seek(0)
            st.download_button(
                f"Download Payouts by Status (Excel)",
                data=buffer,
                file_name="payouts_by_status.xlsx",
                mime="application/vnd.ms-excel"
            )
    
    # Payouts by insurance type
    payouts_by_type = get_payouts_by_type()
    if payouts_by_type:
        st.subheader("Payouts by Insurance Type")
        df_type = pd.DataFrame(payouts_by_type)
        
        # Format the amounts for display
        df_display = df_type.copy()
        df_display['TotalAmount'] = df_display['TotalAmount'].apply(lambda x: f"${x:,.2f}" if x else "$0.00")
        
        # Display the data as a table
        st.dataframe(df_display, use_container_width=True)
        
        # Create a bar chart
        fig2 = px.bar(
            df_type, 
            x='InsuranceName', 
            y='TotalAmount', 
            title='Total Payout Amount by Insurance Type',
            color='InsuranceName',
            color_discrete_sequence=px.colors.qualitative.G10
        )
        fig2.update_layout(xaxis_title='Insurance Type', yaxis_title='Total Amount ($)')
        st.plotly_chart(fig2, use_container_width=True)
        
        # Allow download
        if download_format == "CSV":
            csv = df_display.to_csv(index=False)
            st.download_button(
                f"Download Payouts by Insurance Type (CSV)",
                data=csv,
                file_name="payouts_by_type.csv",
                mime="text/csv"
            )
        else:
            buffer = io.BytesIO()
            with pd.ExcelWriter(buffer, engine='xlsxwriter') as writer:
                df_display.to_excel(writer, sheet_name='Payouts by Type', index=False)
            buffer.seek(0)
            st.download_button(
                f"Download Payouts by Insurance Type (Excel)",
                data=buffer,
                file_name="payouts_by_type.xlsx",
                mime="application/vnd.ms-excel"
            )
    
    # Monthly payout trends
    payouts_by_month = get_payouts_by_month()
    if payouts_by_month:
        st.subheader("Monthly Payout Trends")
        df_month = pd.DataFrame(payouts_by_month)
        
        # Create a line chart
        fig3 = px.line(
            df_month, 
            x='Month', 
            y='TotalAmount', 
            title='Monthly Payout Trend',
            markers=True,
            line_shape='linear',
            color_discrete_sequence=['#F59E0B']
        )
        fig3.update_layout(xaxis_title='Month', yaxis_title='Total Amount ($)')
        st.plotly_chart(fig3, use_container_width=True)
        
        # Allow download
        if download_format == "CSV":
            csv = df_month.to_csv(index=False)
            st.download_button(
                f"Download Monthly Payout Trends (CSV)",
                data=csv,
                file_name="payouts_by_month.csv",
                mime="text/csv"
            )
        else:
            buffer = io.BytesIO()
            with pd.ExcelWriter(buffer, engine='xlsxwriter') as writer:
                df_month.to_excel(writer, sheet_name='Monthly Payouts', index=False)
            buffer.seek(0)
            st.download_button(
                f"Download Monthly Payout Trends (Excel)",
                data=buffer,
                file_name="payouts_by_month.xlsx",
                mime="application/vnd.ms-excel"
            )

# Customer Activity Report
elif report_type == "Customer Activity":
    st.subheader("Customer Activity Report")
    
    # Display customer overview metrics
    overview = get_customer_overview()
    if overview and overview[0]['TotalCustomers'] > 0:
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            # Convert Decimal to int
            total_customers = int(overview[0]['TotalCustomers'])
            st.metric("Total Customers", total_customers)
        with col2:
            # Convert Decimal to float
            avg_contracts = float(overview[0]['AvgContractsPerCustomer'] or 0)
            st.metric("Avg Contracts/Customer", f"{avg_contracts:.2f}")
        with col3:
            # Convert Decimal to float
            avg_claims = float(overview[0]['AvgClaimsPerCustomer'] or 0)
            st.metric("Avg Claims/Customer", f"{avg_claims:.2f}")
        with col4:
            # Convert Decimal to float
            avg_payout = float(overview[0]['AvgPayoutPerCustomer'] or 0)
            st.metric("Avg Payout/Customer", f"${avg_payout:,.2f}")
    
    # Top customers by contracts
    top_customers_contracts = get_top_customers_by_contracts()
    if top_customers_contracts:
        st.subheader("Top Customers by Number of Contracts")
        df_contracts = pd.DataFrame(top_customers_contracts)
        
        # Create a bar chart
        fig1 = px.bar(
            df_contracts, 
            x='CustomerName', 
            y='ContractCount', 
            title='Top 10 Customers by Number of Contracts',
            color='ContractCount',
            color_continuous_scale='Blues'
        )
        fig1.update_layout(xaxis_title='Customer', yaxis_title='Number of Contracts')
        st.plotly_chart(fig1, use_container_width=True)
        
        # Allow download
        if download_format == "CSV":
            csv = df_contracts.to_csv(index=False)
            st.download_button(
                f"Download Top Customers by Contracts (CSV)",
                data=csv,
                file_name="top_customers_contracts.csv",
                mime="text/csv"
            )
        else:
            buffer = io.BytesIO()
            with pd.ExcelWriter(buffer, engine='xlsxwriter') as writer:
                df_contracts.to_excel(writer, sheet_name='Top Customers', index=False)
            buffer.seek(0)
            st.download_button(
                f"Download Top Customers by Contracts (Excel)",
                data=buffer,
                file_name="top_customers_contracts.xlsx",
                mime="application/vnd.ms-excel"
            )
    
    # Top customers by payout
    top_customers_payouts = get_top_customers_by_payout()
    if top_customers_payouts:
        st.subheader("Top Customers by Total Payout Amount")
        df_payouts = pd.DataFrame(top_customers_payouts)
        
        # Format for display
        df_display = df_payouts.copy()
        df_display['TotalPayoutAmount'] = df_display['TotalPayoutAmount'].apply(lambda x: f"${x:,.2f}" if x else "$0.00")
        
        # Display the table
        st.dataframe(df_display, use_container_width=True)
        
        # Create a bar chart
        fig2 = px.bar(
            df_payouts, 
            x='CustomerName', 
            y='TotalPayoutAmount', 
            title='Top 10 Customers by Total Payout Amount',
            color='TotalPayoutAmount',
            color_continuous_scale='Greens'
        )
        fig2.update_layout(xaxis_title='Customer', yaxis_title='Total Payout Amount ($)')
        st.plotly_chart(fig2, use_container_width=True)
        
        # Allow download
        if download_format == "CSV":
            csv = df_display.to_csv(index=False)
            st.download_button(
                f"Download Top Customers by Payouts (CSV)",
                data=csv,
                file_name="top_customers_payouts.csv",
                mime="text/csv"
            )
        else:
            buffer = io.BytesIO()
            with pd.ExcelWriter(buffer, engine='xlsxwriter') as writer:
                df_display.to_excel(writer, sheet_name='Top Customers', index=False)
            buffer.seek(0)
            st.download_button(
                f"Download Top Customers by Payouts (Excel)",
                data=buffer,
                file_name="top_customers_payouts.xlsx",
                mime="application/vnd.ms-excel"
            )
    
    # Top customers by claims
    top_customers_claims = get_top_customers_by_claims()
    if top_customers_claims:
        st.subheader("Top Customers by Number of Claims")
        df_claims = pd.DataFrame(top_customers_claims)
        
        # Create a bar chart
        fig3 = px.bar(
            df_claims, 
            x='CustomerName', 
            y='ClaimCount', 
            title='Top 10 Customers by Number of Claims',
            color='ClaimCount',
            color_continuous_scale='Reds'
        )
        fig3.update_layout(xaxis_title='Customer', yaxis_title='Number of Claims')
        st.plotly_chart(fig3, use_container_width=True)
        
        # Allow download
        if download_format == "CSV":
            csv = df_claims.to_csv(index=False)
            st.download_button(
                f"Download Top Customers by Claims (CSV)",
                data=csv,
                file_name="top_customers_claims.csv",
                mime="text/csv"
            )
        else:
            buffer = io.BytesIO()
            with pd.ExcelWriter(buffer, engine='xlsxwriter') as writer:
                df_claims.to_excel(writer, sheet_name='Top Customers', index=False)
            buffer.seek(0)
            st.download_button(
                f"Download Top Customers by Claims (Excel)",
                data=buffer,
                file_name="top_customers_claims.xlsx",
                mime="application/vnd.ms-excel"
            )
