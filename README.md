# DBMS_InsuranceManagement
This project presents a comprehensive Insurance Management System developed using Python, MySQL, and Streamlit for the user interface. The primary goal is to efficiently manage insurance customers, policies/contracts, insurance types, claim assessments, and payout processes. The system emphasizes robust contract lifecycle tracking, streamlined claims processing, and the generation of insightful financial reports.
Core components include a meticulously designed MySQL database (ERD, relational schema) enhanced with advanced features like Indexes, Views, Stored Procedures, User-Defined Functions (UDFs), and Triggers to optimize performance and automate workflows. The Python backend provides functional modules for customer enrollment, contract management, claim entry, and payout processing. A user-friendly interactive interface built with Streamlit allows insurance agents and other users to easily interact with the system, manage data, and access reports. The project also addresses database security through user roles and data protection considerations.

# Getting started

### Project Structure

```
DBMS_InsuranceManagement
├─ database
│  ├─ Query         // Chứa các file .sql để gen data cũng như các functions (trigger, procedure, ...)
│  └─ db_connector.py
├─ models
│  ├─ assessment.py
│  ├─ contract.py
│  ├─ customer.py
│  ├─ dashboard.py
│  ├─ insurance_type.py
│  ├─ payout.py
│  └─ report.py
├─ pages             // Chứa các file .py cho từng trang Streamlit (ví dụ: 01_Customers.py)
├─ .env
├─ .gitignore
├─ Home.py           // Trang chủ của ứng dụng Streamlit
├─ login.py          // Trang đăng nhập (nếu có, hoặc một phần của Home.py)
├─ README.md
└─ requirements.txt
```


### Prerequisites

Before you can run this project, make sure you have the following prerequisites installed:

- Python
- MySQL sever
- Pip (Python package manager)
- Other required Python packages (see in requirement.txt)

### Clone the Repository

To get started, clone this repository to your local machine using the following command:

```cmd
git clone https://github.com/ngvthoang/DBMS_InsuranceManagement
cd DBMS_InsuranceManagement
```
### Installation
Create and activate a virtual environment (optional but recommended)
```cmd
python -m venv venv
source venv/bin/activate  # On Windows, use `venv\Scripts\activate`
```
Install dependencies
```cmd
pip install -r requirements.txt
```
### Set environment example
Create a .env file and set an environment example 

```#DATABASE CONNECTION
DB_HOST = "localhost"

DB_NAME = 'prj_insurance'

DB_USER = 'root'

DB_PASSWORD = 'your password here'
```

### Run processing file
Before running the application, you need to run the processing file to create the database and tables by running the sql files: data_gen.sql, sql_function.sql in the database folder. You can do this by using MySQL Workbench or any other MySQL client.
To run the SQL files in MySQL Workbench:
1. Open MySQL Workbench and connect to your MySQL server.
2. Open the SQL file (data_gen.sql) in MySQL Workbench.
3. Click on the lightning bolt icon (Execute) to run the SQL script.
4. Repeat the same steps for the sql_function.sql file.

### Run the Application
To run the application, navigate to the project directory and run the following command:
```cmd
streamlit run Home.py
```

### Login account
- Username: admin
- Password: admin123

- Username: agent_user
- Password: agent123

- Username: assessor_user  
- Password: assessor123