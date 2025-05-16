import streamlit as st
import pandas as pd
import plotly.express as px
from database.db_connector import get_cached_data

@st.cache_data(ttl=300)
def get_contracts_by_type():
    """Get contracts by insurance type for reporting"""
    query = """
        SELECT t.InsuranceName, COUNT(*) as Count
        FROM InsuranceContracts c
        JOIN InsuranceTypes t ON c.InsuranceTypeID = t.InsuranceTypeID
        GROUP BY t.InsuranceName
    """
    return get_cached_data(query)

@st.cache_data(ttl=300)
def get_contracts_by_status():
    """Get contracts by status for reporting"""
    query = """
        SELECT Status, COUNT(*) as Count
        FROM InsuranceContracts
        GROUP BY Status
    """
    return get_cached_data(query)

@st.cache_data(ttl=300)
def get_contracts_by_month():
    """Get contracts by month for reporting"""
    query = """
        SELECT DATE_FORMAT(SignDate, '%Y-%m') as Month, COUNT(*) as Count
        FROM InsuranceContracts
        GROUP BY DATE_FORMAT(SignDate, '%Y-%m')
        ORDER BY Month
    """
    return get_cached_data(query)

@st.cache_data(ttl=300)
def get_active_contracts_summary():
    """Get summary of active contracts"""
    query = """
        SELECT 
            COUNT(*) as TotalActive,
            SUM(CASE WHEN ExpirationDate <= DATE_ADD(CURDATE(), INTERVAL 30 DAY) THEN 1 ELSE 0 END) as ExpiringIn30Days,
            MIN(ExpirationDate) as EarliestExpiration,
            MAX(ExpirationDate) as LatestExpiration
        FROM InsuranceContracts
        WHERE Status = 'Active'
    """
    return get_cached_data(query)

@st.cache_data(ttl=300)
def get_claims_by_status():
    """Get claims by status for reporting"""
    query = """
        SELECT Result, COUNT(*) as Count
        FROM Assessments
        GROUP BY Result
    """
    return get_cached_data(query)

@st.cache_data(ttl=300)
def get_claims_by_type():
    """Get claims by insurance type for reporting"""
    query = """
        SELECT t.InsuranceName, COUNT(*) as Count
        FROM Assessments a
        JOIN InsuranceContracts c ON a.ContractID = c.ContractID
        JOIN InsuranceTypes t ON c.InsuranceTypeID = t.InsuranceTypeID
        GROUP BY t.InsuranceName
    """
    return get_cached_data(query)

@st.cache_data(ttl=300)
def get_claim_amounts_by_type():
    """Get claim amounts by insurance type"""
    query = """
        SELECT t.InsuranceName, SUM(a.ClaimAmount) as TotalAmount, AVG(a.ClaimAmount) as AverageAmount
        FROM Assessments a
        JOIN InsuranceContracts c ON a.ContractID = c.ContractID
        JOIN InsuranceTypes t ON c.InsuranceTypeID = t.InsuranceTypeID
        GROUP BY t.InsuranceName
    """
    return get_cached_data(query)

@st.cache_data(ttl=300)
def get_claims_by_month():
    """Get claims by month for reporting"""
    query = """
        SELECT DATE_FORMAT(AssessmentDate, '%Y-%m') as Month, COUNT(*) as Count
        FROM Assessments
        GROUP BY DATE_FORMAT(AssessmentDate, '%Y-%m')
        ORDER BY Month
    """
    return get_cached_data(query)

@st.cache_data(ttl=300)
def get_claims_metrics():
    """Get overall claims metrics"""
    query = """
        SELECT 
            COUNT(*) as TotalClaims,
            SUM(CASE WHEN Result = 'Approved' THEN 1 ELSE 0 END) as ApprovedClaims,
            SUM(CASE WHEN Result = 'Rejected' THEN 1 ELSE 0 END) as RejectedClaims,
            SUM(CASE WHEN Result = 'Pending' THEN 1 ELSE 0 END) as PendingClaims,
            AVG(ClaimAmount) as AverageClaimAmount,
            MAX(ClaimAmount) as MaximumClaimAmount
        FROM Assessments
    """
    return get_cached_data(query)

@st.cache_data(ttl=300)
def get_payouts_by_type():
    """Get payouts by insurance type for reporting"""
    query = """
        SELECT t.InsuranceName, COUNT(*) as Count, SUM(p.Amount) as TotalAmount
        FROM Payouts p
        JOIN InsuranceContracts c ON p.ContractID = c.ContractID
        JOIN InsuranceTypes t ON c.InsuranceTypeID = t.InsuranceTypeID
        WHERE p.Status = 'Approved' OR p.Status = 'Completed'
        GROUP BY t.InsuranceName
    """
    return get_cached_data(query)

