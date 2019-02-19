import common.assertions as assertions

execfile('wlst/common.py')

def run(cfg):
	#""""""
	assertions.sanityCheckInstall(cfg)
	assertions.sanityCheckDomainConfig(cfg)
	assertions.sanityCheckOnlineConfig(cfg)
	if wlst_support:
		createMserverDomain(cfg)
	else:
		raise Exception('WLST support required for this command')

def createMserverDomain(cfg):
	servers=cfg.getProperty('wls.servers')
	if not servers is None and len(servers)>0:
		try:
			__connectAdminServer(cfg)
	#		connectAdminServerOverSSL(cfg)
		except Exception, error:
			print 'unable to connect Admin'
			sys.exit('FAILED')

		try:
			__createDomainTemplate(cfg)
		except Exception, error:
			print 'Unable to create Mserver Domain : ' + str(error)
