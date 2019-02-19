##
## common.py
##
## This script contains functions that may be common to multiple scripts. This 
## includes configuration, connection and error functions.

from weblogic.descriptor import BeanAlreadyExistsException
from weblogic.management.utils import AlreadyExistsException
from java.io import BufferedReader
from java.io import FileInputStream
from java.io import InputStreamReader
from java.security import MessageDigest
from javax.naming import AuthenticationException
from java.lang import Runtime
from java.lang import SecurityException
from org.apache.log4j import Logger, PropertyConfigurator
from shutil import *

import socket
import sys
import os
import re
import getopt
import java.sql as jsql
import string

OS_TYPE_WINDOWS = "WindowsNT"

PROPERTY_DISABLE_PROMPTING = "confignow.noninteractive"


#=======================================================================================
# Global variables
#=======================================================================================

commonModule = '1.0.1'

try:
	scriptConfigProperties
except NameError:
	scriptConfigProperties = None

try:
	replaceFlag
except NameError:
	replaceFlag = None

try:
	log
except NameError:
	log = Logger.getLogger('ConfigNOW')

log.debug('Loading module [common.py] version [' + commonModule + ']')

	
#=======================================================================================
# Error class for script errors
#=======================================================================================

class ScriptError(Exception):
  def __init__(self, msg):
    self.msg = msg

  def __str__(self):
    return repr(self.msg)


#=======================================================================================
# getUserInput
# 
# Prompt user for input
#=======================================================================================

def getUserInput(prompt, default):
	"""Reads input from the user"""
	
	if default is not None:
		prompt += ' [' + default + ']'
	
	prompt += ' : '
	
	value = raw_input(prompt)
	
	if len(value) == 0:
		return default
	else:
		return value
	
	# done with reading input


#=======================================================================================
# getPropertyFileLocation
# 
# Returns the location of the properties file being used by the script.
#=======================================================================================

def getPropertyFileLocation():
	return str(sys.argv[1])


#==============================================================================
# isUpdate
#
# Indicates if the configure domain process is being performed as
# part of an update to a freshly created domain (changed with the create 
# domain process) or as an update to a previously created domain
#==============================================================================
def isUpdateToPreviouslyCreatedDomain():
	
	isUpdate = 'false'
	
	try:
		opts, args = getopt.getopt(sys.argv[2:], "", ["domainProperties=","resourcesProperties=","update=", "managedServer="])
	except getopt.GetoptError, err:
		log.error(str(err))
		sys.exit(2)	
	for o, a in opts:
		if o == "--update":
			isUpdate = a

	return isUpdate


#==============================================================================
# getManagedServer()
#
#==============================================================================
def getManagedServer():
	
	managedServer = None
	
	try:
		opts, args = getopt.getopt(sys.argv[2:], "", ["domainProperties=", "resourcesProperties=", "update=", "managedServer="])
	except getopt.GetoptError, err:
		log.error(str(err))
		sys.exit(2)	
	for o, a in opts:
		if o == "--managedServer":
			managedServer = a

	return managedServer


#==============================================================================
# getDomainFileName
#
#==============================================================================
def getDomainFileName():
	
	domainPropFile = None
	
	try:
		opts, args = getopt.getopt(sys.argv[2:], "", ["domainProperties=","resourcesProperties=","update=", "managedServer="])
	except getopt.GetoptError, err:
		log.error(str(err))
		sys.exit(2)	
	for o, a in opts:
		if o == "--domainProperties":
			domainPropFile = a

	if domainPropFile is None:
		domainPropFile = 'domain.properties'
		
	log.debug('#################################################')
	log.debug('#################################################')
	log.debug('#################################################')
	log.debug('Using ' + str(domainPropFile))
	log.debug('#################################################')
	log.debug('#################################################')
	log.debug('#################################################')
	
	return domainPropFile

#==============================================================================
# getResourcesFileName
#
#==============================================================================
def getResourcesFileName():

	resourcesPropFile = None
	
	try:
		opts, args = getopt.getopt(sys.argv[2:], "", ["domainProperties=","resourcesProperties=","update=", "managedServer="])
	except getopt.GetoptError, err:
		log.error(str(err))
		sys.exit(2)
	for o, a in opts:
		if o == "--resourcesProperties":
			resourcesPropFile = a
	
	if resourcesPropFile is None:
		resourcesPropFile = 'resources.properties'
	
	log.debug('#################################################')
	log.debug('#################################################')
	log.debug('#################################################')
	log.debug('Using ' + str(resourcesPropFile))
	log.debug('#################################################')
	log.debug('#################################################')
	log.debug('#################################################')
	
	return resourcesPropFile

#=======================================================================================
# isReplaceRequired
# 
# Provides the user with an information message informing them that property values will
# will not be overridden when REPLACE is absent as an environment variable.
#=======================================================================================
def isReplaceRequired(replaceFlagParam):

	global replaceFlag
	
	if not replaceFlagParam:
		try:
			replaceFlag = os.environ['REPLACE']
		except KeyError, error:
			if replaceFlag is None:
				log.debug('#####################################################')
				log.debug('#The REPLACE environment variable does not exist.')
				log.debug('#If you want to override property values, ')
				log.debug('#please append [set REPLACE=true] into setenv.cmd or ')
				log.debug('#[export REPLACE=true] into setenv.sh and run the scripts again.')
				log.debug('#####################################################')
				replaceFlag = 'N'
	else:
		replaceFlag = replaceFlagParam

	if not replaceFlag is None and len(replaceFlag)>0:
		if replaceFlag.upper()=='TRUE' or replaceFlag.upper()=='YES' or replaceFlag.upper()=='Y':
			return 1
		else:
			return 0
	else:
		return 0

def __connectManagedServer(wlsHost, wlsPort, wlsUser, wlsPassword):
	#=======================================================================================
	# Load domain properties
	#=======================================================================================
	
	wlsURL='t3://' + str(wlsHost) + ':' + str(wlsPort)
	
	sleeptime = 15
	maxAttempt = 10
	attemptIdx = 1
	while 1:
		log.debug('Establishing connection to Server at URL [' + str(wlsURL) + '], attempt #' + str(attemptIdx))
		try:
			connect(wlsUser, wlsPassword, wlsURL)
			break
		except Exception, error:
			if attemptIdx<maxAttempt:
				log.debug('Establishing connection to Server failed at attempt #' + str(attemptIdx) + ': No Server running on URL [' + str(wlsURL) + '] or the server is not ready to execute WLST command. Delay ' + str(sleeptime) + ' seconds and try again.')
				Thread.currentThread().sleep(sleeptime*1000)
				attemptIdx+=1
			else:
				raise ScriptError, 'Unable to connect to Server at URL [' + str(wlsURL) + ']: ' + str(error)

#=======================================================================================
# __connectAdminServer
# 
# Connects to the admin server, as determined from the config and makes
# a series of attempts to connect to the admin server.
#=======================================================================================

def __connectAdminServer(configProperties, wlsAdminPortSSL=None):
	if connected == 'false':
		wlsAdminPort=configProperties.getProperty('wls.admin.Port')
		wlsAdminSSLIncrement=configProperties.getProperty('wls.admin.SSLListenPortIncrementOverHttpPort')
		wlsAdminUser=configProperties.getProperty('wls.admin.username')
		wlsAdminPassword=configProperties.getProperty('wls.admin.password')
		if wlsAdminPortSSL is None or len(str(wlsAdminPortSSL)) == 0:
			wlsAdminURL='t3://' + str(configProperties.getProperty('wls.admin.Hostname')) + ':' + str(wlsAdminPort)
		else:
			wlsAdminURL='t3s://' + str(configProperties.getProperty('wls.admin.Hostname')) + ':' + str(wlsAdminPortSSL)
    
		sleeptime = 15
		maxAttempt = 5
		attemptIdx = 1
         
		while 1:
			log.info('Establishing connection to Admin Server at URL [' + str(wlsAdminURL) + '], attempt #' + str(attemptIdx))
			try:
				print "connecting.."
				print connected
				connect(wlsAdminUser, wlsAdminPassword, wlsAdminURL)
				print connected
				break
			except Exception, error:
				exceptionStr = str(error)
				if (exceptionStr.count('failed to be authenticated') > 0):
					log.error('Authentication error occurred connecting to Admin Server at URL [' + str(wlsAdminURL) + ']: ' + str(error))
					raise ScriptError, 'Authentication issue connecting to Admin Server at URL [' + str(wlsAdminURL) + ']: ' + str(error)
				if attemptIdx<maxAttempt:
					log.debug('Establishing connection to Admin Server failed at attempt #' + str(attemptIdx) + ': No Admin Server running on URL [' + str(wlsAdminURL) + '] or the server is not ready to execute WLST command. Delay ' + str(sleeptime) + ' seconds and try again.')
					Thread.currentThread().sleep(sleeptime*1000)
					attemptIdx+=1
				else:
					raise ScriptError, 'Unable to connect to Admin Server at URL [' + str(wlsAdminURL) + ']: ' + str(error)
	else:
		print "Already Connected with Admin Server"

