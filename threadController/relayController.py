import threading
import logging
from inbox import Inbox

inbox = Inbox()

class relayController(threading.Thread):
	def __init__(self):
		self.log = logging.getLogger()
		self.log.debug("Init relay Controll Thread")
		threading.Thread.__init__(self)

	def run(self):
		self.log.debug("Run rely Controll Thread")
		inbox.serve(address='127.0.0.1', port=4467)

	@inbox.collate
	def handle(to, sender, subject, body):
		log = logging.getLogger()
		log.info("Incomming Mail")
		return "550 - Oups"
