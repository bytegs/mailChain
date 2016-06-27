from threadController.relayController import relayController
from threadController.sendMail import sendMail
import logging
import time
import configparser


logger = logging.getLogger()
handler = logging.StreamHandler()
formatter = logging.Formatter('%(asctime) 12s %(levelname)-8s %(message)s')
handler.setFormatter(formatter)
logger.addHandler(handler)
logger.setLevel(logging.DEBUG)

config = configparser.RawConfigParser()
config.read('defaults.cfg')


t = relayController()
t.start()
if(config.get('sendMail', 'enabled')=="True"):
	m = sendMail()
	m.start()
	m.join()
t.join()
print("Main script Stops!")