#=======================================================================================
# __setTargetsOnline
# 
# Sets targets for a particular MBean while online (connected to running domain)
#=======================================================================================

def __setTargetsOnline(bean, targets, targetType, domainProperties):
    try:
        if targets is None or len(targets)==0 or targetType is None or len(targetType)==0:
            targetNames = domainProperties.getProperty('wls.admin.name')
        else:
            targetList=targets.split(',')
            targetNames = None
            for targetKey in targetList:
                targetName = None
                if targetType.upper()=='CLUSTER':
                    targetName=domainProperties.getProperty('wls.cluster.' + str(targetKey) + '.name')
                    cd('/')
                    clusterInstance = lookup(targetName, 'Cluster')
                    bean.addTarget(clusterInstance)
                else:
                    if targetType.upper()=='SERVER':
                        targetName=domainProperties.getProperty('wls.server.' + str(targetKey) + '.name')
                        cd('/')
                        serverInstance = lookup(targetName, 'Server')
                        bean.addTarget(serverInstance)
                    else:
                        log.debug('Does not support target type [' + str(targetType) + '], skipping.')
                        
    except Exception, error:
        raise ScriptError, 'Unable to add target [' + str(targets) + ']: ' + str(error)

    
#=======================================================================================
# __setTargetsOffline
# 
# Sets targets for a bean offline (while connected to the directory structure of a 
# domain that is not running)
#=======================================================================================

def __setTargetsOffline(targets, targetType, domainProperties):
    try:
        if targets is None or len(targets)==0 or targetType is None or len(targetType)==0:
            targetNames = domainProperties.getProperty('wls.admin.name')
        else:
            targetList=targets.split(',')
            targetNames = None
            for targetKey in targetList:
                targetName = None
                if targetType.upper()=='CLUSTER':
                    targetName=domainProperties.getProperty('wls.cluster.' + str(targetKey) + '.name')
                else:
                    if targetType.upper()=='SERVER':
                        targetName=domainProperties.getProperty('wls.server.' + str(targetKey) + '.name')
                    else:
                        log.debug('Does not support target type [' + str(targetType) + '], skipping.')
                        
                if targetNames is None:
                    targetNames = targetName
                else:
                    targetNames = targetNames + ',' + targetName

        if not targetNames is None: 
            set('targets', targetNames)
        else:
            log.debug('Could not add target None to [' + str(bean.getName()) + '], skipping.')
    except Exception, error:
        raise ScriptError, 'Unable to add target [' + str(targets) + ']: ' + str(error)

       
#=======================================================================================
# setConfigProperties
# 
# Set the global script properties
#=======================================================================================

def setConfigProperties(properties):
	"""Sets the global script configuration properties"""

	global scriptConfigProperties
	
	scriptConfigProperties = properties
	
	# done setting global script config

#=======================================================================================
# getConfigProperties
# 
# Return the global script properties
#=======================================================================================

def getConfigProperties():
	"""Returns the global script configuration properties"""

	global scriptConfigProperties
	
	if scriptConfigProperties is None:
		scriptConfigProperties = Properties()
	
	return configProperties
	
	# done returning global script config

#=======================================================================================
# setComponentProperties
# 
# Set the global component properties
#=======================================================================================

def setComponentProperties(properties):
	"""Sets the global script component properties"""

	global scriptComponentProperties
	
	scriptComponentProperties = properties
	
	# done setting global script config


#=======================================================================================
# getComponentProperties
# 
# Return the global script properties
#=======================================================================================

def getComponentProperties():
	"""Returns the global script configuration properties"""

	global scriptComponentProperties
	
	if scriptComponentProperties is None:
		scriptComponentProperties = Properties()
	
	return scriptComponentProperties
	
	# done returning global script config
	


#==============================================================================
# __loadTextFile
#
# Loads contents of the text file specified, performing appropriate error-checking
#==============================================================================

def __loadTextFile(filePath):

	file = open(filePath)
	contents = file.read()
	file.close()
	return contents
	
def getServerName(serverNameInConfig, domainProperties):
	name = domainProperties.getProperty('wls.server.' + serverNameInConfig + '.name')
	replaceName = domainProperties.getProperty('wls.server.' + serverNameInConfig + '.replace.name')
	if name is None:
	        raise ScriptError, 'Could not find server name in configuration matching [' + serverNameInConfig + '].'
	if not replaceName is None:
	    	name = replaceName
	return name

def getMachineName(machineNameInConfig, domainProperties):
	name = domainProperties.getProperty('wls.domain.machine.' + machineNameInConfig + '.name')
	replaceName = domainProperties.getProperty('wls.domain.machine.' + machineNameInConfig + '.replace.name')
	if name is None:
	        raise ScriptError, 'Could not find machine name in configuration matching [' + machineNameInConfig + '].'
	if not replaceName is None:
	    	name = replaceName
	return name

#=======================================================================================
# runDbScripts
# 
# Runs all of the db script files that are specified in the dbScripts list
#=======================================================================================

def runDbScripts(dbScripts, dbURL, dbUser, dbPassword, dbDriver):

	if not dbScripts is None and not dbURL is None and not dbUser is None and not dbPassword is None:
		lang.Class.forName(dbDriver)
		con = jsql.DriverManager.getConnection(dbURL,dbUser,dbPassword)
		stmt = con.createStatement()

		scriptList = dbScripts.split(",")
		for scriptFile in scriptList:
			log.info('Executing script ' + str(scriptFile))
			file = open(scriptFile, 'r')
			script = ''
			for line in file.readlines():
			   line = line.strip()
			   if len(line) > 0:
				   try:
					   if line[len(line)-1] == ':':
						line = line[0:len(line)-1]
						script = script + line + '\n'
						stmt.executeUpdate(script)
						script = ''
					   else:
						script = script + line + '\n'
				   except Exception, error:
					   log.warn('Ignoring error: ' + str(error))
		stmt.close()
		con.close()
		
#==============================================================================
# __readBytes
#
# Reads the contents of the file specified, returning as a byte array
#==============================================================================
def __readBytes(file):
	# Returns the contents of the file in a byte array.
	inputstream = FileInputStream(file)
    
	# Get the size of the file
	length = file.length()

	# Create the byte array to hold the data
	bytes = jarray.zeros(length, "b")

	# Read in the bytes
	offset = 0
	numRead = 1
        while (offset < length) and (numRead > 0):
		numRead = inputstream.read(bytes, offset, len(bytes) - offset)
		offset += numRead

	# Ensure all the bytes have been read in
	if offset < len(bytes):
		log.warn("Could not read entire contents of '" + file.getName()) 

	# Close the input stream and return bytes
	inputstream.close()
	return bytes

#==============================================================================
# getOsType
#
# Returns a string indicating the OS type
#==============================================================================
def getOsType():

    NOT_WINDOWS = 'NOT WINDOWS'

    try:
        osNameTemp = os.getenv('OS',NOT_WINDOWS)
        if not osNameTemp == NOT_WINDOWS and string.find(osNameTemp, 'Windows') == 0:
            return OS_TYPE_WINDOWS

        # non-Windows process
        process = Runtime.getRuntime().exec("uname")
        output = process.getInputStream() # process' output is our input
        br = BufferedReader(InputStreamReader(output))
        osName = br.readLine()

    except Exception, error:
        log.error("Could not determine operating system type: " + str(error))

    return osName


def __startAdminServerwithScript(domainProperties):
    try:
