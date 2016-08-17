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
from lib.mailChainSMTP import MailChainSMTP

class sendMail(threading.Thread):
	def __init__(self, config = None, db = None):
		self.log = logging.getLogger()
		self.log.debug("Init sendMail Controll Thread")
		threading.Thread.__init__(self)
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
	def run(self):
		while(True):
			self.log.debug("SendMails")
			self.cur.execute("SELECT * FROM `outgoing` WHERE `status` = 'toSent'")
			res = self.cur.fetchall()
			for mail in res:
				try:
					self.log.debug("Send Mail #"+str(mail[0]))
					domain = mail[1][mail[1].find("@")+1:]
					self.log.debug("Domain: "+domain)
					mailserver = dns.resolver.query(domain, 'MX')
					self.log.debug("Mailserver: "+str(mailserver[0].exchange))
					smtpObj = MailChainSMTP(str(mailserver[0].exchange))
					smtpObj.set_debuglevel(1)
					try:
						res = smtpObj.sendmail(mail[2], mail[1], mail[4])
						self.cur.execute("UPDATE `mail2`.`outgoing` SET `status` = 'sent' WHERE `outgoing`.`id` = "+str(int(mail[0]))+";")
					except:
						errorStr = traceback.format_exc()
						self.sendMail(mail[2], "Mail cant send", "Sorry, this is a beta function and it dont work!!\r\n\r\n"+errorStr)
						self.cur.execute("UPDATE `mail2`.`outgoing` SET `status` = 'error' WHERE `outgoing`.`id` = "+str(int(mail[0]))+";")
						self.cur.execute("INSERT INTO `sendMailLog`(`mailID`, `log`) VALUES (%s, %s)", (int(mail[0]), errorStr))
						self.log.info("Mail can not send")
					finally:
						log = smtpObj.getLog();
						logStr = ""
						for l in log:
							logStr += l+"\r\n"
						self.cur.execute("INSERT INTO `sendMailLog`(`mailID`, `log`) VALUES (%s, %s)", (int(mail[0]), logStr))
						self.log.debug("Mail Send")

				except:
					errorStr = traceback.format_exc()
					self.log.error("Mail Send failed!")
					self.log.error(errorStr)
					self.cur.execute("INSERT INTO `sendMailLog`(`mailID`, `log`) VALUES (%s, %s)", (int(mail[0]), errorStr))
					self.cur.execute("UPDATE `mail2`.`outgoing` SET `status` = 'error' WHERE `outgoing`.`id` = "+str(int(mail[0]))+";")
					self.log.debug("Mail Send")

			self.db.commit()
			time.sleep(int(self.config.get('sendMail', 'loopTime')))
