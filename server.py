from inbox import Inbox
import MySQLdb as mdb
from smtplib import SMTP
import requests
import ConfigParser, os
import re
import datetime
import sys

inbox = Inbox()

def checkChain(rule, to, sender, subject):
    check = True #Status of this Rule
    #Check if Sender Match
    if rule[2] != None and re.match(rule[2], sender) is None:
        check = False
    #Check if To Match
    oneToFails = False #If it get True, min on to header don`t match
    oneToMatch = False #If it get True, min on to header match
    for mail in to:
        if rule[3] != None and re.match(rule[3], mail) is None:
            oneToFails = True
        elif rule[3] != None and re.match(rule[3], mail) is not None:
            oneToMatch = True
    if rule[4] == True and oneToFails == True: #Rules says all to header must match but they dont do
        check = False
    elif rule[4] == False and oneToMatch == False: #Rules say min one to header must match but no to header matchs
        check = False
    #Check Subject
    if rule[5] != None and re.match(rule[5], subject) is None:
        check = False
    return check

def checkAuthenticatedSender(sender, body, asenderRegEx):
    #print(asenderRegEx)
    asender = re.findall(r'\(Authenticated\ssender\:\s{0,10}([^)]*)\)\n\s*', body)
    if(len(asender)>0):
        asender = asender[0]
    else:
        asender = None
    if asenderRegEx != None and re.match(asenderRegEx, str(asender)) is None:
        pLog("AuthenticatedSender is required but failed")
        #Send Abuse Mail
        config = ConfigParser.RawConfigParser()
        config.read('defaults.cfg')
        msg = ("From: %s\r\nSubject: Mail Authenticated Sender Fails\r\nTo: %s\r\n\r\n" % (config.get('SendAbuse', 'from'), ", ".join([sender])))
        msg = msg + "Mail from %s send from Authenticated Sender %s\r\n\r\nMail don't send, please check the Config or Contact your Mail-Server-Admin per E-Mail to %s" % (sender, asender, config.get('SendAbuse', 'from'))
        smtp = SMTP()
        smtp.connect(config.get('SendAbuse', 'server'), config.get('SendAbuse', 'port'))
        smtp.login(config.get('SendAbuse', 'user'), config.get('SendAbuse', 'pass'))
        smtp.sendmail(config.get('SendAbuse', 'from'), [sender], msg)
        smtp.quit()
        pLog("AuthenticatedSender %s dont match on %s" % (asender, asenderRegEx))
        return False
    pLog("AuthenticatedSender Match")
    return True

def dumpMail(to, sender, subject, body):
    if not os.path.exists("./mails"):
        os.makedirs("./mails")
    if not os.path.exists("./mails/%s" % sender):
        os.makedirs("./mails/%s" % sender)
    d = datetime.datetime.now()
    fp = open("./mails/%s/%s_%s.txt" % (sender, d.strftime("%y_%m_%d_%H_%M_%S"), subject), "w")
    fp.write(body)
    fp.close()
    pLog("Dump Mail to File System")

def logMail(to, sender, subject, body, con):
    asender = re.findall(r'\(Authenticated\ssender\:\s{0,10}([^)]*)\)\n\s*', body)
    cur = con.cursor()
    if(len(asender)>0):
        asender = asender[0]
    else:
        asender = None
    for t in to:
        sql = "INSERT INTO `mailLog`(`from`, `to`, `authenticatedSender`, `subject`) VALUES ('%s', '%s', '%s', '%s')" % (sender, t, asender, subject)
        cur.execute(sql)
    con.commit()
    pLog("Mail Logged in DB")

def removeAuthenticatedSende(body):
    body = re.sub(r'\(Authenticated\ssender\:\s[^)]*\)\n\s*', '', body)
    pLog("Remove Authenticated Sende from Mail Head")
    return body

def pLog(msg):
    d = datetime.datetime.now()
    print("[%s] %s" % (d.strftime("%y-%m-%d %H:%M:%S"), msg))

def addReceived(body, ruleId):
    config = ConfigParser.RawConfigParser()
    config.read('defaults.cfg')
    start = body.find("Received")
    receivedmsg = "Received: mailChain ("+config.get('Mail', 'ReceivedName')+") #"+str(ruleId)+"\r\n"
    body = body[0:start] + receivedmsg + body[start:]
    pLog("Add Received Header to Mail")
    return body

@inbox.collate
def handle(to, sender, subject, body):
    pLog("Incoming mail from %s" % sender)
    #Read Config
    config = ConfigParser.RawConfigParser()
    config.read('defaults.cfg')
    #Dump Mail to File System
    if config.get('Mail', 'dump'):
        dumpMail(to, sender, subject, body)
    #Connect to Database
    try:
        con = mdb.connect(config.get('MYSQL', 'host'), config.get('MYSQL', 'user'), config.get('MYSQL', 'pass'), config.get('MYSQL', 'db'));
        cur = con.cursor()
    except:
        pLog("FATAL!!! MYSQL Connection cant create, can`t run without MYSQL")
        pLog(str(sys.exc_info()))
        sys.exit()
    #Get Rules
    cur.execute("SELECT * FROM `mailChain` ORDER BY `mailChain`.`prio` ASC")
    chains = cur.fetchall()
    send = False
    for rule in chains:
        if send == True:
            continue
        check = checkChain(rule, to, sender, subject)
        pLog("Chain %s is %s" % ((rule[0]), (check)))
        if check == True:
            #Send Mail
            send = True     #Mail alwady send
            tosend = True   #Send Mail?

            #Do Stuff with Mail
            #Add Received Header to Mail
            if config.get('Mail', 'addReceived'):
                body = addReceived(body, rule[0])
            #Check Authenticated Header
            if config.get('Mail', 'mailAuthenticatedSender'):
                cur.execute('SELECT * FROM `mailAuthenticatedSender` WHERE `from` = "%s"' % sender)
                asenderregex = cur.fetchone()
                if asenderregex != None:
                    tosend = checkAuthenticatedSender(sender, body, str(asenderregex[2]))
            #Remove Authenticate Header:
            if rule[11] == True:
                body = removeAuthenticatedSende(body)
            #tosend = False
            if tosend == True:
                pLog("Redirect Mail")
                if config.get('Mail', 'sendLog'):
                    logMail(to, sender, subject, body, con)
                if rule[6] != None:
                    pLog("Send Mail ofer SMTP Relay %s" % rule[6])
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
                    pLog("Make HTTP Call to %s" % rule[10])
                    payload = {'to': to, 'sender': sender, 'subject': subject, 'body': body}
                    r = requests.post(rule[10], data=payload)

# Bind directly.
pLog("Start Server")
inbox.serve(address='127.0.0.1', port=4467)
