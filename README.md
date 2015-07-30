# mailChain
Mailchain is a Python Script that create a SMTP-Relay Server and decides based on some Rules from a MYSQL Database which whey the E-Mail go (another SMTP Server or a HTTP Call).

It creates a new MYSQL-Connection (and Query) for each Mail, so it always have the newest Version but it take some time (and load)
