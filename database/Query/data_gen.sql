-- Create and populate the database for an Insurance Management System
CREATE DATABASE IF NOT EXISTS prj_insurance;
USE prj_insurance;

-- Drop tables in reverse order of creation (due to foreign key constraints)
DROP TABLE IF EXISTS Users;
DROP TABLE IF EXISTS Roles;
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
    EncryptedClaimAmount VARBINARY(255),
    FOREIGN KEY (ContractID) REFERENCES InsuranceContracts(ContractID)
);

CREATE TABLE Payouts (
    PayoutID VARCHAR(10) PRIMARY KEY,
    ContractID VARCHAR(10),
    Amount DECIMAL(12, 2),
    PayoutDate DATE,
    Status VARCHAR(20) DEFAULT 'Pending',
    EncryptedAmount VARBINARY(255),
    FOREIGN KEY (ContractID) REFERENCES InsuranceContracts(ContractID)
);

CREATE TABLE Roles (
    RoleID INT PRIMARY KEY AUTO_INCREMENT,
    RoleName VARCHAR(50) UNIQUE NOT NULL
);

CREATE TABLE Users (
    UserID INT PRIMARY KEY AUTO_INCREMENT,
    Username VARCHAR(50) UNIQUE NOT NULL,
    PasswordHash VARCHAR(255) NOT NULL,
    RoleID INT,
    FOREIGN KEY (RoleID) REFERENCES Roles(RoleID)
);

-- Insert Roles
INSERT INTO Roles (RoleName) VALUES ('Admin'), ('Insurance Agent'), ('Claim Assessor');

-- Insert Users
INSERT INTO Users (Username, PasswordHash, RoleID) VALUES
('admin', SHA2('admin123', 256), 1),
('agent_user', SHA2('agent123', 256), 2),
('assessor_user', SHA2('assessor123', 256), 3);

-- Encrypt sensitive data in Assessments and Payouts
UPDATE Assessments SET EncryptedClaimAmount = AES_ENCRYPT(ClaimAmount, 'encryption_key');
UPDATE Payouts SET EncryptedAmount = AES_ENCRYPT(Amount, 'encryption_key');

-- Optimize contract lookups by CustomerID, InsuranceTypeID, ExpirationDate, and Status
CREATE INDEX idx_contract_customer ON InsuranceContracts(CustomerID);
CREATE INDEX idx_contract_type ON InsuranceContracts(InsuranceTypeID);
CREATE INDEX idx_contract_expiration ON InsuranceContracts(ExpirationDate);
CREATE INDEX idx_contract_status ON InsuranceContracts(Status);

-- Optimize claim (assessment) lookups by ContractID, Result, and AssessmentDate
CREATE INDEX idx_assessment_contract ON Assessments(ContractID);
CREATE INDEX idx_assessment_result ON Assessments(Result);
CREATE INDEX idx_assessment_date ON Assessments(AssessmentDate);

-- Optimize payout lookups by ContractID and Status
CREATE INDEX idx_payout_contract ON Payouts(ContractID);
CREATE INDEX idx_payout_status ON Payouts(Status);

-- -- Insert Sample Data

-- INSERT INTO Customers (CustomerID, CustomerName, Address, PhoneNumber) VALUES
-- ('C001', 'John Smith', '123 Main St, New York, NY', '555-1234'),
-- ('C002', 'Alice Johnson', '456 Oak Ave, Los Angeles, CA', '555-2345'),
-- ('C003', 'Bob Lee', '789 Pine Rd, Chicago, IL', '555-3456'),
-- ('C004', 'Emma Davis', '321 Maple St, Seattle, WA', '555-4567'),
-- ('C005', 'Michael Brown', '654 Elm Dr, Austin, TX', '555-5678');


-- INSERT INTO InsuranceTypes (InsuranceTypeID, InsuranceName, Description) VALUES
-- ('T001', 'Auto Insurance', 'Covers vehicle damage and liability'),
-- ('T002', 'Health Insurance', 'Covers medical expenses and treatments'),
-- ('T003', 'Home Insurance', 'Covers house damage and property loss'),
-- ('T004', 'Travel Insurance', 'Covers trip cancellations and emergencies'),
-- ('T005', 'Life Insurance', 'Provides financial support after death');


-- INSERT INTO InsuranceContracts (ContractID, CustomerID, InsuranceTypeID, SignDate) VALUES
-- ('CT001', 'C001', 'T001', '2024-01-15'),
-- ('CT002', 'C002', 'T002', '2024-03-01'),
-- ('CT003', 'C003', 'T003', '2024-05-10'),
-- ('CT004', 'C001', 'T005', '2024-06-20'),
-- ('CT005', 'C004', 'T004', '2024-07-05'),
-- ('CT006', 'C005', 'T002', '2024-08-12');

-- INSERT INTO Assessments (AssessmentID, ContractID, AssessmentDate, ClaimAmount, Result) VALUES
-- ('A001', 'CT001', '2024-06-01', 5000.00, 'Approved'),
-- ('A002', 'CT002', '2024-04-10', 0.00, 'Rejected'),
-- ('A003', 'CT003', '2024-05-15', 20000.00, 'Approved'),
-- ('A004', 'CT005', '2024-07-10', 0.00, 'Pending'),
-- ('A005', 'CT001', '2025-01-05', 800.00, 'Approved');

-- INSERT INTO Payouts (PayoutID, ContractID, Amount, PayoutDate, Status) VALUES
-- ('P001', 'CT001', 5000.00, '2024-06-15', 'Approved'),
-- ('P002', 'CT003', 20000.00, '2024-05-20', 'Rejected'),
-- ('P003', 'CT004', 150000.00, '2024-07-01', 'Approved'),
-- ('P004', 'CT001', 800.00, '2025-01-10', 'Pending'),
-- ('P005', 'CT002', 0.00, '2024-04-20', 'Rejected'); 