#	if connected == 'true':
#		print 'Shutting down the Admin Server...':
#		disconnect()
#		shutdown(force='true', block='true')
#
	domainLocation = domainProperties.getProperty('wls.domain.dir') + '/' + domainProperties.getProperty('wls.domain.name')
	startScript = domainLocation+ '/bin/startadmin.sh'
	stopScript = domainLocation+ '/bin/stopWebLogic.sh'
	if connected == 'true':
                print 'Shutting down the Admin Server...'
                disconnect()
		print ('The following start command will be used: '+stopScript)
		os.system(stopScript)
        	print 'Just in case wait for 30 seconds.'
    #    	java.lang.Thread.sleep(30000)

	print 'Start the admin server using start script'
	print ('The following start command will be used: '+startScript)
	os.system(startScript)
	print 'Just in case wait for 30 seconds.'
	java.lang.Thread.sleep(30000)
    except OSError:
        print 'Exception while starting the adminserver !'
        dumpStack()

def __createDomainTemplate(domainProperties):
	servers=domainProperties.getProperty('wls.servers')
	if not servers is None and len(servers)>0:
		mserver=domainProperties.getProperty('wls.mserver.domain.dir') 
		domainName=domainProperties.getProperty('wls.domain.name')
		domainPath = mserver+'/'+domainName
		domainTemplate=domainProperties.getProperty('ConfigNOW.home')+'/custom/resources/templates/'+domainName+'.jar'
		nodemanagerHome=domainProperties.getProperty('wls.oracle.home')+'/oracle_common/common/nodemanager'
#		print domainPath
#		print domainTemplate
#		__connectAdminServer(domainProperties)
		print "Writing domain to a template."
		
		if os.path.exists(domainTemplate):
			try:
				print "Removing existing template jar"
    				os.remove(domainTemplate)
			except OSError:
    				sys.exit('Unable to remove '+str(domainTemplate)+' , aborting ...')

		print domainTemplate
		writeTemplate(domainTemplate)

		disconnect()

		#select and load the template that was downloaded from the Administration Server.
		print "Loading the template."+domainTemplate
		selectCustomTemplate(domainTemplate)
		loadTemplates()
		setOption("OverwriteDomain", "true")

		print "Configuring Nodemanager."
		cd("/NMProperties")
		set("NodeManagerHome", nodemanagerHome)

		#create the mserver domain
		print "Writing Domain Configuration."
		writeDomain(domainPath)
		os.unlink(domainTemplate)

		print "Managed Domain built successfully."
		#disconnect()
	else:
		print "Managed Server Doesn't exist in this domain ..."
	
	
def __generateScripts(domainProperties):
	try:
		platformHome=domainProperties.getProperty('ConfigNOW.home')
		wlscliScript= platformHome + '/' + "wlscli.sh"
		env = sys.argv[2]
		config = sys.argv[3]
		createAdmin = wlscliScript+' populate.startadmin.sh '+env+' '+config
		print ('The following command will be used: '+createAdmin)
		os.system(createAdmin)
		java.lang.Thread.sleep(10000)

		servers=domainProperties.getProperty('wls.servers')
		if not servers is None and len(servers)>0:
			createNM = wlscliScript+' populate.startnm.sh '+env+' '+config
			print ('The following command will be used: '+createNM)
			os.system(createNM)
			java.lang.Thread.sleep(10000)

			createNMstop = wlscliScript+' populate.stopnm.sh '+env+' '+config
			print ('The following command will be used: '+createNMstop)
			os.system(createNMstop)
			java.lang.Thread.sleep(10000)
		
		createCacheClean = wlscliScript+' populate.cache.sh '+env+' '+config
		print ('The following command will be used: '+createCacheClean)
		os.system(createCacheClean)
		java.lang.Thread.sleep(10000)

		dataSources=domainProperties.getProperty('jdbc.datasources')
		if not dataSources is None and len(dataSources)>0:
			createJDBCPoolMonitoringScript = wlscliScript+' populate.pool_monitoring.sh '+env+' '+config
			print ('The following command will be used: '+createJDBCPoolMonitoringScript)
			os.system(createJDBCPoolMonitoringScript)
			java.lang.Thread.sleep(10000)
		
	except OSError:
		print "Exception while executing commands !"
		dumpStack()
	
	
def __configureNM(domainProperties):
	servers=domainProperties.getProperty('wls.servers')
	if not servers is None and len(servers)>0:
		try:
			platformHome=domainProperties.getProperty('ConfigNOW.home')
			wlscliScript= platformHome + '/' + "wlscli.sh"
			env = sys.argv[2]
			config = sys.argv[3]
			configureNMCommand = wlscliScript+' configure_nodemanager '+env+' '+config
			print ('The following command will be used: '+configureNMCommand)
			os.system(configureNMCommand)
			java.lang.Thread.sleep(10000)
		except OSError:
			print "Exception while executing commands !"
			dumpStack()
		
def __startNM(domainProperties):
	servers=domainProperties.getProperty('wls.servers')
	wlsVersion=domainProperties.getProperty('wls.version')
	if not servers is None and len(servers)>0:
		try:
			env = sys.argv[2]
			config = sys.argv[3]
			if wlsVersion == "wls12130":
				startNMScript = domainProperties.getProperty('wls.domain.dir') +'/'+domainProperties.getProperty('wls.domain.name')+'/bin/startnodemgr.sh'
			else:
				startNMScript = domainProperties.getProperty('wls.mserver.domain.dir') +'/'+domainProperties.getProperty('wls.domain.name')+'/bin/startnodemgr.sh'

			pidCommand="kill -9 `ps -ef | grep NodeManager | grep "+ domainProperties.getProperty('wls.oracle.home')+"| grep -v grep | grep bea | awk '{print $2}'`"
			if not pidCommand is None and len(pidCommand)>0:
				os.system(pidCommand)
			
			print ('The following command will be used: '+startNMScript)
			os.system(startNMScript)
			java.lang.Thread.sleep(10000)
		except OSError:
			print "Exception while executing commands !"
			dumpStack()
		
def __restartNM(domainProperties):
	servers=domainProperties.getProperty('wls.servers')
	wlsVersion=domainProperties.getProperty('wls.version')
	if not servers is None and len(servers)>0:
		try:
			env = sys.argv[2]
			config = sys.argv[3]
			if wlsVersion == "wls12130":
				stopNMScript = domainProperties.getProperty('wls.domain.dir') +'/'+domainProperties.getProperty('wls.domain.name')+'/bin/stopnodemgr.sh'
				startNMScript = domainProperties.getProperty('wls.domain.dir') +'/'+domainProperties.getProperty('wls.domain.name')+'/bin/startnodemgr.sh'
			else:
				stopNMScript = domainProperties.getProperty('wls.mserver.domain.dir') +'/'+domainProperties.getProperty('wls.domain.name')+'/bin/stopnodemgr.sh'
				startNMScript = domainProperties.getProperty('wls.mserver.domain.dir') +'/'+domainProperties.getProperty('wls.domain.name')+'/bin/startnodemgr.sh'
			#pidCommand="kill -9 `ps -ef | grep NodeManager | grep "+ domainProperties.getProperty('wls.oracle.home')+"| grep -v grep | grep bea | awk '{print $2}'`"
			print ('The following command will be used: '+stopNMScript)
			os.system(stopNMScript)
			java.lang.Thread.sleep(1000)		
			print ('The following command will be used: '+startNMScript)
			os.system(startNMScript)
			java.lang.Thread.sleep(1000)
		except OSError:
			print "Exception while executing commands !"
			dumpStack()

def __changeJDK(domainProperties):
        try:
                platformHome=domainProperties.getProperty('ConfigNOW.home')
                wlscliScript= platformHome + '/' + "wlscli.sh"
                env = sys.argv[2]
                config = sys.argv[3]
                createJDKScript = wlscliScript+' populate.changeJDK.sh  '+env+' '+config
                script= platformHome + '/core/commands/ant/resources/changeJDKHome.sh'
		print ('The following command will be used: '+createJDKScript)
                os.system(createJDKScript)
                print ('The following command will be used: '+script)
                os.system(script)
                java.lang.Thread.sleep(10000)
        except OSError:
                print "Exception while executing commands !"
                dumpStack()

def startEditSession():
    print 'Starting an edit session for making changes to the Weblogic configuration\n'
    redirect('/dev/null','false')
    edit()
    startEdit()

	
