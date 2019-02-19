import common.assertions as assertions

execfile('wlst/common.py')
execfile('wlst/createNetworkChannel.py')

def run(cfg):
	"""Create Network Channel"""
	assertions.sanityCheckInstall(cfg)
	assertions.sanityCheckDomainConfig(cfg)
	assertions.sanityCheckOnlineConfig(cfg)
	if wlst_support:
		create_NetworkChannel(cfg)
	else:
		raise Exception('WLST support required for this command')

def create_NetworkChannel(cfg):
	try:
		connectAdminServerOverSSL(cfg)
	except Exception, error:
		print 'unable to connect Admin'
	try:
		createDomainNetworkChannel(cfg)
	except Exception, error:
		print 'Unable to configure PKI : ' + str(error)
		


