import threading
import logging
from inbox import Inbox
import time
import pymysql
import configparser
from threadController.chainController import chainController
import sys

inbox = Inbox()

class relayController(threading.Thread):
	def __init__(self):
		self.log = logging.getLogger()
		self.log.debug("Init relay Controll Thread")
		threading.Thread.__init__(self)
		self.config = configparser.RawConfigParser()
		self.config.read('config/defaults.cfg')

	def run(self):
		self.log.debug("Run rely Controll Thread")
		inbox.serve(address='127.0.0.1', port=4467)

	@inbox.collate
	def handle(to, sender, subject, body):
		try:
			log = logging.getLogger()
			log.info("Incomming Mail")
			# Seperate in secound thread, than i can replace it faster
			t = chainController(to, sender, subject, body)
			t.start()
			t.join()
			response = t.retMailInfo()
			if(response == None):
				response = "550 - Oups"
			return response
		except:
			log.critical("Something go terrible Wrong: "+str(sys.exc_info()))
			return "550 Server Error"
