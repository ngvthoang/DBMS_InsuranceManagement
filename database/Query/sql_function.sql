USE prj_insurance;
-- Drop triggers and events first
DROP TRIGGER IF EXISTS AfterAssessmentInsert;
DROP TRIGGER IF EXISTS AfterAssessmentUpdate;
DROP TRIGGER IF EXISTS BeforeContractInsert;
DROP TRIGGER IF EXISTS BeforeContractUpdate;
DROP EVENT IF EXISTS ExpireContractsEvent;

-- Create Trigger to Automatically Create Payouts After Assessment Creation

DELIMITER $$

CREATE TRIGGER AfterAssessmentInsert
AFTER INSERT ON Assessments
FOR EACH ROW
BEGIN
    -- Generate a unique PayoutID
    DECLARE new_payout_id VARCHAR(10);
    SET new_payout_id = CONCAT('P', LPAD((SELECT COUNT(*) + 1 FROM Payouts), 3, '0'));

    -- Automatically create a payout with status 'Pending'
    INSERT INTO Payouts (PayoutID, ContractID, Amount, PayoutDate, Status)
    VALUES (
        new_payout_id,
        NEW.ContractID,
        NEW.ClaimAmount, -- Use the claim amount from the assessment
        CURDATE(), -- Current date as PayoutDate
        'Pending' -- Default status
    );
END$$

DELIMITER ;

DELIMITER $$
CREATE TRIGGER AfterAssessmentUpdate
AFTER UPDATE ON Assessments
FOR EACH ROW
BEGIN
    -- Update the payout status based on the assessment result
    IF NEW.Result = 'Approved' THEN
        UPDATE Payouts
        SET Status = 'Approved'
        WHERE ContractID = NEW.ContractID AND Amount = NEW.ClaimAmount;
    ELSEIF NEW.Result = 'Rejected' THEN
        UPDATE Payouts
        SET Status = 'Rejected'
        WHERE ContractID = NEW.ContractID AND Amount = NEW.ClaimAmount;
    END IF;
END$$

DELIMITER ;

DELIMITER $$

CREATE TRIGGER BeforeContractInsert
BEFORE INSERT ON InsuranceContracts
FOR EACH ROW
BEGIN
    -- Calculate the expiration date as one year from the sign date
    SET NEW.ExpirationDate = DATE_ADD(NEW.SignDate, INTERVAL 1 YEAR);
    -- Set the status based on the expiration date
    IF NEW.ExpirationDate > CURDATE() THEN
        SET NEW.Status = 'Active';
    ELSE
        SET NEW.Status = 'Expired';
    END IF;
END$$

DELIMITER ;

DELIMITER $$
-- Create Trigger to Automatically change the status of a contract to 'Expired' after one year
CREATE EVENT ExpireContractsEvent
ON SCHEDULE EVERY 1 DAY
DO
BEGIN
    UPDATE InsuranceContracts
    SET Status = 'Expired'
    WHERE ExpirationDate < CURDATE() AND Status = 'Active';
END$$

DELIMITER ;

DELIMITER $$

CREATE TRIGGER BeforeContractUpdate
BEFORE UPDATE ON InsuranceContracts
FOR EACH ROW
BEGIN
    -- Check if we're explicitly setting an expiration date (for contract extension)
    IF NEW.ExpirationDate != OLD.ExpirationDate THEN
        -- This is likely a contract extension, so keep the user-specified expiration date
        -- Only update the status based on the new expiration date
        IF NEW.ExpirationDate > CURDATE() THEN
            SET NEW.Status = 'Active';
        ELSE
            SET NEW.Status = 'Expired';
        END IF;
    ELSE
        -- Regular update (not extending the contract)
        -- Calculate the expiration date as one year from the sign date
        SET NEW.ExpirationDate = DATE_ADD(NEW.SignDate, INTERVAL 1 YEAR);
        
        -- Update the status based on the new expiration date
        IF NEW.ExpirationDate > CURDATE() THEN
            SET NEW.Status = 'Active';
        ELSE
            SET NEW.Status = 'Expired';
        END IF;
    END IF;
END$$

DELIMITER ;

DROP PROCEDURE IF EXISTS CreateContract;
-- Create contract for a customer
DELIMITER $$
CREATE PROCEDURE CreateContract (
    IN p_ContractID VARCHAR(10),
    IN p_CustomerID VARCHAR(10),
    IN p_InsuranceTypeID VARCHAR(10),
    IN p_SignDate DATE,
    IN p_ExpirationDate DATE
)
BEGIN
    INSERT INTO InsuranceContracts (
        ContractID, CustomerID, InsuranceTypeID, SignDate, ExpirationDate, Status
    )
    VALUES (
        p_ContractID, p_CustomerID, p_InsuranceTypeID, p_SignDate, p_ExpirationDate, 'Active'
    );
END$$
DELIMITER ;

-- -- Calculate Claim Success Rate of a customer
-- DELIMITER $$
-- CREATE FUNCTION CalculateClaimSuccessRate(customerID VARCHAR(10))
-- RETURNS DECIMAL(5,2)
-- DETERMINISTIC
-- BEGIN
--     DECLARE totalClaims INT;
--     DECLARE approvedClaims INT;
--     DECLARE successRate DECIMAL(5,2);


--     SELECT COUNT(*) INTO totalClaims
--     FROM Assessments a
--     JOIN InsuranceContracts c ON a.ContractID = c.ContractID
--     WHERE c.CustomerID = customerID;


--     SELECT COUNT(*) INTO approvedClaims
--     FROM Assessments a
--     JOIN InsuranceContracts c ON a.ContractID = c.ContractID
--     WHERE c.CustomerID = customerID AND a.Result = 'Approved';

--     IF totalClaims = 0 THEN
--         SET successRate = 0.00;
--     ELSE
--         SET successRate = (approvedClaims / totalClaims) * 100;
--     END IF;


--     RETURN successRate;
-- END$$
-- DELIMITER ;

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

-- INSERT INTO Payouts (PayoutID, ContractID, Amount, PayoutDate, Status) VALUES
-- ('P001', 'CT001', 5000.00, '2024-06-15', 'Approved'),
-- ('P002', 'CT003', 20000.00, '2024-05-20', 'Rejected'),
-- ('P003', 'CT004', 150000.00, '2024-07-01', 'Approved'),
-- ('P004', 'CT001', 800.00, '2025-01-10', 'Pending'),
-- ('P005', 'CT002', 0.00, '2024-04-20', 'Rejected');