def discardChanges():
    print 'Discarding any changes made as part of this edit session...\n'
    try:
        cfgManager = getConfigManager()
        try:
            cfgManager.getChanges()
            print 'There are existing edit sessions with pending changes\n'
            edit()
            print 'Undoing any pending changes'
            undo(unactivateChanges='true', defaultAnswer='y')
            print 'Cancelling any existing edit sessions\n'
            cancelEdit(defaultAnswer='y')
            print "\n"
            if connected=="false":
                disconnect()
            exit(exitcode=1)
        except:
            print 'There are no existing edit sessions\n'
            cancelEdit(defaultAnswer='y')
            if connected=="true":
                disconnect()
            exit(exitcode=1)
    except Exception, e:
        print 'Error occurred while cancelling any existing edit sessions\n'
        print 'Exception is : ',  e
        print 'The stack trace is : '
        dumpStack()
        print "\n"
        undo(unactivateChanges='true', defaultAnswer='y')
        cancelEdit(defaultAnswer='y')
        if connected=="true":
            disconnect()
        exit(exitcode=1)

def saveAndActivateChanges():
    print 'Activating all the changes made during the existing edit session\n'

    try:
        save()
        activate()
	redirect('/dev/null','true')
    except Exception, e:
        print 'Error in activating the changes made during the existing edit session\n'
        dumpStack()
        print 'Discarding all the changes made during the existing edit session\n'
        discardChanges()
		
def __disableHTTPPort(domainProperties):
	#username=domainProperties.getProperty('wls.admin.username') 
	#password=domainProperties.getProperty('wls.admin.password') 

	#adminHost=domainProperties.getProperty('wls.admin.Hostname') 
	#adminPort=domainProperties.getProperty('wls.admin.Port') 
	#httpProtocolEnabled=domainProperties.getProperty('wls.servers.httpProtocolEnabled')
	httpsProtocolEnabled=domainProperties.getProperty('wls.servers.httpsProtocolEnabled')
	httpProtocolEnabled=''
	SecureReplicationEnable=''
	
	if httpsProtocolEnabled == 'true':
		httpProtocolEnabled = 'false'
		SecureReplicationEnable = 'true'
	else:
		httpProtocolEnabled = 'true'
		SecureReplicationEnable = 'false'
		
	#url='t3://'+adminHost+':'+adminPort
	connectAdminServerOverSSL(domainProperties)

		
	try:
		startEditSession()
		serversList=cmo.getServers()
		for each_server in serversList:
			svrName=each_server.getName()
			cd('/Servers/' + svrName+'/SSL/'+svrName)
			cmo.setEnabled(java.lang.Boolean(httpsProtocolEnabled))
			cd('/Servers/' + svrName)
			print "Disable HTTP Port for "+svrName
			cmo.setListenPortEnabled(java.lang.Boolean(httpProtocolEnabled))
			
		cd('/')
		clustersList=cmo.getClusters()
		if len(clustersList) > 0:
			for each_cluster in clustersList:
				clusterName=each_cluster.getName()
				cd('/Clusters/' + clusterName)
				print "Enable Secure Replication for "+clusterName
				cmo.setSecureReplicationEnabled(java.lang.Boolean(SecureReplicationEnable))

		cd('/')
		serversList=cmo.getServers()
		for each_server in serversList:
			svrName=each_server.getName()
			cd('/Servers/' + svrName + '/NetworkAccessPoints/')
			ncList=cmo.getNetworkAccessPoints()
			for e_nc in ncList:
				nc_name = e_nc.getName()
				cd('/Servers/' + svrName + '/NetworkAccessPoints/')
				cd(nc_name)
				print 'Disable insecure protocol for '+svrName+'\'s Network Channel '+nc_name
				cmo.setHttpEnabledForThisProtocol(false)
				#print 'Done...'
				cd('/')

		saveAndActivateChanges()
#		disconnect()
	except Exception, e:
		print 'Error in setting insecure protocol...\n'
		print e
		dumpStack()
		discardChanges()
		
def __disableNetworkChannelHTTP(domainProperties):
	httpsProtocolEnabled=domainProperties.getProperty('wls.servers.httpsProtocolEnabled')
	httpProtocolEnabled=''
	SecureReplicationEnable=''
	
	if httpsProtocolEnabled == 'true':
		httpProtocolEnabled = 'false'
		SecureReplicationEnable = 'true'
	else:
		httpProtocolEnabled = 'true'
		SecureReplicationEnable = 'false'
		
	connectAdminServerOverSSL(domainProperties)
	
	try:
		startEditSession()
		cd('/')
		serversList=cmo.getServers()
		for each_server in serversList:
			svrName=each_server.getName()
			cd('/Servers/' + svrName + '/NetworkAccessPoints/')
			ncList=cmo.getNetworkAccessPoints()
			for e_nc in ncList:
				nc_name = e_nc.getName()
				cd('/Servers/' + svrName + '/NetworkAccessPoints/')
				cd(nc_name)
				print 'Disable insecure protocol for '+svrName+'\'s Network Channel '+nc_name
				cmo.setHttpEnabledForThisProtocol(false)
				#print 'Done...'
				cd('/')
		
		saveAndActivateChanges()
#		disconnect()
	except Exception, e:
		print "<Error> Caught exception in disableInsecureProtocol"
		discardChanges()
	

def connectAdminServerOverSSL(domainProperties):
	domainDir=domainProperties.getProperty('wls.domain.dir')
	domainName=domainProperties.getProperty('wls.domain.name')
	adminServer_name=domainProperties.getProperty('wls.admin.name')
	separator = os.sep
	absDomain=domainDir+separator+domainName
        print connected
	if connected == 'false':
		print('Read Domain')
		readDomain(absDomain)
		cd('/')
		cd('Servers'+separator+adminServer_name+separator+'SSL'+separator+adminServer_name)
		sslEnabledFlag=get('Enabled')
		adminSSLPort=get('ListenPort')
		cd('/')
		cd('Servers'+separator+adminServer_name)
		httpEnabledFlag=get('ListenPortEnabled')
		#if sslEnabledFlag == 1:
		if httpEnabledFlag == 0:
#			adminSSLPort=get('ListenPort')
			closeDomain()
			__connectAdminServer(domainProperties, adminSSLPort)
		#elif sslEnabledFlag == 0:
		if httpEnabledFlag == 1:
			#url='t3://'+adminHost+':'+adminPort
			closeDomain()
			__connectAdminServer(domainProperties)
		else:
			print('Admin Url is invalid')
		#closeDomain()
	else:
		print "Already Connected to Admin Server"

	
def __domainSSLConfiguration(domainProperties):
	try:
		platformHome=domainProperties.getProperty('ConfigNOW.home')
		wlscliScript= platformHome + '/' + "wlscli.sh"
		env = sys.argv[2]
		config = sys.argv[3]
		configureSSLCommand = wlscliScript+' configure_SSL '+env+' '+config
		print ('The following command will be used: '+configureSSLCommand)
		os.system(configureSSLCommand)
		java.lang.Thread.sleep(10000)
	except OSError:
		print "Exception while executing commands !"
		dumpStack()
	
def __createDomainNetworkChannel(domainProperties):
	try:
		platformHome=domainProperties.getProperty('ConfigNOW.home')
		wlscliScript= platformHome + '/' + "wlscli.sh"
		env = sys.argv[2]
		config = sys.argv[3]
		createNCCommand = wlscliScript+' create_NetworkChannel '+env+' '+config
		print ('The following command will be used: '+createNCCommand)
		os.system(createNCCommand)
		java.lang.Thread.sleep(10000)
	except OSError:
		print "Exception while executing commands !"
		dumpStack()

				
