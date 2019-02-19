import common.assertions as assertions

execfile('wlst/common.py')
execfile('wlst/apps.py')

def run(cfg):
    #
    assertions.sanityCheckInstall(cfg)
    assertions.sanityCheckDomainConfig(cfg)
    assertions.sanityCheckOnlineConfig(cfg)
    if wlst_support:
        userConfig(cfg)
    else:
        raise Exception('WLST support required for this command')
        
def userConfig(cfg):
    __connectAdminServer(cfg)
    edit()
    startEdit()
    try:
        create_userConfig(cfg)
    except Exception, error:
        print 'Unable to create user config : ' + str(error)
        cancelEdit('y')
    else:
        save()
        activate(block='true')
    #disconnect('true')
	
def create_userConfig(configProperties):
	domainHome = configProperties.getProperty('wls.domain.dir')
	domainName = configProperties.getProperty('wls.domain.name')
	userconfig=domainHome+'/'+domainName+'/userconfig/user.config'
	userkey=domainHome+'/'+domainName+'/userconfig/user.key'
	storeUserConfig(userconfig, userkey)
	

