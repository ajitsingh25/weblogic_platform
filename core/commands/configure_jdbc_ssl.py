import common.assertions as assertions

execfile('wlst/common.py')
execfile('wlst/manageJdbcSSL.py')

def run(cfg):
	"""Configure JDBC Monitoring"""
	assertions.sanityCheckInstall(cfg)
	assertions.sanityCheckDomainConfig(cfg)
	assertions.sanityCheckOnlineConfig(cfg)
	if wlst_support:
		configure_JDBCSSL(cfg)
	else:
		raise Exception('WLST support required for this command')

def configure_JDBCSSL(cfg):
	try:
		connectAdminServerOverSSL(cfg)
	except Exception, error:
		print 'unable to connect Admin'
		sys.exit('Aborting..')

	try:
		configureJDBCSSL(cfg)
	except Exception, error:
		print 'Unable to configure JDBC Monitoring : ' + str(error)
