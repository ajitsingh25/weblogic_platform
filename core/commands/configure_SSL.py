import common.assertions as assertions

execfile('wlst/common.py')
execfile('wlst/configurePKI.py')

def run(cfg):
	"""Configure Domain PKI"""
	assertions.sanityCheckInstall(cfg)
	assertions.sanityCheckDomainConfig(cfg)
	assertions.sanityCheckOnlineConfig(cfg)
	if wlst_support:
		configure_domain_PKI(cfg)
	else:
		raise Exception('WLST support required for this command')

def configure_domain_PKI(cfg):
	try:
		#__connectAdminServer(cfg)
		connectAdminServerOverSSL(cfg)
	except Exception, error:
		print 'unable to connect Admin'
		sys.exit()
	try:
		domainSSLConfiguration(cfg)
	except Exception, error:
		print 'Unable to configure PKI : ' + str(error)
		


