import threading
import time
import logging
import pymysql
import configparser
import dns.resolver
import smtplib
import sys
import tempfile
import uuid
import urllib.request
import traceback

class sendMail(threading.Thread):
	def __init__(self, config = None, db = None):
		self.log = logging.getLogger()
		self.log.debug("Init sendMail Controll Thread")
		threading.Thread.__init__(self)
		if(config == None):
			self.config = configparser.RawConfigParser()
			self.config.read('defaults.cfg')
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

	def run(self):
		while(True):
			self.log.debug("SendMails")
			self.cur.execute("SELECT * FROM `outgoing` WHERE `status` = 'toSent'")
			res = self.cur.fetchall()
			for mail in res:
				orig_std = (sys.stdout, sys.stderr)
				filename = tempfile.gettempdir()+"/"+str(uuid.uuid1())
				try:
					self.log.debug("Send Mail #"+str(mail[0]))
					domain = mail[1][mail[1].find("@")+1:]
					self.log.debug("Domain: "+domain)
					mailserver = dns.resolver.query(domain, 'MX')
					self.log.debug("Mailserver: "+str(mailserver[0].exchange))
					self.log.debug("Log filename: "+filename)
					sys.stdout = sys.stderr = open(filename, "a")
					smtpObj = smtplib.SMTP(str(mailserver[0].exchange))
					smtpObj.set_debuglevel(1)
					res = smtpObj.sendmail(mail[2], mail[1], mail[4])
					sys.stdout, sys.stderr = orig_std
					mailLog = urllib.request.urlopen("file://"+filename).read()
					#INSERT INTO `sendMailLog`(`mailID`, `log`) VALUES ()
					self.cur.execute("UPDATE `mail2`.`outgoing` SET `status` = 'sent' WHERE `outgoing`.`id` = "+str(int(mail[0]))+";")
					self.cur.execute("INSERT INTO `sendMailLog`(`mailID`, `log`) VALUES (%s, %s)", (int(mail[0]), mailLog))
					self.log.debug("Mail Send")
				except:
					errorStr = traceback.format_exc()
					self.log.error("Mail Send failed!")
					mailLog = urllib.request.urlopen("file://"+filename).read()
					sys.stdout, sys.stderr = orig_std
					self.cur.execute("INSERT INTO `sendMailLog`(`mailID`, `log`) VALUES (%s, %s)", (int(mail[0]), mailLog))
					self.cur.execute("INSERT INTO `sendMailLog`(`mailID`, `log`) VALUES (%s, %s)", (int(mail[0]), errorStr))
					self.cur.execute("UPDATE `mail2`.`outgoing` SET `status` = 'error' WHERE `outgoing`.`id` = "+str(int(mail[0]))+";")
					self.log.debug("Mail Send")
				#print(mail)

			self.db.commit()
			time.sleep(int(self.config.get('sendMail', 'loopTime')))
