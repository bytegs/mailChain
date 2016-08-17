-- phpMyAdmin SQL Dump
-- version 4.4.4
-- http://www.phpmyadmin.net
--
-- Host: 46.101.168.205:3306
-- Generation Time: Jul 31, 2015 at 01:57 PM
-- Server version: 5.5.41-0ubuntu0.14.04.1
-- PHP Version: 5.6.11

SET SQL_MODE = "NO_AUTO_VALUE_ON_ZERO";
SET time_zone = "+00:00";

--
-- Database: `cp2`
--

-- --------------------------------------------------------

--
-- Table structure for table `mailAuthenticatedSender`
--

CREATE TABLE IF NOT EXISTS `mailAuthenticatedSender` (
  `id` int(255) NOT NULL,
  `from` varchar(255) NOT NULL,
  `authenticatedSender` varchar(255) NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=latin1;

-- --------------------------------------------------------

--
-- Table structure for table `mailChain`
--

CREATE TABLE IF NOT EXISTS `mailChain` (
  `id` int(255) NOT NULL,
  `prio` int(255) NOT NULL,
  `from` varchar(255) DEFAULT NULL,
  `to` varchar(255) DEFAULT NULL,
  `allTo` tinyint(1) NOT NULL DEFAULT '1' COMMENT 'to must match on all to mails',
  `subject` varchar(255) DEFAULT NULL,
  `smtpServer` varchar(255) DEFAULT NULL,
  `smtpPort` int(255) DEFAULT NULL,
  `smtpUser` varchar(255) DEFAULT NULL,
  `smtpPass` varchar(255) DEFAULT NULL,
  `httpCall` varchar(255) DEFAULT NULL,
  `removeAuthenticatedSender` tinyint(1) NOT NULL DEFAULT '1' COMMENT 'Remove Authenticated sender from Header bevor redirect'
) ENGINE=InnoDB DEFAULT CHARSET=latin1;

-- --------------------------------------------------------

--
-- Table structure for table `mailLog`
--

CREATE TABLE IF NOT EXISTS `mailLog` (
  `id` int(255) NOT NULL,
  `from` varchar(255) NOT NULL,
  `to` text NOT NULL,
  `authenticatedSender` varchar(255) DEFAULT NULL,
  `subject` text NOT NULL,
  `sendDate` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=latin1;

--
-- Indexes for dumped tables
--

--
-- Indexes for table `mailAuthenticatedSender`
--
ALTER TABLE `mailAuthenticatedSender`
  ADD UNIQUE KEY `id` (`id`);

--
-- Indexes for table `mailChain`
--
ALTER TABLE `mailChain`
  ADD UNIQUE KEY `id` (`id`);

--
-- Indexes for table `mailLog`
--
ALTER TABLE `mailLog`
  ADD UNIQUE KEY `id` (`id`);

--
-- AUTO_INCREMENT for dumped tables
--

--
-- AUTO_INCREMENT for table `mailAuthenticatedSender`
--
ALTER TABLE `mailAuthenticatedSender`
  MODIFY `id` int(255) NOT NULL AUTO_INCREMENT;
--
-- AUTO_INCREMENT for table `mailChain`
--
ALTER TABLE `mailChain`
  MODIFY `id` int(255) NOT NULL AUTO_INCREMENT;
--
-- AUTO_INCREMENT for table `mailLog`
--
ALTER TABLE `mailLog`
  MODIFY `id` int(255) NOT NULL AUTO_INCREMENT;