def __changeScriptT3s(domainProperties):
	wlsAdminPort=domainProperties.getProperty('wls.admin.Port')
	wlsAdminSSLIncrement=domainProperties.getProperty('wls.admin.SSLListenPortIncrementOverHttpPort')
	wlsAdminSSLPort=int(wlsAdminPort)+int(wlsAdminSSLIncrement)
	domainName=domainProperties.getProperty('wls.domain.name')
	aserver=domainProperties.getProperty('wls.domain.dir')
	mserver=domainProperties.getProperty('wls.mserver.domain.dir')
	wlsVersion=domainProperties.getProperty('wls.version')

	pattern1='s/t3:/t3s:/g'
	pattern2='s/'+str(wlsAdminPort)+'/'+str(wlsAdminSSLPort)+'/g'
	pattern3='s/http:/https:/g'
	sedCommand3="sed -i 's/\${JAVA_OPTIONS}.*weblogic.WLST/\${JAVA_OPTIONS} -Dweblogic.security.SSL.ignoreHostnameVerification=true weblogic.WLST/g' "+aserver+'/'+domainName+'/bin/stopWebLogic.sh'
	sedCommand1='sed -i -e '+pattern1+' -e '+pattern2+' -e '+pattern3+' '+aserver+'/'+domainName+'/bin/*.sh'
	print ('Modifying WLS Scripts to t3s...')
	os.system(sedCommand1)	
	os.system(sedCommand3)
	servers=domainProperties.getProperty('wls.servers')
	if not servers is None and len(servers)>0:
		if wlsVersion != "wls12130":
			sedCommand2='sed -i -e '+pattern1+' -e '+pattern2+' -e '+pattern3+' '+mserver+'/'+domainName+'/bin/*.sh'
			os.system(sedCommand2)
		else:
			print wlsVersion
	
def __configureNMSSL(domainProperties):
	servers=domainProperties.getProperty('wls.servers')
	if not servers is None and len(servers)>0:
		try:
			platformHome=domainProperties.getProperty('ConfigNOW.home')
			wlscliScript= platformHome + '/' + "wlscli.sh"
			env = sys.argv[2]
			config = sys.argv[3]
			configureNMSSLCommand = wlscliScript+' configure_nodemanager_ssl '+env+' '+config
			print ('The following command will be used: '+configureNMSSLCommand)
			os.system(configureNMSSLCommand)
			java.lang.Thread.sleep(1000)
		except OSError:
			print "Exception while executing commands !"
			dumpStack()

def __configureDomainMonitoring(domainProperties):
	try:
		platformHome=domainProperties.getProperty('ConfigNOW.home')
		wlscliScript= platformHome + '/' + "wlscli.sh"
		env = sys.argv[2]
		config = sys.argv[3]
		configureDomainMonCommand = wlscliScript+' domain_monitoring '+env+' '+config
		print ('The following command will be used: '+configureDomainMonCommand)
		os.system(configureDomainMonCommand)
		java.lang.Thread.sleep(1000)
	except OSError:
		print "Exception while executing commands !"
		dumpStack()

def getOSVersion():
	try:
		versionList = open('/etc/redhat-release','r').read().split(' ')[6].split('.')
		majorVersionNumber = versionList[0]
		minorUpdateNumber = versionList[1]
		return majorVersionNumber
	except IOError, OSError:
		print "Skiping OS Version Checking"
		pass

def __getOSUser():
	import java.lang.System
	try:
		userName = System.getProperty("user.name")
		return userName
	except OSError:
		print "Skiping User Checking..."
		pass

def checkOSGroup(domainProperties):
	grpName=domainProperties.getProperty('wls.install.group')
	try:
		osGrpCmd = '[ $(getent group '+grpName+') ] && echo 1 || echo 0 '
		out = os.popen(osGrpCmd).read()
		return int(out)
	except OSError:
		print "Skiping OS Version Checking"
		pass

def checkOSUser(domainProperties):
	usrName=domainProperties.getProperty('wls.install.user')
	try:
		osUsrCmd='[ `getent passwd '+usrName+' | wc -l` -eq 1 ] && echo 1 || echo 0 '
		out = os.popen(osUsrCmd).read()
		return int(out)
	except ValueError, OSError:
		print "Skiping OS Version Checking"
		pass

def __populatePreCheckScript(domainProperties):
	try:
		platformHome=domainProperties.getProperty('ConfigNOW.home')
		wlscliScript= platformHome + '/' + "wlscli.sh"
		env = sys.argv[2]
		config = sys.argv[3]
		populatePreCheckScriptCommand = wlscliScript+' populate.preCheck.sh '+env+' '+config
		print ('The following command will be used: '+populatePreCheckScriptCommand)
		os.system(populatePreCheckScriptCommand)
		java.lang.Thread.sleep(1000)
		print "Please execute below script with root to complete prerequisite"
		print "["+platformHome+"/core/commands/ant/tmp/preCheck.sh]"
		sys.exit()
	except OSError:
		print "Exception while executing commands !"
		dumpStack()

def __checkOSCertification(domainProperties):
	grp=domainProperties.getProperty('wls.install.group')
	usr=domainProperties.getProperty('wls.install.user')
	pegaBase=domainProperties.getProperty('wls.pega.top')
	oracleBase=domainProperties.getProperty('wls.oracle.top')
	osVersion = getOSVersion()
	if not osVersion is None and int(osVersion) < 6:
		print "OS is not certified.\nLinux version must be above 5"
	#        sys.exit()
	else:
		print "OS is certified."

	grpOut = checkOSGroup(domainProperties)
	if not grpOut is None and grpOut == 1:
		print "Group "+grp+" Exists"
	else:
		print "Group "+grp+" Doesn't Exists"

	usrOut = checkOSUser(domainProperties)
	if not usrOut is None and usrOut == 1:
		print "User "+usr+" Exists"
	else:
		print "User "+usr+" Doesn't Exists"

	pegaOut=''
	if not domainType is None and domainType == 'pega':
		if not os.path.isdir(pegaBase):
			pegaOut=0
			print pegaBase+" dir do not exist"

	oracleOut=''
	if not os.path.isdir(oracleBase):
		oracleOut=0
                print oracleBase+" dir do not exist"
	
	if not grpOut is None and not usrOut is None and grpOut == 0 or  usrOut == 0 or pegaOut == 0 or oracleOut ==0:
		__populatePreCheckScript(domainProperties)
		

def domainInventory(domainProperties):
    #ssh pegaadmin@gcp2s0046.localhost "python3 /home/pegaadmin/confluence-update/update.py -s $HOSTNAME -u USERID -w WLSVERSION -d DOMAINS -p PATCH_ID -o OS_NAME -c CPU_CORES -db DBNAME"
	hostname=domainProperties.getProperty('wls.admin.Hostname')
	HOSTNAME=hostname.split('.')[0]
	USERID=domainProperties.getProperty('wls.domain.owner.userid')
	dataSources=domainProperties.getProperty('jdbc.datasources')
	if not dataSources is None and len(dataSources)>0:
		DBNAME=domainProperties.getProperty('db.name')
	else:
		DBNAME=str(None)

	CPU_CORES=os.popen("grep pro /proc/cpuinfo -c").read().strip()
	OS_NAME=open('/etc/redhat-release','r').read().split('(')[0].replace(" ", "")
	DOMAINS=domainProperties.getProperty('wls.domain.name')
	WLSVERSION=domainProperties.getProperty('wls.version')
	PATCH_ZIP_NAME=domainProperties.getProperty('opatch.patchZipName')
	patchCMD="echo "+PATCH_ZIP_NAME+" |awk -F'_' '{print $1}'|awk -F 'p' '{print $2}'"
	PATCH_ID=os.popen(patchCMD).read().strip()
	expectScriptHome=domainProperties.getProperty('ConfigNOW.home')+'/core/commands/ant/resources/inventory/'
	expectScriptName='inventoryUpdate.exp'
	inventoryHostUser=domainProperties.getProperty('wls.inventory.user')
	inventoryHostPwd=domainProperties.getProperty('wls.inventory.password')
	inventoryHost=domainProperties.getProperty('wls.inventory.host')
	inventoryUpdateCMD="python3 /home/pegaadmin/confluence-update/update.py -s "+HOSTNAME+" -u "+USERID+" -w "+WLSVERSION+" -d "+DOMAINS+" -p "+PATCH_ID+" -o "+OS_NAME+" -c "+CPU_CORES+" -targetdb "+DBNAME
	expectCMD="expect "+expectScriptHome+expectScriptName+" "+inventoryHostUser+" "+inventoryHostPwd+" "+inventoryHost+" "+'\"'+inventoryUpdateCMD+'\"'
	print expectCMD
	os.system(expectCMD)

