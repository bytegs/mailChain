#!/usr/bin/python
from inbox import Inbox
import MySQLdb as mdb
from smtplib import SMTP
import requests
from backports import configparser as ConfigParser
import os
#import ConfigParser, os
import re
import datetime
import sys
import hashlib
from sender import Mail, Message
import time

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
    pLog("Check Authenticated Sender")
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
        msg = "Mail from %s send from Authenticated Sender %s\r\n\r\nThe Mail Header must match!\r\nMail don't send, please check the Config or Contact your Mail-Server-Admin per E-Mail to %s" % (sender, asender, config.get('SendAbuse', 'from'))
        sendMail(sender, "Mail from "+sender+" with wrong Authenticated Sender Header", msg)
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
    m = hashlib.md5()
    m.update("%s_%s" % (d.strftime("%y_%m_%d_%H_%M_%S"), subject))
    fp = open("./mails/%s/%s.txt" % (sender, str(m.hexdigest())), "w")
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

def runBasic(to, sender, subject, body):
    pLog("Incoming mail from %s" % sender)
    #Read Config
    config = ConfigParser.RawConfigParser()
    config.read('defaults.cfg')
    #Dump Mail to File System
    if config.get('Mail', 'dump') == True:
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
                pLog("Check Authentication Sender for %s" % sender)
                cur.execute('SELECT * FROM `mailAuthenticatedSender` WHERE `from` = "%s"' % sender)
                asenderregex = cur.fetchone()
                if asenderregex != None:
                    retAuth = checkAuthenticatedSender(sender, body, str(asenderregex[2]))
                    if retAuth == False:
                        tosend = False
                        return "503 Autoriced Header is wrong"
            #tosend = False
            if tosend == True:
                pLog("Redirect Mail")
                if config.get('Mail', 'sendLog'):
                    logMail(to, sender, subject, body, con)
                #Remove Authenticate Header:
                if rule[11] == True:
                    body = removeAuthenticatedSende(body)
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

def sendMail(to, subject, msgContext):
    pLog("Send Server Mail")
    config = ConfigParser.RawConfigParser()
    config.read('defaults.cfg')
    msg = Message(subject, fromaddr=config.get('SendAbuse', 'from'), to=to)
    if(to!=config.get('SendAbuse', 'from')):
        msg.bcc = config.get('SendAbuse', 'from')
    msg.body = msgContext
    msg.date = time.time()
    msg.charset = "utf-8"
    mail = Mail(config.get('SendAbuse', 'server'), port=config.get('SendAbuse', 'port'), username=config.get('SendAbuse', 'user'), password=config.get('SendAbuse', 'pass'),use_tls=False, use_ssl=False, debug_level=None)
    mail.send(msg)

@inbox.collate
def handle(to, sender, subject, body):
    try:
        return runBasic(to, sender, subject, body)
    except:
        pLog("Something go Wrong, Mail sendet")
        errorStr = str(sys.exc_info())
        config = ConfigParser.RawConfigParser()
        config.read('defaults.cfg')
        sendMail(sender, "Mail cant not sendet", "Hello, you try to send a Mail, we cant send this Mail because an error appear. Our Team get the Information, please try it again later!")
        sendMail(config.get('SendAbuse', 'from'), "MailChain Error", "So following error appear:\r\n\r\n"+errorStr)
        return "550 Something go wrong"

# Bind directly.
pLog("Start Server")
#sendMail("hello@kekskurse.de", "Abuse Mail", "Something go Wrong!")
inbox.serve(address='127.0.0.1', port=4467)
