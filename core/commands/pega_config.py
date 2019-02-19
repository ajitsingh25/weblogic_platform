import common.assertions as assertions

execfile('wlst/common.py')

def run(cfg):
	#""""""
	assertions.sanityCheckInstall(cfg)
	assertions.sanityCheckDomainConfig(cfg)
	assertions.sanityCheckOnlineConfig(cfg)
	if wlst_support:
		createPegaConfig(cfg)
	else:
		raise Exception('WLST support required for this command')

def createPegaConfig(cfg):
	try:
		connectAdminServerOverSSL(cfg)
	except Exception, error:
		print 'unable to connect Admin'

	try:
		__pegaConfig(cfg)
	except Exception, error:
		print 'Unable to create PEGA Config : ' + str(error)