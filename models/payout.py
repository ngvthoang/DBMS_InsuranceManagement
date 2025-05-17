import streamlit as st
import pandas as pd
import datetime
from database.db_connector import create_connection, execute_query, get_cached_data, execute_write_query
from models.assessment import get_approved_claims
from mysql.connector import Error

@st.cache_data(ttl=300)
def get_all_payouts(limit=100, offset=0):
    """Get all payouts with related information with pagination"""
    # Truy vấn này lấy tất cả các khoản thanh toán với thông tin liên quan.
    # Đã thêm LIMIT và OFFSET để hỗ trợ phân trang, giúp giảm tải dữ liệu trả về.
    query = """
        SELECT p.PayoutID, p.ContractID, cust.CustomerName, 
               p.PayoutDate, p.Amount, p.Status, t.InsuranceName
        FROM Payouts p
        JOIN InsuranceContracts c ON p.ContractID = c.ContractID
        JOIN Customers cust ON c.CustomerID = cust.CustomerID
        JOIN InsuranceTypes t ON c.InsuranceTypeID = t.InsuranceTypeID
        ORDER BY p.PayoutDate DESC
        LIMIT %s OFFSET %s
    """
    return get_cached_data(query, (limit, offset))

@st.cache_data(ttl=300)
def get_payout_by_id(payout_id):
    """Get a specific payout by ID"""
    # Truy vấn này lấy thông tin chi tiết của một khoản thanh toán dựa trên ID.
    # Chỉ chọn các cột cần thiết để giảm tải dữ liệu không cần thiết.
    query = """
        SELECT p.PayoutID, p.ContractID, c.CustomerID, cust.CustomerName,
               p.PayoutDate, p.Amount, p.Status, t.InsuranceName
        FROM Payouts p
        JOIN InsuranceContracts c ON p.ContractID = c.ContractID
        JOIN Customers cust ON c.CustomerID = cust.CustomerID
        JOIN InsuranceTypes t ON c.InsuranceTypeID = t.InsuranceTypeID
        WHERE p.PayoutID = %s
    """
    result = get_cached_data(query, (payout_id,))
    if result and len(result) > 0:
        return result[0]
    return None

@st.cache_data(ttl=300)
def get_payouts_dropdown():
    """Get payouts for dropdown selection"""
    # Truy vấn này lấy danh sách các khoản thanh toán để hiển thị trong dropdown.
    # Đã thêm LIMIT để giới hạn số lượng kết quả trả về.
    query = """
        SELECT p.PayoutID, cust.CustomerName, p.Amount
        FROM Payouts p
        JOIN InsuranceContracts c ON p.ContractID = c.ContractID
        JOIN Customers cust ON c.CustomerID = cust.CustomerID
        LIMIT 100
    """
    payouts = get_cached_data(query)
    if not payouts:
        return {}
    return {f"{p['PayoutID']}: {p['CustomerName']} - ${float(p['Amount']):,.2f}": p['PayoutID'] for p in payouts}

@st.cache_data(ttl=300)
def get_pending_payouts():
    """Get pending payouts"""
    query = """
        SELECT p.PayoutID, p.ContractID, cust.CustomerName, 
               p.PayoutDate, p.Amount, p.Status
        FROM Payouts p
        JOIN InsuranceContracts c ON p.ContractID = c.ContractID
        JOIN Customers cust ON c.CustomerID = cust.CustomerID
        WHERE p.Status = 'Pending'
        ORDER BY p.PayoutDate
    """
    return get_cached_data(query)

@st.cache_data(ttl=300)
def get_total_approved_payouts():
    """Get total amount of approved payouts"""
    query = """
        SELECT SUM(Amount) AS total
        FROM Payouts
        WHERE Status = 'Approved' OR Status = 'Completed'
    """
    result = get_cached_data(query)
    return result[0]['total'] if result and result[0]['total'] else 0

@st.cache_data(ttl=300)
def get_payout_counts_by_status():
    """Get count of payouts by status"""
    query = """
        SELECT Status, COUNT(*) AS count
        FROM Payouts
        GROUP BY Status
    """
    return get_cached_data(query)

def generate_next_payout_id():
    """Generate the next payout ID"""
    last_payout = get_cached_data("SELECT PayoutID FROM Payouts ORDER BY PayoutID DESC LIMIT 1")
    next_id = "P001"  # Default starting ID if no records exist
    
    if last_payout and len(last_payout) > 0:
        last_id = last_payout[0]['PayoutID']
        # Extract the numeric part, increment it, and format it back
        try:
            id_num = int(last_id[1:])
            next_id = f"P{(id_num + 1):03d}"
        except (ValueError, IndexError):
            pass  # Use default if parsing fails
    
    return next_id

def add_payout(payout_id, contract_id, amount, payout_date, status="Pending"):
    """Add a new payout to the database"""
    query = """
    INSERT INTO Payouts (PayoutID, ContractID, Amount, PayoutDate, Status) 
    VALUES (%s, %s, %s, %s, %s)
    """
    data = (payout_id, contract_id, amount, payout_date, status)
    result = execute_write_query(query, data)
    
    # Clear cache for payout-related functions
    clear_payout_cache()
    
    return result

def update_payout_status(payout_id, status):
    """Update a payout's status in the database"""
    query = """
    UPDATE Payouts 
    SET Status = %s
    WHERE PayoutID = %s
    """
    data = (status, payout_id)
    result = execute_write_query(query, data)
    
    # Clear cache for payout-related functions
    clear_payout_cache()
    
    return result

def clear_payout_cache():
    """Clear all cached payout data"""
    if hasattr(get_all_payouts, 'clear'):
        get_all_payouts.clear()
    if hasattr(get_payout_by_id, 'clear'):
        get_payout_by_id.clear()
    if hasattr(get_payouts_dropdown, 'clear'):
        get_payouts_dropdown.clear()
    if hasattr(get_pending_payouts, 'clear'):
        get_pending_payouts.clear()
    if hasattr(get_total_approved_payouts, 'clear'):
        get_total_approved_payouts.clear()
    if hasattr(get_payout_counts_by_status, 'clear'):
        get_payout_counts_by_status.clear()