def __createUserOverrideSh(domainProperties):
	sslEnable=domainProperties.getProperty('wls.domain.ssl.enable')
	domainDir=domainProperties.getProperty('wls.domain.dir')
	domainName=domainProperties.getProperty('wls.domain.name')
	adminServer_name=domainProperties.getProperty('wls.admin.name')
	ADMIN_SERVER_MEM_ARGS=domainProperties.getProperty('wls.admin.vmarguments')
	ADMIN_SERVER_SSL_ARGS=domainProperties.getProperty('wls.admin.ssl.vmarguments')
	ADMIN_SERVER_GC_ARGS=domainProperties.getProperty('wls.admin.gc.vmarguments')
	full_file_name = domainDir+'/'+domainName+'/bin/setUserOverrides.sh'
	if not os.path.exists(full_file_name):
		print "creating "+str(full_file_name)
		f= open(full_file_name, 'w')
		f.write("#!/bin/sh\n")
		f.write("ADMIN_SERVER_MEM_ARGS=\"%s\"\n"% ADMIN_SERVER_MEM_ARGS)
		f.write("ADMIN_SERVER_GC_ARGS=\"%s\"\n"% ADMIN_SERVER_GC_ARGS)
		if not sslEnable is None and sslEnable.lower() == 'true':
			f.write("ADMIN_SERVER_SSL_ARGS=\"%s\"\n"% ADMIN_SERVER_SSL_ARGS)
#		f.write("SERVER_NAME=\"%s\"\n"% adminServer_name)
#		f.write("export SERVER_NAME\n")
		#f.write('if [ "${SERVER_NAME}" = "" ] : then')
		f.write("if [ \"${SERVER_NAME}\" = \"%s\" ] ; then"% adminServer_name)
		f.write("\n")
		if not sslEnable is None and sslEnable.lower() == 'true':
			f.write('    USER_MEM_ARGS="${ADMIN_SERVER_MEM_ARGS} ${ADMIN_SERVER_GC_ARGS} ${ADMIN_SERVER_SSL_ARGS}"')
		else:
			f.write('    USER_MEM_ARGS="${ADMIN_SERVER_MEM_ARGS} ${ADMIN_SERVER_GC_ARGS}"')
		f.write("\n")
		f.write('fi')
		f.write("\n")
		f.write('export USER_MEM_ARGS')
		f.write("\n")
		f.flush()
		f.close()
		os.system('chmod 750 ' + full_file_name)
	else:
		print "Already Exists : "+full_file_name
		
	if os.path.exists(full_file_name) and sslEnable.lower() == 'true':
		cmd1='if [ `grep "ADMIN_SERVER_SSL_ARGS=" '+full_file_name+' | wc -l` == 0 ]; then sed -i "/ADMIN_SERVER_GC_ARGS=/ a ADMIN_SERVER_SSL_ARGS=\\\"'+ADMIN_SERVER_SSL_ARGS+'\\\"" '+full_file_name+'; fi'
		
		cmd2='if [ `grep "USER_MEM_ARGS=" '+full_file_name+' | grep ADMIN_SERVER_SSL_ARGS | wc -l` == 0 ]; then sed -i \'s/USER_MEM_ARGS="${ADMIN_SERVER_MEM_ARGS} ${ADMIN_SERVER_GC_ARGS}"/USER_MEM_ARGS="${ADMIN_SERVER_MEM_ARGS} ${ADMIN_SERVER_GC_ARGS} ${ADMIN_SERVER_SSL_ARGS}" /g\' '+full_file_name+'; fi'
		os.system(cmd1)
		os.system(cmd1)
	

def updateDomainPropertiesForMonitoring(config):
	domainName=config.getProperty('ConfigNOW.configuration')
	monitoringHome=config.getProperty('ConfigNOW.home')+'/core/commands/ant/resources/monitoring/'
	domainPropFile=monitoringHome+'domain.properties'
	dataSources=config.getProperty('jdbc.datasources')
	if not dataSources is None and len(dataSources)>0:
		if not os.path.exists(domainPropFile):
			file_mode='w'
			#print file_mode
		else:
			file_mode='a+'
			#print file_mode

		if file_mode=='w':
			f= open(domainPropFile, file_mode)
			#print f
			#print "write file"
			f.write(domainName)
			f.flush()
			f.close()
			
		if file_mode=='a+':
			f= open(domainPropFile, file_mode)
			#print f
			#print "write file"
			lines=open(domainPropFile).readlines()
			if domainName not in lines:
				print 'appendig domain'
				f.write("\n"+domainName)
					 
			f.flush()
			f.close()
		
def __update_domainInventory(domainProperties):
	try:
		platformHome=domainProperties.getProperty('ConfigNOW.home')
		wlscliScript= platformHome + '/' + "wlscli.sh"
		env = sys.argv[2]
		config = sys.argv[3]
		updateDOmainInventoryCmd = wlscliScript+' update_inventory '+env+' '+config
		print ('The following command will be used: '+updateDOmainInventoryCmd)
		os.system(updateDOmainInventoryCmd)
		java.lang.Thread.sleep(100)
	except OSError:
		print "Exception while executing commands !"+updateDOmainInventoryCmd
		dumpStack()

def copyFileFxn(src,dst):
	try:
		print "copying to "+ str(dst)
		copyfile(src, dst)
	except IOError, Error:
		print "Unable to copy "+str(src)+"  "+Error
		
def __pegaConfig(domainProperties):
	#hostname_fqdn = socket.getfqdn()
	#hostname =  hostname_fqdn.split('.')[0]
	hostname=java.net.InetAddress.getLocalHost().getHostName()

	domainHome=domainProperties.getProperty('wls.domain.dir')
	domainName=domainProperties.getProperty('wls.domain.name')
	platformHome=domainProperties.getProperty('ConfigNOW.home')
	pegaTop=domainProperties.getProperty('wls.pega.top')
	pegaLogTop=domainProperties.getProperty('wls.pega.log.dir')
	pegaTmpTop=domainProperties.getProperty('wls.pega.temp.dir')
	pegaConfigTop=domainProperties.getProperty('wls.pega.config.dir')
	pegaDirList = []
	if not pegaLogTop is None:
		pegaDirList.append(pegaLogTop)
	if not pegaTmpTop is None:
		pegaDirList.append(pegaTmpTop)
	if not pegaConfigTop is None:
		pegaDirList.append(pegaConfigTop)	

	src=platformHome+'/custom/resources/pega/prpc-plan.xml'
	dst=domainHome+'/'+domainName+'/config/prpc-plan.xml'

	copyFileFxn(src,dst)
	sedCmd='sed -i "s/STAGENAME/'+hostname+'/g" '+dst
	os.system(sedCmd)

	cd('/')
	machinesList = cmo.getMachines()
	serversList = cmo.getServers()
	dixMachine= {}
	if len(machinesList) >0:
		for each_machine in machinesList:
			machineName=each_machine.getName()
			#print machineName
			cd('/Machines/'+machineName+'/NodeManager/'+machineName)
			machineListenAddress= cmo.getListenAddress()
			dixMachine[machineName]= {}
			dixMachine[machineName]['ListenAddress'] = machineListenAddress
			dixMachine[machineName]['Servers'] = []
			
	if len(serversList) >0:
		for each_server in serversList:
			svrName=each_server.getName()
			machineMbean = each_server.getMachine()
			if not machineMbean is None:
				machineName=machineMbean.getName()
				if svrName not in dixMachine[machineName]['Servers']:
					dixMachine[machineName]['Servers'].append(svrName)


	##Create Directories on Local as well as on Remote hosts
	for k,v in dixMachine.iteritems():
		#print k
		if k.find('localpal.com')!=-1:
			k = k.split('.')[0]
		for server in v['Servers']:
			if k == hostname:
	           		#print k +'   '+server
				for dr in pegaDirList:
					pegaDirectory = dr+'/'+server
					#print pegaDirectory
					if not os.path.exists(pegaDirectory):
						os.makedirs(pegaDirectory)
						if dr.find('config') != -1:
							src_config1=platformHome+'/custom/resources/pega/'+domainName+'_config/logging.properties'
							dst_config1=pegaDirectory+'/logging.properties'
							sed_config1='sed -i "s/STAGENAME/'+hostname+'/g" '+dst_config1
							src_config2=platformHome+'/custom/resources/pega/'+domainName+'_config/prlogging.xml'
							dst_config2=pegaDirectory+'/prlogging.xml'
        						sed_config2='sed -i "s/STAGENAME/'+hostname+'/g" '+dst_config2
							dst_config2=pegaDirectory+'/prlogging.xml'
							copyFileFxn(src_config1,dst_config1)
							copyFileFxn(src_config2,dst_config2)
							os.system(sed_config1)
							os.system(sed_config2)
					else:
						print pegaDirectory+' already exists'
			else:
				#print k +'   '+server
				for dr in pegaDirList:
					pegaDirectory = dr+'/'+server
					sshCmd1 = 'ssh '+k+' "if [ -d '+pegaTop+' ]; then if [ ! -d '+pegaDirectory+' ]; then mkdir -p '+pegaDirectory+'; else echo \\"'+pegaDirectory+'already exists\\"; fi; else echo \\"'+pegaTop+' do not exists\\"; fi"'
					os.system(sshCmd1)
				


