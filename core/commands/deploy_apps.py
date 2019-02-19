import common.assertions as assertions

execfile('wlst/common.py')
execfile('wlst/apps.py')

def run(cfg):
    #"""Deploy Apps"""
    assertions.sanityCheckInstall(cfg)
    assertions.sanityCheckDomainConfig(cfg)
    assertions.sanityCheckOnlineConfig(cfg)
    if wlst_support:
        deploy_apps(cfg)
    else:
        raise Exception('WLST support required for this command')
        
def deploy_apps(cfg):
	try:
		connectAdminServerOverSSL(cfg)
		#connect('weblogic','Welcome1','t3://gcp2cpp084:19101')
	except Exception, error:
		print 'unable to connect Admin'
		sys.exit()

	startEditSession()
	try:
		deployApps(cfg)
	except Exception, error:
		print 'Unable to deploy applications : ' + str(error)
		cancelEdit('y')
	else:
		saveAndActivateChanges()
    #disconnect('true')

