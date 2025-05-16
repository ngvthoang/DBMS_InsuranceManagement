from math import e
import streamlit as st
import hashlib

# Function to hash passwords
def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

# Updated login function with role-based access
def login():
    st.markdown('<div class="main-header" style="font-size: 20px; font-weight: bold; margin-bottom: 20px;">Insurance Management System Login</div>', unsafe_allow_html=True)
    username = st.text_input("Username")
    password = st.text_input("Password", type="password")
    login_btn = st.button("Login")

    if login_btn:
        # Simulate database query for user credentials and roles
        user_data = {
            "admin": {"password": hash_password("admin123"), "role": "Admin"},
            "agent_user": {"password": hash_password("agent123"), "role": "Insurance Agent"},
            "assessor_user": {"password": hash_password("assessor123"), "role": "Claim Assessor"}
        }

        if username in user_data and user_data[username]["password"] == hash_password(password):
            st.session_state["logged_in"] = True
            st.session_state["username"] = username
            st.session_state["role"] = user_data[username]["role"]
            st.success(f"Login successful! Role: {user_data[username]['role']}")
            st.rerun()
        else:
            st.error("Invalid username or password.")

# # Check login state
# if "logged_in" not in st.session_state or not st.session_state["logged_in"]:
#     login()
#     st.stop()

# # Role-based content display
# role = st.session_state.get("role", "")
# if role == "Insurance Agent":
#     st.write("Access restricted: You cannot view Payouts and Assessments.")
# elif role == "Claim Assessor":
#     st.write("Access restricted: You cannot view Customers Management, Insurance Types, and Contracts Management.")
# elif role == "Admin":
#     st.write("Acess granted: You can view all sections.")