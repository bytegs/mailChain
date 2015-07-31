# mailChain
Mailchain is a Python Script that create a SMTP-Relay Server and decides based on some Rules from a MYSQL Database which whey the E-Mail go (another SMTP Server or a HTTP Call).

It creates a new MYSQL-Connection (and Query) for each Mail, so it always have the newest Version but it take some time (and load)

#Functions
* Open SMTP-Relay Server
* Check Mail agains Rule to decide which SMTP-Relay or HTTP Call used to forward to

#Posible Rules in on Chain
* Check if From or Subject Match a RegEx (From MYSQL)
* Check if one or all to Header Match a RegEx (From MYSQL)

#Extra Rules
* Check if AuthenticatedSende in Mail Header Match a Regex (From MYSQL)

#Modify E-Mail
* Remove AuthenticatedSende from Header bevor forward it
* Add a Received Header to the Mail (Include a Name and the Chain-ID)

#Forward a Mail
* (Re)send Abuse Message to Sender (if AuthenticatedSende is required and wrong)
* Send Mail to another SMTP-Relay
* Make a HTTP Call with the Mail Content in a POST Request
