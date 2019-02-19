import common.assertions as assertions

execfile('wlst/common.py')
execfile('wlst/configureNodeManagerSSL.py')

def run(cfg):
	"""Configure Node Manager with PKI"""
	assertions.sanityCheckInstall(cfg)
	assertions.sanityCheckDomainConfig(cfg)
	assertions.sanityCheckOnlineConfig(cfg)
	if wlst_support:
		configureNMSSL(cfg)
	else:
		raise Exception('WLST support required for this command')

def configureNMSSL(cfg):
#	try:
#		connectAdminServerOverSSL(cfg)
#	except Exception, error:
#		print 'unable to connect Admin'
	try:
		configureNodeManagerSSL(cfg)
	except Exception, error:
		print 'Unable to configure NodeManager SSL : ' + str(error)
