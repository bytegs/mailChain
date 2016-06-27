import smtplib
class MailChainSMTP(smtplib.SMTP):
	def __init__(self, mailserver):
		smtplib.SMTP.__init__(self, mailserver)
		self.log = []

	def _print_debug(self, *args):
		logStr = s = "{}".format(args)
		self.log.append(logStr)

	def getLog(self):
		return self.log
