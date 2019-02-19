import common.assertions as assertions

execfile('wlst/common.py')

def run(cfg):
	#""""""
	assertions.sanityCheckInstall(cfg)
	assertions.sanityCheckDomainConfig(cfg)
	assertions.sanityCheckOnlineConfig(cfg)
	if wlst_support:
		setUserOverride(cfg)
	else:
		raise Exception('WLST support required for this command')

def setUserOverride(cfg):
	try:
		__createUserOverrideSh(cfg)
	except Exception, error:
		print 'Unable to update Domain Inventory : ' + str(error)