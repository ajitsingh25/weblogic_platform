import common.assertions as assertions

execfile('wlst/common.py')

def run(cfg):
	"""Update Domain Inventory at Centralized Location"""
	assertions.sanityCheckInstall(cfg)
	assertions.sanityCheckDomainConfig(cfg)
	assertions.sanityCheckOnlineConfig(cfg)
	if wlst_support:
		updateInventory(cfg)
	else:
		raise Exception('WLST support required for this command')

def updateInventory(cfg):
	try:
		domainInventory(cfg)
	except Exception, error:
		print 'Unable to update Domain Inventory : ' + str(error)