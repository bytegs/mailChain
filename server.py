from inbox import Inbox
import MySQLdb as mdb
from smtplib import SMTP
import requests
import ConfigParser, os
import re
import datetime

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
    if config.get('Mail', 'dump'):
        if not os.path.exists("./mails"):
            os.makedirs("./mails")
        if not os.path.exists("./mails/%s" % sender):
            os.makedirs("./mails/%s" % sender)
        d = datetime.datetime.now()
        fp = open("./mails/%s/%s_%s.txt" % (sender, d.strftime("%y_%m_%d_%H_%M_%S"), subject), "w")
        fp.write(body)
        fp.close()
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
            #Send Mail
            send = True
            tosend = True
            #log
            asender = re.findall(r'\(Authenticated\ssender\:\s{0,10}([^)]*)\)\n\s*', body)
            if config.get('Mail', 'sendLog'):
                if(len(asender)>0):
                    asender = asender[0]
                else:
                    asender = None
                for t in to:
                    sql = "INSERT INTO `mailLog`(`from`, `to`, `authenticatedSender`, `subject`) VALUES ('%s', '%s', '%s', '%s')" % (sender, t, asender, subject)
                    cur.execute(sql)
                con.commit()
            #Do Stuff with Mail
            #Remove Authenticated sender
            if rule[11] == True:
                body = re.sub(r'\(Authenticated\ssender\:\s[^)]*\)\n\s*', '', body)
            if config.get('Mail', 'addReceived'):
                start = body.find("Received")
                receivedmsg = "Received: mailChain ("+config.get('Mail', 'ReceivedName')+") #"+str(rule[0])+"\r\n"
                body = body[0:start] + receivedmsg + body[start:]
            #Check Authenticated Header
            if config.get('Mail', 'mailAuthenticatedSender'):
                con = mdb.connect(config.get('MYSQL', 'host'), config.get('MYSQL', 'user'), config.get('MYSQL', 'pass'), config.get('MYSQL', 'db'));
                cur = con.cursor()
                cur.execute('SELECT * FROM `mailAuthenticatedSender` WHERE `from` = "%s"' % sender)
                asenderregex = cur.fetchone()
                print asenderregex
                if asenderregex != None and re.match(asenderregex[2], asender) is None:
                    print("Asender FAILED!!!!!")
                    msg = ("From: %s\r\nSubject: Mail Authenticated Sender Fails\r\nTo: %s\r\n\r\n" % (config.get('SendAbuse', 'from'), ", ".join([sender])))
                    msg = msg + "Mail from %s send from Authenticated Sender %s\r\n\r\nMail don't send, please check the Config or Contact your Mail-Server-Admin per E-Mail to %s" % (sender, asender, config.get('SendAbuse', 'from'))
                    #handle(sender, "abuse@byte.gs", "Mail Authenticated Sender Fails", msg)
                    smtp = SMTP()
                    smtp.connect(config.get('SendAbuse', 'server'), config.get('SendAbuse', 'port'))
                    smtp.login(config.get('SendAbuse', 'user'), config.get('SendAbuse', 'pass'))
                    smtp.sendmail(config.get('SendAbuse', 'from'), [sender], msg)
                    smtp.quit()
                    tosend = False
            if tosend == True:
                if rule[6] != None:
                    print("Send SMTP")
                    smtp = SMTP()
                    port = 25
                    if rule[7] != None:
                        port = int(rule[7])
                    smtp.connect(str(rule[6]), int(port))
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
inbox.serve(address='127.0.0.1', port=4467)