def __createMServerDomainCommand(domainProperties):
	try:
		platformHome=domainProperties.getProperty('ConfigNOW.home')
		wlscliScript= platformHome + '/' + "wlscli.sh"
		env = sys.argv[2]
		config = sys.argv[3]
		createMServerDomainCommand = wlscliScript+' create_mserver_domain '+env+' '+config
		print ('The following command will be used: '+createMServerDomainCommand)
		os.system(createMServerDomainCommand)
		java.lang.Thread.sleep(100)
	except OSError:
		print "Exception while executing commands !"+createMServerDomainCommand
		dumpStack()
		
def __createPegaConfigCommand(domainProperties):
	try:
		platformHome=domainProperties.getProperty('ConfigNOW.home')
		wlscliScript= platformHome + '/' + "wlscli.sh"
		env = sys.argv[2]
		config = sys.argv[3]
		createPegaConfigCommand = wlscliScript+' pega_config '+env+' '+config
		print ('The following command will be used: '+createPegaConfigCommand)
		os.system(createPegaConfigCommand)
		java.lang.Thread.sleep(100)
	except OSError:
		print "Exception while executing commands !"+createPegaConfigCommand
		dumpStack()
		
def __setUserOverrideCommand(domainProperties):
	try:
		platformHome=domainProperties.getProperty('ConfigNOW.home')
		wlscliScript= platformHome + '/' + "wlscli.sh"
		env = sys.argv[2]
		config = sys.argv[3]
		setUserOverrideCommand = wlscliScript+' admin_args_override '+env+' '+config
		print ('The following command will be used: '+setUserOverrideCommand)
		os.system(setUserOverrideCommand)
		java.lang.Thread.sleep(100)
	except OSError:
		print "Exception while executing commands !"+setUserOverrideCommand
		dumpStack()
		
def Create_SAML2IdentityAsserterAndSAMLAuthenticator(domainProperties):
	domainName=domainProperties.getProperty('wls.domain.name')
	try:
		connectAdminServerOverSSL(domainProperties)
	except Exception, error:
		print 'unable to connect Admin'
		sys.exit('Aborting..')
			
	try:
		startEditSession()
		rlmPath = "/SecurityConfiguration/" + domainName + "/Realms/myrealm"
		cd(rlmPath)
		#	startEditSession()
		saml2iaName = "SAML2IdentityAsserter"
		samlauthName = "SAMLAuthenticator"
		cmo.createAuthenticationProvider(saml2iaName, "com.bea.security.saml2.providers.SAML2IdentityAsserter")
		cmo.createAuthenticationProvider(samlauthName, "weblogic.security.providers.saml.SAMLAuthenticator")
		cd("AuthenticationProviders/SAMLAuthenticator")
		cmo.setControlFlag("SUFFICIENT")
		cd("../DefaultAuthenticator")
		cmo.setControlFlag("SUFFICIENT")
		cd ("../..")
		set('AuthenticationProviders',jarray.array([ObjectName('Security:Name=myrealmSAMLAuthenticator'), ObjectName('Security:Name=myrealmDefaultAuthenticator'), ObjectName('Security:Name=myrealmDefaultIdentityAsserter'), ObjectName('Security:Name=myrealmSAML2IdentityAsserter')], ObjectName))
		saveAndActivateChanges()
	except weblogic.descriptor.BeanAlreadyExistsException, bae:
		print "<Error> Caught BeanAlreadyExistsException exception in Create_SAML2IdentityAsserterAndSAMLAuthenticator, so skipping it !!" + str(bae)
		stopEdit('y')
		pass
	except java.lang.IllegalArgumentException, ia:
		print "<Error> Caught exception in Create_SAML2IdentityAsserterAndSAMLAuthenticator " + str(ia)
		pass
	except Exception, e:
		print "<Error> Caught exception in Create_SAML2IdentityAsserterAndSAMLAuthenticator" + str(e)
		discardChanges()
		sys.exit()
	
def Create_SAML2IdentityPartnerAndConfigureSAML2_GeneralAndServiceProvider(domainProperties):
	domainName=domainProperties.getProperty('wls.domain.name')
	adminserverName=domainProperties.getProperty('wls.admin.name')
	adminHost=domainProperties.getProperty('wls.admin.Hostname') 
	adminPort=domainProperties.getProperty('wls.admin.Port')
	adminPortIncreatmenttoSSL=domainProperties.getProperty('wls.admin.SSLListenPortIncrementOverHttpPort')
	adminSSLPort=int(adminPort)+int(adminPort)
	domainHome=domainProperties.getProperty('wls.domain.dir')+str(domainName)
	idpMetaFileName=domainProperties.getProperty('wls.sso.idpMetaFile.name')
	idpMetaFileLoc=domainProperties.getProperty('wls.sso.idpMetaFile.destination.location')
	metapartnerName=domainProperties.getProperty('wls.sso.metapartner.name')
	idpMetaFile=idpMetaFileLoc+'/'+idpMetaFileName

	try:
		connectAdminServerOverSSL(domainProperties)
	except Exception, error:
		print 'unable to connect Admin '+str(error)
		sys.exit('Aborting..')

	iaPath = "SecurityConfiguration/" + domainName + "/Realms/myrealm/AuthenticationProviders/SAML2IdentityAsserter"
	cd(iaPath)

	try:
		metapartner = cmo.consumeIdPPartnerMetadata(idpMetaFile)
		metapartner.setName(metapartnerName)
		metapartner.setEnabled(true)
		cmo.addIdPPartner(metapartner)
	except weblogic.management.utils.AlreadyExistsException, ae:
		print "<Warning> Caught exception "+ str(ae)
		pass
	
	try:
	#	startEditSession()
		edit()
		startEdit()
		adminServerPath = "/Servers/" + adminserverName + "/SingleSignOnServices/" + adminserverName
		print(adminServerPath)
		cd(adminServerPath)

		PublishedSiteURL = "https://" + adminHost + ":" + str(adminSSLPort) + "/saml2"
		#print(PublishedSiteURL)

		DefaultURL = "https://" + adminHost + ":" + str(adminSSLPort) + "/console"
		#print(DefaultURL)

		#pwd()
		cmo.setReplicatedCacheEnabled(true)
		cmo.setContactPersonGivenName('administrator')
		cmo.setContactPersonType('administrative')
		cmo.setPublishedSiteURL(PublishedSiteURL)
		cmo.setEntityID(domainName)
		cmo.setServiceProviderEnabled(true)
		cmo.setServiceProviderPreferredBinding("HTTP/POST")
		cmo.setDefaultURL(DefaultURL)
		saveAndActivateChanges()

	except weblogic.descriptor.BeanAlreadyExistsException, bae:
		print "<Error> Caught BeanAlreadyExistsException exception in Create_SAML2IdentityPartnerAndConfigureSAML2_GeneralAndServiceProvider, so skipping it !!" + str(bae)
		stopEdit('y')
		pass
	except Exception, e:
		print "<Error> Caught exception in Create_SAML2IdentityPartnerAndConfigureSAML2_GeneralAndServiceProvider" + str(e)
		discardChanges()
		sys.exit()
	
