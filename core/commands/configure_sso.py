import common.assertions as assertions

execfile('wlst/common.py')

def run(cfg):
	"""COnfigure Domain SSO"""
	assertions.sanityCheckInstall(cfg)
	assertions.sanityCheckDomainConfig(cfg)
	assertions.sanityCheckOnlineConfig(cfg)
	if wlst_support:
		configureSSO(cfg)
	else:
		raise Exception('WLST support required for this command')

def configureSSO(cfg):

	try:
		__ssoSetUp(cfg)
	except Exception, error:
		print 'Unable to implement insecure protocol : ' + str(error)
		
