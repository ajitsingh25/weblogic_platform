import common.assertions as assertions

execfile('wlst/common.py')
execfile('wlst/domainWatchesNotification.py')

def run(cfg):
	"""Configure Domain Monitoring"""
	assertions.sanityCheckInstall(cfg)
	assertions.sanityCheckDomainConfig(cfg)
	assertions.sanityCheckOnlineConfig(cfg)
	if wlst_support:
		configureDomainMonitoring(cfg)
	else:
		raise Exception('WLST support required for this command')

def configureDomainMonitoring(cfg):
	try:
		connectAdminServerOverSSL(cfg)
	except Exception, error:
		print 'unable to connect Admin'

	try:
		configureDomainWatchNotification(cfg)
	except Exception, error:
		print 'Unable to configure Domain Monitoring : ' + str(error)