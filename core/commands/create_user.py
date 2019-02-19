import common.assertions as assertions

execfile('wlst/common.py')
execfile('wlst/manageUserandGroups.py')

def run(cfg):
	""""""
	assertions.sanityCheckInstall(cfg)
	assertions.sanityCheckDomainConfig(cfg)
	assertions.sanityCheckOnlineConfig(cfg)
	if wlst_support:
		create_User(cfg)
	else:
		raise Exception('WLST support required for this command')

def create_User(cfg):
	try:
		connectAdminServerOverSSL(cfg)
	except Exception, error:
		print 'unable to connect Admin'
		sys.exit('Aborting..')

	try:
		createUsers(cfg)
	except Exception, error:
		print 'Unable to create users : ' + str(error)
