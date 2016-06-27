ALTER TABLE `mailChain` ADD `sentDirect` BOOLEAN NOT NULL DEFAULT FALSE AFTER `removeAuthenticatedSender`;
ALTER TABLE `mailLog` ADD `outgoingID` INT(255) NOT NULL AFTER `sendDate`, ADD INDEX (`outgoingID`);
