# mailChain
Mailchain is a Python Script that create a SMTP-Relay Server and decides based on some Rules from a MYSQL Database which whey the E-Mail go (another SMTP Server or a HTTP Call).

It creates a new MYSQL-Connection (and Query) for each Mail, so it always have the newest Version but it take some time (and load)

It allowso allows to log some Information about the send Mail (from, to, authenticatedSender, subject, datetime) that another script can easy detect spamming accounts with some mysql querys.

It allows to check the authenticatedSender for spezieal From headers
