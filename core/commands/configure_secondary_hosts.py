import common.assertions as assertions

execfile('wlst/common.py')

def run(cfg):
	#""""""
	assertions.sanityCheckInstall(cfg)
	assertions.sanityCheckDomainConfig(cfg)
	assertions.sanityCheckOnlineConfig(cfg)
	if wlst_support:
		configureSecondary(cfg)
	else:
		raise Exception('WLST support required for this command')

def configureSecondary(cfg):
	try:
		getWLSMachineandandExecuteSecondary(cfg)
	except Exception, error:
		print 'Unable to configure secondary hosts : ' + str(error)