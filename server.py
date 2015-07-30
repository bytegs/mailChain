from inbox import Inbox
import MySQLdb as mdb
from smtplib import SMTP
import requests
import ConfigParser, os
import re

inbox = Inbox()

@inbox.collate
def handle(to, sender, subject, body):
    print("Incomming Mail")
    print("From: %s" % sender)
    print("TO: %s" % to)
    print("Subject: %s" % subject)
    config = ConfigParser.RawConfigParser()
    config.read('defaults.cfg')
    #print(config.get('MYSQL', 'host', "localhost"))
    print("Get Chains")
    con = mdb.connect(config.get('MYSQL', 'host'), config.get('MYSQL', 'user'), config.get('MYSQL', 'pass'), config.get('MYSQL', 'db'));
    cur = con.cursor()
    cur.execute("SELECT * FROM `mailChain` ORDER BY `mailChain`.`prio` ASC")
    chains = cur.fetchall()
    send = False
    for rule in chains:
        if send == True:
            continue
        check = True
        #Check From
        if rule[2] != None and re.match(rule[2], sender) is None:
            check = False
        #Check To
        oneToFails = False
        oneToMatch = False
        for mail in to:
            if rule[3] != None and re.match(rule[3], mail) is None:
                oneToFails = True
            elif rule[3] != None and re.match(rule[3], mail) is not None:
                oneToMatch = True
        if rule[4] == True and oneToFails == True:
            check = False
        elif rule[4] == False and oneToMatch == False:
            check = False
        #Check Subject
        if rule[5] != None and re.match(rule[5], subject) is None:
            check = False
        print("Chain %s is %s" % ((rule[0]), (check)))
        if check == True:
            send = True
            if rule[6] != None:
                print("Send SMTP")
                smtp = SMTP()
                if rule[7] == None:
                    rule[7] = 25
                smtp.connect(rule[6], rule[7])
                if rule[8] != None and rule[9] != None:
                    smtp.login(rule[8], rule[9])
                smtp.sendmail(sender, to, body)
                smtp.quit()
            if rule[10] != None:
                print("Make HTTP Call")
                payload = {'to': to, 'sender': sender, 'subject': subject, 'body': body}
                r = requests.post(rule[10], data=payload)
        #print(rule)
    #print(ver)
    #print "Database version : %s " % ver

# Bind directly.
inbox.serve(address='0.0.0.0', port=4467)
