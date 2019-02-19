import common.assertions as assertions

execfile('wlst/common.py')
execfile('wlst/updateSvrStartArguments.py')

def run(cfg):
	"""Update Server Start Arguments"""
	assertions.sanityCheckInstall(cfg)
	assertions.sanityCheckDomainConfig(cfg)
	assertions.sanityCheckOnlineConfig(cfg)
	if wlst_support:
		updateSvrStrtArgs(cfg)
	else:
		raise Exception('WLST support required for this command')

def updateSvrStrtArgs(cfg):
	try:
		connectAdminServerOverSSL(cfg)
	except Exception, error:
		print 'unable to connect Admin'

	try:
		updateSvrArg(cfg)
	except Exception, error:
		print 'Unable to Update Server Startup Parameter : ' + str(error)