@st.cache_data(ttl=300)
def get_payouts_by_month():
    """Get payouts by month for reporting"""
    query = """
        SELECT DATE_FORMAT(PayoutDate, '%Y-%m') as Month, SUM(Amount) as TotalAmount
        FROM Payouts
        WHERE Status = 'Approved' OR Status = 'Completed'
        GROUP BY DATE_FORMAT(PayoutDate, '%Y-%m')
        ORDER BY Month
    """
    return get_cached_data(query)

@st.cache_data(ttl=300)
def get_payouts_by_status():
    """Get payouts by status for reporting"""
    query = """
        SELECT Status, COUNT(*) as Count, SUM(Amount) as TotalAmount
        FROM Payouts
        GROUP BY Status
    """
    return get_cached_data(query)

@st.cache_data(ttl=300)
def get_payout_metrics():
    """Get overall payout metrics"""
    query = """
        SELECT 
            COUNT(*) as TotalPayouts,
            SUM(CASE WHEN Status = 'Approved' OR Status = 'Completed' THEN Amount ELSE 0 END) as TotalApprovedAmount,
            AVG(CASE WHEN Status = 'Approved' OR Status = 'Completed' THEN Amount ELSE NULL END) as AveragePayoutAmount,
            MAX(CASE WHEN Status = 'Approved' OR Status = 'Completed' THEN Amount ELSE NULL END) as MaximumPayoutAmount
        FROM Payouts
    """
    return get_cached_data(query)

@st.cache_data(ttl=300)
def get_top_customers_by_contracts():
    """Get top customers by number of contracts"""
    query = """
        SELECT cust.CustomerName, COUNT(c.ContractID) as ContractCount
        FROM Customers cust
        LEFT JOIN InsuranceContracts c ON cust.CustomerID = c.CustomerID
        GROUP BY cust.CustomerID
        ORDER BY ContractCount DESC
        LIMIT 10
    """
    return get_cached_data(query)

@st.cache_data(ttl=300)
def get_top_customers_by_payout():
    """Get top customers by total payout amount"""
    query = """
        SELECT cust.CustomerName, SUM(p.Amount) as TotalPayoutAmount
        FROM Customers cust
        JOIN InsuranceContracts c ON cust.CustomerID = c.CustomerID
        JOIN Payouts p ON c.ContractID = p.ContractID
        WHERE p.Status = 'Approved' OR p.Status = 'Completed'
        GROUP BY cust.CustomerID
        ORDER BY TotalPayoutAmount DESC
        LIMIT 10
    """
    return get_cached_data(query)

@st.cache_data(ttl=300)
def get_top_customers_by_claims():
    """Get top customers by number of claims"""
    query = """
        SELECT cust.CustomerName, COUNT(a.AssessmentID) as ClaimCount
        FROM Customers cust
        JOIN InsuranceContracts c ON cust.CustomerID = c.CustomerID
        JOIN Assessments a ON c.ContractID = a.ContractID
        GROUP BY cust.CustomerID
        ORDER BY ClaimCount DESC
        LIMIT 10
    """
    return get_cached_data(query)

@st.cache_data(ttl=300)
def get_customer_overview():
    """Get customer overview metrics"""
    query = """
        SELECT 
            COUNT(DISTINCT cust.CustomerID) as TotalCustomers,
            AVG(contracts.ContractCount) as AvgContractsPerCustomer,
            AVG(IFNULL(claims.ClaimCount, 0)) as AvgClaimsPerCustomer,
            AVG(IFNULL(payouts.PayoutAmount, 0)) as AvgPayoutPerCustomer
        FROM 
            Customers cust
            LEFT JOIN (
                SELECT CustomerID, COUNT(ContractID) as ContractCount
                FROM InsuranceContracts
                GROUP BY CustomerID
            ) contracts ON cust.CustomerID = contracts.CustomerID
            LEFT JOIN (
                SELECT c.CustomerID, COUNT(a.AssessmentID) as ClaimCount
                FROM Customers c
                JOIN InsuranceContracts ic ON c.CustomerID = ic.CustomerID
                JOIN Assessments a ON ic.ContractID = a.ContractID
                GROUP BY c.CustomerID
            ) claims ON cust.CustomerID = claims.CustomerID
            LEFT JOIN (
                SELECT c.CustomerID, SUM(p.Amount) as PayoutAmount
                FROM Customers c
                JOIN InsuranceContracts ic ON c.CustomerID = ic.CustomerID
                JOIN Payouts p ON ic.ContractID = p.ContractID
                WHERE p.Status = 'Approved' OR p.Status = 'Completed'
                GROUP BY c.CustomerID
            ) payouts ON cust.CustomerID = payouts.CustomerID
    """
    return get_cached_data(query)
