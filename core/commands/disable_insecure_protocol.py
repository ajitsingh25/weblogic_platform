import common.assertions as assertions

execfile('wlst/common.py')
execfile('wlst/configurePKI.py')

def run(cfg):
	"""Disable Insecure Protocol For a Weblogic Domain"""
	assertions.sanityCheckInstall(cfg)
	assertions.sanityCheckDomainConfig(cfg)
	assertions.sanityCheckOnlineConfig(cfg)
	if wlst_support:
		disableInsecureProtocol(cfg)
	else:
		raise Exception('WLST support required for this command')

def disableInsecureProtocol(cfg):

	try:
		__disableHTTPPort(cfg)
	except Exception, error:
		print 'Unable to implement insecure protocol : ' + str(error)
		
