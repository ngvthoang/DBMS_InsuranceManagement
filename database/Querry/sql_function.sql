USE DATABASE prj_insurance;

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
    -- Change the status to 'Active' if the ExpirationDate is in the future
    IF NEW.ExpirationDate > CURDATE() THEN
        SET NEW.Status = 'Active';
    ELSE
        SET NEW.Status = 'Expired';
    END IF;
END$$

DELIMITER ;