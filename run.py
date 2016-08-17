#!/usr/bin/python3
from threadController.relayController import relayController
from threadController.sendMail import sendMail
import logging
import time
import configparser
import os
import pymysql


logger = logging.getLogger()
handler = logging.StreamHandler()
formatter = logging.Formatter('%(asctime) 12s %(levelname)-8s %(message)s')
handler.setFormatter(formatter)
logger.addHandler(handler)
logger.setLevel(logging.DEBUG)

logger.info("Start")
logger.debug("Try to find "+os.path.dirname(os.path.realpath(__file__))+"/config/defaults.cfg")
if os.path.isfile(os.path.dirname(os.path.realpath(__file__))+"/config/defaults.cfg") == False:
	logger.error("Config file not found")
	raise Exception("Config not found")

config = configparser.RawConfigParser()
config.read(os.path.dirname(os.path.realpath(__file__))+'/config/defaults.cfg')

logger.debug("Check MYSQL Connection")
db = pymysql.connect(host=config.get('MYSQL', 'host'), user=config.get('MYSQL', 'user'), passwd=config.get('MYSQL', 'pass'), db=config.get('MYSQL', 'db'))
die
t = relayController()
t.start()
if(config.get('sendMail', 'enabled')=="True"):
	m = sendMail()
	m.start()
	m.join()
t.join()
print("Main script Stops!")
