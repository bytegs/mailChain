# mailChain
Mailchain is a Python Script that create a SMTP-Relay Server and decides based on some Rules from a MYSQL Database which whey the E-Mail go (another SMTP Server or a HTTP Call).

It creates a new MYSQL-Connection (and Query) for each Mail, so it always have the newest Version but it take some time (and load)

## Functions
### Basic Functions
* Open SMTP-Relay Server
* Check Mail agains Rule to decide which SMTP-Relay or HTTP Call used to forward to

### Posible Rules in on Chain
* Check if From or Subject Match a RegEx (From MYSQL)
* Check if one or all to Header Match a RegEx (From MYSQL)

### Extra Rules
* Check if AuthenticatedSende in Mail Header Match a Regex (From MYSQL)

### Modify E-Mail
* Remove AuthenticatedSende from Header bevor forward it
* Add a Received Header to the Mail (Include a Name and the Chain-ID)

### Forward a Mail
* (Re)send Abuse Message to Sender (if AuthenticatedSende is required and wrong)
* Send Mail to another SMTP-Relay
* Make a HTTP Call with the Mail Content in a POST Request
* Log Mail (To, From, Subject, AuthenticatedSende, Timestamp) to a MYSQL Database to detect Spaming

## Config File
The Basic Config File contains the MYSQL Connection and some Basic Config.
```
[MYSQL]
host:localhost
user:root
pass:
db:mailChain

[Mail]
dump:False
addReceived:True
ReceivedName:Default
sendLog:True
mailAuthenticatedSender:True

[SendAbuse]
from:
server:
port:
user:
pass:
```
### MYSQL
*  host -> Contains the MYSQL Host
*  user -> Contains the MYSQL User
*  pass -> Contains the MYSQL Password
*  db -> Contains the MYSQL Database Name

### Mail
* dump -> If it "True" all Mails are dump to the Database before Modified
* addReceived -> If it "True" a "Received" Entry to the Mail Header
* ReceivedName -> Contains the Name to Add in the "Received" Entry
* sendLog -> If it is True, all outgoing Mails log in a MYSQL Database
* mailAuthenticatedSender -> If it is "True" outgoing Mails Check if a AuthenticatedSender is required and if it match

### SendAbuse
If the Script have to send a abused Message (e.g. if the AuthenticatedSender don't match) it use the SMTP-Setting of this Section to send it.

## Installation
Do the following Steps:
### Set up the Database
Create the Database Structure from the mysql.sql File and create a new MYSQL User

### Clone the Project and Config it
Clone the Project and change the defaults.cfg to your Settings. Than run the server, install all needet dependencies. Than Start the server.py

### Config Postfiy
Let Postfiy relay all Mails ofter 127.0.0.1:4467

### Add a Default Rule in your Chain
```
INSERT INTO `mailChain` (prio`, `from`, `to`, `allTo`, `subject`, `smtpServer`, `smtpPort`, `smtpUser`, `smtpPass`, `httpCall`, `removeAuthenticatedSender`) VALUES
(100000, NULL, NULL, 1, NULL, 'smtp-relay.server', NULL, NULL, NULL, NULL, 1);
```
