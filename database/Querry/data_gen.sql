USE DATABASE prj_insurance;

-- Drop tables in reverse order of creation (due to foreign key constraints)
DROP TABLE IF EXISTS Payouts;
DROP TABLE IF EXISTS Assessments;
DROP TABLE IF EXISTS InsuranceContracts;
DROP TABLE IF EXISTS InsuranceTypes;
DROP TABLE IF EXISTS Customers;

-- Create Tables
CREATE TABLE Customers (
    CustomerID VARCHAR(10) PRIMARY KEY,
    CustomerName VARCHAR(100),
    Address VARCHAR(255),
    PhoneNumber VARCHAR(20)
);


CREATE TABLE InsuranceTypes (
    InsuranceTypeID VARCHAR(10) PRIMARY KEY,
    InsuranceName VARCHAR(100),
    Description TEXT
);


CREATE TABLE InsuranceContracts (
    ContractID VARCHAR(10) PRIMARY KEY,
    CustomerID VARCHAR(10),
    InsuranceTypeID VARCHAR(10),
    SignDate DATE,
    ExpirationDate DATE,
    Status VARCHAR(20) DEFAULT 'Active',
    FOREIGN KEY (CustomerID) REFERENCES Customers(CustomerID),
    FOREIGN KEY (InsuranceTypeID) REFERENCES InsuranceTypes(InsuranceTypeID)
);

CREATE TABLE Assessments (
    AssessmentID VARCHAR(10) PRIMARY KEY,
    ContractID VARCHAR(10),
    AssessmentDate DATE,
    ClaimAmount DECIMAL(12, 2),
    Result VARCHAR(255),
    FOREIGN KEY (ContractID) REFERENCES InsuranceContracts(ContractID)
);

CREATE TABLE Payouts (
    PayoutID VARCHAR(10) PRIMARY KEY,
    ContractID VARCHAR(10),
    Amount DECIMAL(12, 2),
    PayoutDate DATE,
    Status VARCHAR(20) DEFAULT 'Pending',
    FOREIGN KEY (ContractID) REFERENCES InsuranceContracts(ContractID)
);

-- Insert Sample Data


INSERT INTO Customers (CustomerID, CustomerName, Address, PhoneNumber) VALUES
('C001', 'John Smith', '123 Main St, New York, NY', '555-1234'),
('C002', 'Alice Johnson', '456 Oak Ave, Los Angeles, CA', '555-2345'),
('C003', 'Bob Lee', '789 Pine Rd, Chicago, IL', '555-3456'),
('C004', 'Emma Davis', '321 Maple St, Seattle, WA', '555-4567'),
('C005', 'Michael Brown', '654 Elm Dr, Austin, TX', '555-5678');


INSERT INTO InsuranceTypes (InsuranceTypeID, InsuranceName, Description) VALUES
('T001', 'Auto Insurance', 'Covers vehicle damage and liability'),
('T002', 'Health Insurance', 'Covers medical expenses and treatments'),
('T003', 'Home Insurance', 'Covers house damage and property loss'),
('T004', 'Travel Insurance', 'Covers trip cancellations and emergencies'),
('T005', 'Life Insurance', 'Provides financial support after death');


INSERT INTO InsuranceContracts (ContractID, CustomerID, InsuranceTypeID, SignDate) VALUES
('CT001', 'C001', 'T001', '2024-01-15'),
('CT002', 'C002', 'T002', '2024-03-01'),
('CT003', 'C003', 'T003', '2024-05-10'),
('CT004', 'C001', 'T005', '2024-06-20'),
('CT005', 'C004', 'T004', '2024-07-05'),
('CT006', 'C005', 'T002', '2024-08-12');

INSERT INTO Assessments (AssessmentID, ContractID, AssessmentDate, ClaimAmount, Result) VALUES
('A001', 'CT001', '2024-06-01', 5000.00, 'Approved'),
('A002', 'CT002', '2024-04-10', 0.00, 'Rejected'),
('A003', 'CT003', '2024-05-15', 20000.00, 'Approved'),
('A004', 'CT005', '2024-07-10', 0.00, 'Pending'),
('A005', 'CT001', '2025-01-05', 800.00, 'Approved');

INSERT INTO Payouts (PayoutID, ContractID, Amount, PayoutDate, Status) VALUES
('P001', 'CT001', 5000.00, '2024-06-15', 'Approved'),
('P002', 'CT003', 20000.00, '2024-05-20', 'Rejected'),
('P003', 'CT004', 150000.00, '2024-07-01', 'Approved'),
('P004', 'CT001', 800.00, '2025-01-10', 'Pending'),
('P005', 'CT002', 0.00, '2024-04-20', 'Rejected'); -- rejected claim
