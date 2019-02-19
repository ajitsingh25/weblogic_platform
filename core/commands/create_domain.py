import common.assertions as assertions
import common.logredirect as logredirect
import common.create_xml as cx
from xml.dom import minidom

from java.io import File

execfile('wlst/common.py')
execfile('wlst/apps.py')
execfile('wlst/manageUserandGroups.py')
execfile('wlst/createDomain.py')

def run(cfg):
		"""Create WebLogic Domain"""
		assertions.sanityCheckInstall(cfg)
		assertions.sanityCheckDomainConfig(cfg)
		xmlDoc = cx.run(cfg)
		if wlst_support:
			logredirect.setup()
			#print(cfg)
			currentUser=__getOSUser()
			definedUser=cfg.getProperty('wls.install.user')
			__checkOSCertification(cfg)
			if str(currentUser) == str(definedUser):
				create_domain(cfg, xmlDoc)
			else:
				print("Please execute wlscli with user "+definedUser)
				sys.exit('Aborting..')
		else:
			raise Exception('WLST support required for this command')

def create_domain(configProperties, doc):
	domainPath=configProperties.getProperty('wls.domain.dir')
	domainName=configProperties.getProperty('wls.domain.name')   
	domainAppDir=configProperties.getProperty('wls.domain.app.dir')
	webLogicHome=configProperties.getProperty('wls.oracle.home')
	domainType=configProperties.getProperty('wls.domain.type')
	version=configProperties.getProperty('wls.version')
	try:
		if domainName=='':
			log.error("wls.domain.name property can't be empty")
			raise Exception('wls.domain.name property can not be empty')
		domainFullPath=str(domainPath) + '/' + str(domainName)
		#checkDomainExistence(domainFullPath)   
		log.info('Creating domain: ' + domainFullPath)
		__createDomain(doc)
		   
	except Exception, error:
		log.error('Unable to create domain [' + str(domainPath) + '/' + str(domainName) + ']')
		raise error

        __changeJDK(configProperties)
	updateDomainPropertiesForMonitoring(configProperties)
#	__update_domainInventory(configProperties)
	__generateScripts(configProperties)
        __configureNM(configProperties)
	__startAdminServerwithScript(configProperties)
#       createUsers(configProperties)
	if not domainType is None and domainType == 'pega':
		deployPegaApp(configProperties)
	createUserConfig(configProperties)
	__createUserCommand(configProperties)
        if not domainType is None and domainType == 'pega':
                __createDomainNetworkChannel(configProperties)
        if version != "wls12130":
                __createMServerDomainCommand(configProperties)
#        if not domainType is None and domainType == 'pega':
#                __createPegaConfigCommand(configProperties)
        if version != "wls12130":
                __configureDomainMonitoring(configProperties)
        __domainSSLConfiguration(configProperties)
	__disableHTTPPort(configProperties)
#        __domainSSLConfiguration(configProperties)
	__shutdownAdminServer()
        __changeScriptT3s(configProperties)
        __setUserOverrideCommand(configProperties)
        __configureNMSSL(configProperties)
        __restartNM(configProperties)
        __startAdminServerwithScript(configProperties)
	#__startNM(configProperties)

		
def checkDomainExistence(domainPath):
        if File(domainPath).exists():
                raise Exception('Cannot create domain as it already exists at ' + domainPath)
                
def deployPegaApp(cfg):
	applications = cfg.getProperty('applications')
	if applications is None:
		print "No App to deplot"
	else:
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
                
def createUserConfig(configProperties):
        __connectAdminServer(configProperties)
        edit()
        startEdit()
        try:
                domainHome = configProperties.getProperty('wls.domain.dir')
                domainName = configProperties.getProperty('wls.domain.name')
                userconfig=domainHome+'/'+domainName+'/userconfig/user.config'
                userkey=domainHome+'/'+domainName+'/userconfig/user.key'
                storeUserConfig(userconfig, userkey)
        except Exception, error:
                print 'Unable to create userconfig : ' + str(error)
                cancelEdit('y')
        else:
                save()
                activate(block='true')
        #disconnect()


