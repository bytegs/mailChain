ALTER TABLE `mailChain` ADD `sentDirect` BOOLEAN NOT NULL DEFAULT FALSE AFTER `removeAuthenticatedSender`;
ALTER TABLE `mailLog` ADD `outgoingID` INT(255) NOT NULL AFTER `sendDate`, ADD INDEX (`outgoingID`);

CREATE TABLE IF NOT EXISTS `sendMailLog` (
  `id` int(255) NOT NULL,
  `mailID` int(255) NOT NULL,
  `log` longtext NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=latin1;

ALTER TABLE `sendMailLog`
  ADD UNIQUE KEY `id` (`id`);

ALTER TABLE `sendMailLog`
  MODIFY `id` int(255) NOT NULL AUTO_INCREMENT;

CREATE TABLE IF NOT EXISTS `outgoing` (
  `id` int(255) NOT NULL,
  `to` varchar(255) NOT NULL,
  `sender` varchar(255) NOT NULL,
  `orginalbody` longtext NOT NULL,
  `body` longtext NOT NULL,
  `createtime` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `status` enum('incommed','delivered','toSent','sent','error') NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=latin1;

ALTER TABLE `outgoing`
  ADD UNIQUE KEY `id` (`id`);

ALTER TABLE `outgoing`
  MODIFY `id` int(255) NOT NULL AUTO_INCREMENT;
