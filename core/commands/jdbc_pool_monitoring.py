import common.assertions as assertions

execfile('wlst/common.py')
execfile('wlst/jdbcpool_monitoring.py')

def run(cfg):
	"""Configure JDBC Monitoring"""
	assertions.sanityCheckInstall(cfg)
	assertions.sanityCheckDomainConfig(cfg)
	assertions.sanityCheckOnlineConfig(cfg)
	if wlst_support:
		configureJDBCPoolMonitoring(cfg)
	else:
		raise Exception('WLST support required for this command')

def configureJDBCPoolMonitoring(cfg):
	try:
		connectAdminServerOverSSL(cfg)
	except Exception, error:
		print 'unable to connect Admin'
		sys.exit('Aborting..')

	try:
		checkPool(cfg)
	except Exception, error:
		print 'Unable to configure JDBC Monitoring : ' + str(error)
