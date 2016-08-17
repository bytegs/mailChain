import threading
import logging
import configparser
import pymysql
import sys
from smtplib import SMTP
from sender import Mail, Message, Attachment
import requests
import re
import time
import traceback
import tempfile
import uuid
import os
from lib.mailChainSMTP import MailChainSMTP

class chainController(threading.Thread):
	def __init__(self, to, sender, subject, body, config = None, db = None):
		threading.Thread.__init__(self)
		self.to = to
		self.sender = sender
		self.subject = subject
		self.body = body
		self.messageID = None
		self.retStr = None
		self.log = logging.getLogger()
		self.log.debug("Init chain Controll Thread")
		self.mailLogId = None
		if(config == None):
			self.config = configparser.RawConfigParser()
			self.config.read('config/defaults.cfg')
		else:
			self.config = config
		if(db == None):
			try:
				self.db = pymysql.connect(host=self.config.get('MYSQL', 'host'), user=self.config.get('MYSQL', 'user'), passwd=self.config.get('MYSQL', 'pass'), db=self.config.get('MYSQL', 'db'))
			except:
				self.log.critical("MYSQL Connection can't be estaplet")
				self.setResponse("550 - Server Error")
		else:
			self.db = db
		self.cur = self.db.cursor()

	def sendMail(self, to, subject, msgContext):
		self.log.debug("Send Server Mail")
		if(self.config.get('SendAbuse', 'debug') == "True"):
			self.log.info("Debug modus, dont send Mails!")
			return False
		msg = Message(subject, fromaddr=self.config.get('SendAbuse', 'from'), to=to)
		if(to!=self.config.get('SendAbuse', 'from')):
			msg.bcc = self.config.get('SendAbuse', 'from')
		else:
			mailattachment = Attachment("orginalmail.txt", "text/plain", self.body)
			msg.attach(mailattachment)
		msg.body = msgContext
		msg.date = time.time()
		msg.charset = "utf-8"
		mail = Mail(self.config.get('SendAbuse', 'server'), port=self.config.get('SendAbuse', 'port'), username=self.config.get('SendAbuse', 'user'), password=self.config.get('SendAbuse', 'pass'),use_tls=False, use_ssl=False, debug_level=None)
		mail.send(msg)
		self.log.debug("Mail to %s sended" % to)

	def dumpMailHDD(self):
		self.log.error("dumpMail/dumpMailHDD is remved!")
		return False

	def dumpMailSQL(self):
		self.log.debug("Dump to DB")
		sql = 'INSERT INTO `outgoing`(`to`, `sender`,`orginalbody`, `body`, `status`) VALUES (%s, %s, %s, %s, "incommed")';
		self.cur.execute(sql, (self.to, self.sender, self.body, self.body))
		self.cur.execute("SELECT LAST_INSERT_ID()")
		id = self.cur.fetchone()
		self.log.info("Mail ID:"+str(id[0]))
		self.messageID = id[0]

	def retMailInfo(self):
		return self.retStr

	def addReceived(self, ruleId):
		start = self.body.find("Received")
		receivedmsg = "Received: mailChain ("+self.config.get('Mail', 'ReceivedName')+") #"+str(ruleId)+"\r\n"
		self.body = self.body[0:start] + receivedmsg + self.body[start:]
		self.log.info("Add Received Header to Mail")

	def checkAuthenticatedSender(self, asenderRegEx):
	    self.log.debug("Check Authenticated Sender")
	    asender = re.findall(r'\(Authenticated\ssender\:\s{0,10}([^)]*)\)\n\s*', self.body)
	    if(len(asender)>0):
	        asender = asender[0]
	    else:
	        asender = None
	    if asenderRegEx != None and re.match(asenderRegEx, str(asender)) is None:
	        self.log.info("AuthenticatedSender is required but failed")
	        #Send Abuse Mail
	        msg = "Mail from %s send from Authenticated Sender %s\r\n\r\nThe Mail Header must match!\r\nMail don't send, please check the Config or Contact your Mail-Server-Admin per E-Mail to %s" % (self.sender, asender, self.config.get('SendAbuse', 'from'))
	        self.sendMail(self.sender, "Mail from "+self.sender+" with wrong Authenticated Sender Header", msg)
	        self.log.debug("AuthenticatedSender %s dont match on %s" % (asender, asenderRegEx))
	        return False
	    self.log.debug("AuthenticatedSender Match")
	    return True

	def getAuthenticatedSenderCheck(self):
		self.log.debug("Get AuthenticatedSender Database")
		self.cur.execute('SELECT * FROM `mailAuthenticatedSender` WHERE `from` = "%s"' % self.sender)
		asenderregex = self.cur.fetchone()
		if asenderregex != None:
			retAuth = self.checkAuthenticatedSender(str(asenderregex[2]))
			if retAuth == False:
				self.setStatus("error")
				self.setResponse("503 Autoriced Header is wrong")
				return False
			else:
				return True

	def checkChain(self, rule):
		self.log.debug("Check Rule "+str(rule[0]))
		#Check if Sender Match
		if rule[2] != None and re.match(rule[2], self.sender) is None:
			return False
		#Check if To Match
		oneToFails = False #If it get True, min on to header don`t match
		oneToMatch = False #If it get True, min on to header match
		for mail in self.to:
			if rule[3] != None and re.match(rule[3], mail) is None:
				oneToFails = True
			elif rule[3] != None and re.match(rule[3], mail) is not None:
				oneToMatch = True
		if rule[4] == True and oneToFails == True: #Rules says all to header must match but they dont do
			return False
		elif rule[4] == False and oneToMatch == False: #Rules say min one to header must match but no to header matchs
			return False
		#Check Subject
		if rule[5] != None and re.match(rule[5], self.subject) is None:
			return False
		self.log.debug("Rule Match")
		return True

	def checkSpamc(self):
		self.log.debug("Check Spam")
		filename = tempfile.gettempdir()+"/"+str(uuid.uuid1())
		with open(filename, 'w') as f:
			f.write(self.body)
		ret = os.popen("spamc -c < %s" % filename).read()
		detais = str(ret).split("/")
		count = float(detais[0].strip())
		max = float(detais[1].strip())
		self.log.debug("Spam Score: "+ret.strip())
		if count > max:
			self.setStatus("error")
			self.setResponse("550 Spam detect")
			self.log.info("Spam Detact, reject")
			return False
		return True

	def removeAuthenticatedSende(self):
		self.body = re.sub(r'\(Authenticated\ssender\:\s[^)]*\)\n\s*', '', self.body)
		self.log.debug("Remove Authenticated Sende from Mail Head")

	def logMail(self):
		asender = re.findall(r'\(Authenticated\ssender\:\s{0,10}([^)]*)\)\n\s*', self.body)
		#cur = con.cursor()
		if(len(asender)>0):
			asender = asender[0]
		else:
			asender = None
		for t in self.to:
			#sql = "INSERT INTO `mailLog`(`from`, `to`, `authenticatedSender`, `subject`) VALUES ('%s', '%s', '%s', '%s')" % (self.sender, self.t, asender, self.subject)
			sql = "INSERT INTO `mailLog`(`from`, `to`, `authenticatedSender`, `subject`, `outgoingID`) VALUES (%s, %s, %s, %s, %s)"
			self.cur.execute(sql, (self.sender, t, asender, self.subject, self.messageID))
			if self.mailLogId == None:
				self.cur.execute("SELECT LAST_INSERT_ID()")
				id = self.cur.fetchone()
				self.mailLogId = id[0]
		self.db.commit()
		self.log.debug("Mail Logged in DB")

	def setStatus(self, status):
		if(self.config.get("Mail", "dumpSQL") == "True"):
			self.cur.execute("UPDATE `mail2`.`outgoing` SET `status` = %s WHERE `outgoing`.`id` = "+str(int(self.messageID))+";", (status))
			self.log.debug("Set Status to: "+str(status))
		else:
			self.log.error("Cant change status if dumpSQL is disabled")


	def runMain(self):
		# Dump Mail to HDD
		if self.config.get('Mail', 'dump') == "True":
			self.dumpMailHDD()
		if self.config.get("Mail", "dumpSQL") == "True":
			self.dumpMailSQL()
		# Check Auterised Sender Header
		if self.config.get('Mail', 'mailAuthenticatedSender'):
			ret = self.getAuthenticatedSenderCheck()
			if(ret == False):
				return False
		# General SpamC Check
		#print(self.config.get('Mail', 'spamc'))
		if self.config.get('Mail', 'spamc') == True or self.config.get('Mail', 'spamc') == "True":
			res = self.checkSpamc()
			if res == False:
				return False
		# Get Rules from DB
		self.cur.execute("SELECT * FROM `mailChain` ORDER BY `mailChain`.`prio` ASC")
		chains = self.cur.fetchall()
		for rule in chains:
			check = self.checkChain(rule)
			if check == True:
				# Add Recevied Header to Mail
				if self.config.get('Mail', 'addReceived'):
					self.addReceived(rule[0])
				self.logMail()
				if rule[11] == True:
					self.removeAuthenticatedSende()
				if rule[6] != None:
					self.log.info("Send via SMTP")
					smtp = MailChainSMTP()
					port = 25
					if rule[7] != None:
						port = int(rule[7])
					self.log.debug("SMTP-Server: "+str(rule[6])+":"+str(port))
					smtp.set_debuglevel(1)
					smtp.connect(str(rule[6]), int(port))

					if rule[8] != None and rule[9] != None:
						smtp.login(rule[8], rule[9])
					smtp.sendmail(self.sender, self.to, self.body)
					smtp.quit()
					log = smtp.getLog();
					logStr = ""
					for l in log:
						logStr += l+"\r\n"
					self.cur.execute("INSERT INTO `sendMailLog`(`mailID`, `log`) VALUES (%s, %s)", (int(self.mailLogId), logStr))
					self.log.debug("Mail Send")
					self.setResponse("250 OK")
					self.setStatus("delivered")
				if rule[10] != None:
					self.log.info("Make HTTP Call to %s" % rule[10])
					payload = {'to': to, 'sender': sender, 'subject': subject, 'body': body}
					r = requests.post(rule[10], data=payload)
					self.setResponse("250 OK - POST Request")
					self.setStatus("delivered")
				if rule[12] == True and rule[6] == None:
					if(self.config.get('sendMail', 'enabled')!="True"):
						self.setStatus("error")
						self.setResponse("550 - sendMail function not enabled")
					elif self.config.get("Mail", "dumpSQL") != "True":
						self.setStatus("error")
						self.setResponse("550 - enabled dumpSQL for direct Send")
					else:
						self.setStatus("toSent")
						self.setResponse("250 - sending")



				return True

	def setResponse(self, msg):
		if(self.retStr == None):
			self.retStr = str(msg)

	def run(self):
		self.log.debug("Run Mail Chain")
		try:
			self.runMain()
		except:
			errorStr = traceback.format_exc()
			self.log.critical(errorStr)
			self.sendMail(self.sender, "Mail cant not sendet", "Hello, you try to send a Mail, we cant send this Mail because an error appear. Our Team get the Information, please try it again later!")
			self.sendMail(self.config.get('SendAbuse', 'from'), "MailChain Error", "So following error appear:\r\n\r\n"+errorStr)
			self.setStatus("error")
			self.setResponse("550 - Oups")
		self.log.debug("Status: "+str(self.retStr))
		self.db.commit()
		#Mail Dump FileSystem