def oudRoles(domainProperties):
	from weblogic.management.security.authentication import UserReaderMBean
	from weblogic.management.security.authentication import GroupReaderMBean

	try:
		connectAdminServerOverSSL(domainProperties)
	except Exception, error:
		print 'unable to connect Admin'
		sys.exit('Aborting..')

	try:
		cd('/')
		serverConfig()
		realm=cmo.getSecurityConfiguration().getDefaultRealm()
		rm = realm.lookupRoleMapper('XACMLRoleMapper')

		expr = rm.getRoleExpression(None,'Admin')
		rm.setRoleExpression(None,'Admin',expr+'|Grp(PP_SSO_GOPS_WLS_ADMIN)')

		expr = rm.getRoleExpression(None,'Monitor')
		rm.setRoleExpression(None,'Monitor',expr+'|Grp(PP_SSO_GOPS_WLS_MONITOR)')

		expr = rm.getRoleExpression(None,'Deployer')
		rm.setRoleExpression(None,'Deployer',expr+'|Grp(PP_SSO_GOPS_WLS_DEPLOYER)')

		expr = rm.getRoleExpression(None,'Operator')
		rm.setRoleExpression(None,'Operator',expr+'|Grp(PP_SSO_GOPS_WLS_OPERATOR)')
	except Exception, e:
		print "<Error> Caught exception in oudRoles" + str(e)
		discardChanges()
		sys.exit()
	
def Set_domain_level_config(domainProperties):
	domainName=domainProperties.getProperty('wls.domain.name')
	adminserverName=domainProperties.getProperty('wls.admin.name')
	adminHost=domainProperties.getProperty('wls.admin.Hostname') 
	adminPort=domainProperties.getProperty('wls.admin.Port')
	adminPortIncreatmenttoSSL=domainProperties.getProperty('wls.admin.SSLListenPortIncrementOverHttpPort')
	adminSSLPort=int(adminPort)+int(adminPort)
	domainHome=domainProperties.getProperty('wls.domain.dir')+str(domainName)

	try:
		connectAdminServerOverSSL(domainProperties)
	except Exception, error:
		print 'unable to connect Admin'
		sys.exit('Aborting..')

	try:
		startEditSession()
		cd ('/')
		domMode = getMBean('/')
		cd("/AdminConsole/"+domainName)
		set ('CookieName', 'JSESSIONID')
		saveAndActivateChanges()
	except weblogic.descriptor.BeanAlreadyExistsException, bae:
		print "<Error> Caught BeanAlreadyExistsException exception in Set_domain_level_config, so skipping it !! " + str(bae)
		stopEdit('y')
		pass
	except Exception, e:
		print "<Error> Caught exception in Set_domain_level_config " + str(e)
		discardChanges()
		sys.exit()

	
def __ssoSetUp(domainProperties):
	domainName=domainProperties.getProperty('wls.domain.name')
	adminserverName=domainProperties.getProperty('wls.admin.name')
	idpMetaFileName=domainProperties.getProperty('wls.sso.idpMetaFile.name')
	idpMetaFileSourceLoc=domainProperties.getProperty('wls.sso.idpMetaFile.source.location')
	idpMetaFileDestinationLoc=domainProperties.getProperty('wls.sso.idpMetaFile.destination.location')
	certFileName=domainProperties.getProperty('wls.sso.cert.name')
	certFileSourceLoc=domainProperties.getProperty('wls.sso.cert.source.location')
	certFileDestinationLoc=domainProperties.getProperty('wls.sso.cert.destination.location')
	idpMetaFullSource=idpMetaFileSourceLoc+'/'+idpMetaFileName
	idepMetaFullDestination=idpMetaFileDestinationLoc+'/'+idpMetaFileName
	certFullFileSource=certFileSourceLoc+'/'+certFileName
	certFullFileDestination=certFileDestinationLoc+'/'+certFileName
	domainHome=domainProperties.getProperty('wls.domain.dir')+'/'+str(domainName)
	#Take config Dir backup
	configDir=domainHome+'/config'
	backupConfigDir=domainHome+'/config_before_sso'
	ldapDir=domainHome+'/servers/'+adminserverName+'/data/ldap'
	backupLdapDir=domainHome+'/servers/'+adminserverName+'/data/ldap_before_sso'

	try:
		if not os.path.isdir(backupConfigDir): # This one line does the trick
			copytree(configDir, backupConfigDir)
		else:
			print "Backup already Exists"
	# Directories are the same
	except OSError , e:
		print('Directory not copied. Error: %s' % e)
		
	try:
		if not os.path.isdir(backupLdapDir): # This one line does the trick
			copytree(ldapDir, backupLdapDir)
		else:
			print "Backup already Exists"
	# Directories are the same
	except OSError , e:
		print('Directory not copied. Error: %s' % e)

	try:
		copyfile(idpMetaFullSource, idepMetaFullDestination)
		#copyfile(certFullFileSource, certFullFileDestination)
	except IOError, Error:
		print "Unable to copy File  "+str(Error)
		
	try:
		#copyfile(idpMetaFullSource, idepMetaFullDestination)
		copyfile(certFullFileSource, certFullFileDestination)
	except IOError, Error:
		print "Unable to copy File  "+str(Error)
		
	print "Creating SAML2 Identity Asserter And SAML Authenticator"
	Create_SAML2IdentityAsserterAndSAMLAuthenticator(domainProperties)
	print "Mapping OUD Roles ......."
	oudRoles(domainProperties)
	print "Changing the Console Cookie Name "
	Set_domain_level_config(domainProperties)
	__startAdminServerwithScript(domainProperties)
	java.lang.Thread.sleep(30000)
	print "Creating SAML2 Identity Partner and configuring SAML2.0 General and Service Provider Configuration ....."
	Create_SAML2IdentityPartnerAndConfigureSAML2_GeneralAndServiceProvider(domainProperties)
	__startAdminServerwithScript(domainProperties)
	
	
def getWLSMachineandandExecuteSecondary(domainProperties):
	platformHome=domainProperties.getProperty('ConfigNOW.home')
	hostname=java.net.InetAddress.getLocalHost().getHostName()
	secondaryScript=platformHome+'/custom/resources/secondary/execute_secondary.sh'
	try:
		connectAdminServerOverSSL(domainProperties)
	except Exception, error:
		print 'unable to connect Admin'
	cd('/')
	machinesList = cmo.getMachines()
	machineNameList = []
	if len(machinesList) >0:
		for each_machine in machinesList:
			machineName=each_machine.getName()
			if machineName.find(hostname)==-1 and machineName not in machineNameList:
				#if machineName not in machineNameList:
				machineNameList.append(machineName)

	disconnect()		

	for each_machine_name in machineNameList:
		secondaryCommand="sh "+secondaryScript+" "+each_machine_name
		os.system(secondaryCommand)

def __shutdownAdminServer():
	if connected == 'true':
		print 'Shutting down the Admin Server...'
		shutdown(force='true', block='true')

		
def __configureJDBCSSLCommand(domainProperties):
	try:
		platformHome=domainProperties.getProperty('ConfigNOW.home')
		wlscliScript= platformHome + '/' + "wlscli.sh"
		env = sys.argv[2]
		config = sys.argv[3]
		configureJDBCSSLCommand = wlscliScript+' configure_jdbc_ssl '+env+' '+config
		print ('The following command will be used: '+configureJDBCSSLCommand)
		os.system(configureJDBCSSLCommand)
		java.lang.Thread.sleep(100)
	except OSError:
		print "Exception while executing commands !"+configureJDBCSSLCommand
		dumpStack()
		
def __generateSecondaryHostArtifacts(domainProperties):
	try:
		platformHome=domainProperties.getProperty('ConfigNOW.home')
		wlscliScript= platformHome + '/' + "wlscli.sh"
		env = sys.argv[2]
		config = sys.argv[3]
		configureSecondaryCommand = wlscliScript+' secondary '+env+' '+config
		print ('The following command will be used: '+configureSecondaryCommand)
		os.system(configureSecondaryCommand)
		java.lang.Thread.sleep(100)
	except OSError:
		print "Exception while executing commands !"+configureSecondaryCommand
		dumpStack()

def __createUserCommand(domainProperties):
	try:
		platformHome=domainProperties.getProperty('ConfigNOW.home')
		wlscliScript= platformHome + '/' + "wlscli.sh"
		env = sys.argv[2]
		config = sys.argv[3]
		createUserCommand = wlscliScript+' create_user '+env+' '+config
		print ('The following command will be used: '+createUserCommand)
		os.system(createUserCommand)
		java.lang.Thread.sleep(100)
	except OSError:
		print "Exception while executing commands !"+createUserCommand
		dumpStack()
