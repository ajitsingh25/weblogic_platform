if __name__ == '__main__': 
    from wlstModule import *#@UnusedWildImport

import os,re,threading

#from jarray              import array
from java.net            import InetAddress
from java.lang           import System, UnsupportedOperationException
from java.util           import Properties
from java.io             import FileInputStream, File
from java.lang.reflect   import UndeclaredThrowableException
from javax.management    import MBeanException, RuntimeMBeanException
from javax.xml.parsers   import DocumentBuilderFactory, DocumentBuilder
from org.w3c.dom         import Document, Element, Node, NodeList 
#from weblogic.descriptor import BeanAlreadyExistsException
import common.logredirect as logredirects
execfile('wlst/common.py')



class DoNotRevealPassword(threading.Thread):
    def __init__ (self):
        threading.Thread.__init__(self)
        self.stopOnEvent = threading.Event()
    def run(self):
        Thread.currentThread().setPriority(Thread.MAX_PRIORITY)
        while not self.stopOnEvent.isSet():
            sys.stdout.write("\010" + "*")
            Thread.currentThread().sleep(1)
    def stopThread(self): 
        self.stopOnEvent.set()


    
previousNumberOfManagedServers=0
machineName=""
#Create an empty dictionary to store the managed servers in the domain
domainServersDictionary={}

#Create an empty dictionary to store the clusters in the domain
domainClustersDictionary={}

#Create an empty dictionary to store the physical machines in the domain
domainMachinesDictionary={}

#Create an empty dictionary to store the mapping between the managed servers and the machines on which they are deployed
domainServersMachineMappingDictionary={}

#Create an empty dictionary to store the mapping between the managed servers and the clustes to chich they belong
domainServersClusterMappingDictionary = {}

#Global variable for holding a flag which indicates if the domain already exists or not
existingDomainFlag=0

#Function to discard any changes made as part of the edit session in case of any error
def discardChanges():
    log.info('Discarding any changes made as part of this edit session...\n')
    try:
        cfgManager = getConfigManager()
        try:
            cfgManager.getChanges()
            log.info('There are existing edit sessions with pending changes\n')
            edit()
            log.info('Undoing any pending changes')
            undo(unactivateChanges='true', defaultAnswer='y')
            log.info('Cancelling any existing edit sessions\n')
            cancelEdit(defaultAnswer='y')
            print "\n"
            if connected=="false":
                disconnect()
            exit(exitcode=1)
        except:
            log.info('There are no existing edit sessions\n')
            cancelEdit(defaultAnswer='y')
            if connected=="true":
                disconnect()
            exit(exitcode=1)
    except Exception, e:
        log.error('Error occurred while cancelling any existing edit sessions\n')
        log.error('Exception is : ',  e)
        log.error('The stack trace is : ')
        dumpStack()
        print "\n"
        undo(unactivateChanges='true', defaultAnswer='y')
        cancelEdit(defaultAnswer='y')
        if connected=="true":
            disconnect()
        exit(exitcode=1)

#Function for check if the tag is empty
def checkIfTagIsEmpty(domXMLParser, tagName):
    try:
        log.debug('Checking if tag : ' + tagName + ' is empty in the configuration XML file')
        #log.debug('Checking if tag : ' + tagName + ' is empty in the configuration XML file\n')
        if domXMLParser.getElementsByTagName(tagName).item(0).childNodes.item(0) == None:
            return 0
        else:
            #log.debug('Tag : ' + tagName + ' is not empty in the configuration XML file\n')
            log.debug('Tag : ' + tagName + ' is not empty in the configuration XML file')
            return 1
    except Exception, e:
        #log.debug('Exception ocurred while checking if tag : ' + tagName + ' is empty in the configuration XML file\n')
        log.error('Exception ocurred while checking if tag : ' + tagName + ' is empty in the configuration XML file')
        dumpStack()
        discardChanges()

#Function for getting the tag value from the configuration XML
def getTagValue(domXMLParser, tagName):
    try:
        log.debug('Getting the value for the tag : ' + tagName + ' from the configuration XML file')
        #log.debug('Getting the value for the tag : ' + tagName + ' from the configuration XML file\n')
        log.debug('Value of the tag : ' + tagName + ' is : ' + domXMLParser.getElementsByTagName(tagName).item(0).childNodes.item(0).data + '\n')
        #log.debug('Value of the tag : ' + tagName + ' is : ' + domXMLParser.getElementsByTagName(tagName).item(0).childNodes.item(0).data + '\n')
        return domXMLParser.getElementsByTagName(tagName).item(0).childNodes.item(0).data
    except Exception, e:
        log.error('Exception ocurred while getting the value for the tag : ' + tagName + ' from the configuration XML file\n')
        dumpStack()
        discardChanges()

#Function for changing location to the edit tree and starting a new edit sesseion
def startEditSession():
    log.debug('Starting an edit session for making changes to the Weblogic configuration\n')
    #log.debug('Starting an edit session for making changes to the Weblogic configuration\n')
    redirect('/dev/null','false')
    edit()
    startEdit()

#Function saving the changes during the edit session and activating them
#If there are any problems during activation discard any changes made during the edit session and cancel the edit session
def saveAndActivateChanges():
    log.debug('Activating all the changes made during the existing edit session\n')
    #log.debug('Activating all the changes made during the existing edit session\n')

    try:
        save()
        activate()
	redirect('/dev/null','true')
    except Exception, e:
        log.error('Error in activating the changes made during the existing edit session\n')
        dumpStack()
        log.error('Discarding all the changes made during the existing edit session\n')
        discardChanges()

#Function to start the Weblogic Administration Server
def createDomainAndStartAdminServer(beaHome, domainNameFromConfigurationFile, domainHomeFromConfigurationFile, weblogicAdminUserName, weblogicAdminPassword, adminServerName, adminServerListenAddress, adminServerListenPort, adminServerStartArguments):
    global existingDomainFlag
    try:
        if adminServerListenAddress == None:
            adminServerListenAddress = java.net.InetAddress.getLocalHost().getHostAddress()

        adminServerURL= "t3://" + adminServerListenAddress + ":" + adminServerListenPort
        log.info('Trying to connect to the Weblogic Admin Server at : ')
        hideDumpStack("true")    

        # try connecting to a running server if it is already running ...
        if connected == "false":
            try:
                connect(weblogicAdminUserName, weblogicAdminPassword, adminServerURL)
                existingDomainFlag=1
            except WLSTException:
                log.info('No server is running at ' + adminServerURL + ', the script will start a new server')
                #log.debug('No server is running at ' + adminServerURL + ', the script will start a new server\n')

        domainPath = str(domainHomeFromConfigurationFile) + '/'+ str(domainNameFromConfigurationFile)    

        hideDumpStack("false")    
        if connected=="false":
            if os.path.isdir(domainPath):
                log.debug('The domain directory ' + domainPath + ' already exists. Staring the Weblogic Admin Server using the existing configuration\n')
                existingDomainFlag=1
            else:
                log.debug('The domain directory ' + domainPath + ' does not exist. The directory will be created as part of starting the Weblogic Admin Server for the domain\n')

            log.info('Starting a brand new Weblogic Admin Server at ' + adminServerURL + ' with server name '+adminServerName + '\n')
            log.debug('Please see the server log files for startup messages available at ' + domainPath + '\n')

            if adminServerStartArguments != None:
                startServer(adminServerName, domainNameFromConfigurationFile, adminServerURL, weblogicAdminUserName, weblogicAdminPassword, domainPath, block='true', timeout=240000, jvmArgs=adminServerStartArguments)
            else:
                startServer(adminServerName, domainNameFromConfigurationFile, adminServerURL, weblogicAdminUserName, weblogicAdminPassword, domainPath, block='true', timeout=240000)

            log.info('Started Server. Trying to connect to the Weblogic Admin Server at : ' + adminServerURL + '\n')
            connect(weblogicAdminUserName, weblogicAdminPassword, adminServerURL)

            if connected == 'false':
                stopExecution('You need to be connected.')

        log.info('Successfully connected to the Weblogic Admin Server at : ' + adminServerURL + '\n')

        log.debug('Enrolling the machine with the Node Manager...\n')
        nmEnroll(domainDir=domainPath)

        #Get all the servers in the domain and store it in a dictionary mapping it to physical machine on which it is running
        cd('/')
        domainServersArray=cmo.getServers()
        for i in range(len(domainServersArray)):
            domainServersDictionary[domainServersArray[i].getName()]='Server'

        #Get all the clusters in the domain and store it in a dictionary
        cd('/')
        domainClustersArray=cmo.getClusters()
        for i in range(len(domainClustersArray)):
            domainClustersDictionary[domainClustersArray[i].getName()]='Cluster'

        #Get all the machines in the domain and store it in a dictionary
        cd('/')
        domainMachinesArray=cmo.getMachines()
        for i in range(len(domainMachinesArray)):
            domainMachinesDictionary[domainMachinesArray[i].getName()]='Machine'

    except Exception, e:
        log.error('Exception ocurred while writing the domain/starting the Weblogic Admin Server. Aborting...\n')
        dumpStack()
        exit(exitcode=1)

#Function for creating a Weblogic Admin server
def setAdminServerListenAddressConfiguration(adminServerName, adminServerListenAddress, domainNameFromConfigurationFile, clearTextCredentialAccessEnabledFromConfigurationFile, adminServerStartArguments):
    log.debug('Setting additional configuration for Weblogic Admin Server...\n')
   
    try:
        cd('/Servers/' + adminServerName)
        existingWeblogicAdminServerListenAddress = get('ListenAddress')

        if str(existingWeblogicAdminServerListenAddress) != '':
            log.debug('Weblogic Admin Server is currently configured to listen on : ' + existingWeblogicAdminServerListenAddress + '. Modifying the listen address so that Weblogic Admin Server can listen on all addresses on the machine...\n')
            startEditSession()

            cd('/Servers/' + adminServerName)
            set("ListenAddress", adminServerListenAddress)
            saveAndActivateChanges()

            log.debug('\nSuccessfully set the listen address for Weblogic Admin Server to listen on all addresses on the machine...\n')

        startEditSession()

        #set("ListenAddress", "")
        log.debug('Enabling tunneling for the Weblogic Admin Server...\n')
        set("TunnelingEnabled", "true")

        #log.debug('Setting the machine to empty value for the Weblogic admin server...\n')
        #set("Machine", "")
        cd('/Servers/' + adminServerName +'/ServerStart/' + adminServerName) 
        if adminServerStartArguments != None:
            log.debug('Server start arguments for Admin server : ' + adminServerName +  ' are specified as : ' + str(adminServerStartArguments) + '\n')
            set("Arguments", adminServerStartArguments)

        
        cd('/SecurityConfiguration/' + domainNameFromConfigurationFile)
        securityAttributes=ls(returnMap='true')
        for attributeName in securityAttributes:
            if attributeName == "ClearTextCredentialAccessEnabled":
                startEditSession()
                log.debug('Setting configuration for ClearTextCredentialAccessEnabled for the domain...\n')
                set("ClearTextCredentialAccessEnabled", clearTextCredentialAccessEnabledFromConfigurationFile)
                cd ('/')
                set("ProductionModeEnabled","true")
                
                saveAndActivateChanges()
    except Exception, e:
        log.error('Error in setting the listen address for Weblogic Admin Server to listen on all addresses on the machine...\n')
        dumpStack()
        discardChanges()

def setAdminServerSSLConfiguration(adminServerName, adminServerSSLListenPort):
    try:    
        if adminServerSSLListenPort != None:
            log.info('Setting SSL configuration for Weblogic Admin Server...\n')
            startEditSession()

            cd('/Servers/' + adminServerName + '/SSL/' + adminServerName)
            log.debug('Setting the name for the SSL bean for the Weblogic Admin Server...\n')
            set('Name', adminServerName)

            log.debug('Enabling SSL communication for Weblogic Admin Server...\n')
            set('Enabled', 'true')

            log.debug('Setting SSL listen port for Weblogic Admin Server to : ' + adminServerSSLListenPort + '\n')
            set('ListenPort', adminServerSSLListenPort)

            log.debug('Setting two way SSL flag for : ' + serverName + ' to : false...\n')
            set('TwoWaySSLEnabled', 'false')

            log.debug('Setting HostnameVerifier to null for Weblogic Admin Server\n')
            cmo.setHostnameVerifier(None)

            log.debug('Setting HostNameVerificationIgnored flag to true for Weblogic Admin Server\n')
            cmo.setHostnameVerificationIgnored(true)

            saveAndActivateChanges()

            log.info('\nSuccessfully set the SSL configuration for Weblogic Admin Server...\n')
    except Exception, e:
        log.error('Error in setting the SSL configuration for Weblogic Admin Server...\n')
        dumpStack()
        discardChanges()

#Function for restarting the Weblogic Admin server
#def shutdownAdminServer(beaHome, domainNameFromConfigurationFile,weblogicAdminUsername, weblogicAdminPassword, adminServerName):
def shutdownAdminServer(adminServerName):
    #domainPath = str(beaHome) + '/user_projects/domains/' + str(domainNameFromConfigurationFile)    
    
    #log.debug('Enrolling the machine with the Node Manager...\n')
    #nmEnroll(domainDir=domainPath)
    
    #log.debug('Disconnecting from the Weblogic Admin Server so that it can be restarted with the new configuration...\n')
    #disconnect()
    
    #log.debug('Connecting to the nodemanager on the local machine...\n')
    #nmConnect(username=weblogicAdminUsername, password=weblogicAdminPassword, domainName=domainNameFromConfigurationFile, domainDir=beaHome + '/user_projects/domains/' + domainNameFromConfigurationFile)
    
    log.info('Shutting down the Weblogic Admin Server so that it can be restarted with the new configuration...\n')
    shutdown(adminServerName, 'Server', ignoreSessions='true', force='true', block='true')
    #nmKill(adminServerName)

    #log.debug('Restarting the Weblogic Admin Server the new configuration...\n')
    #nmStart(serverName = adminServerName, domainDir = beaHome + '/user_projects/domains/' + domainNameFromConfigurationFile)

    #log.debug('Disconnecting from the nodemanager...\n')
    #nmDisconnect()    

    #log.debug('Successfully disconnected from the nodemanager...\n')

#Function for setting properties for a Unix machine
def setPropertiesForUnixMachine(machineName, fullyQualifiedHostName, listenAddress):
    try:    
        startEditSession()
        cd('/Machines/' + machineName + '/NodeManager/' + machineName)

        if listenAddress == None:
            log.debug('Setting listen address for NodeManager of machine : ' + machineName + ' to : empty\n')
            set("ListenAddress", "")
            set("ListenPort", "6666")
        elif str(listenAddress).find("REPLACE_IP_ADDRESS") != -1:
            log.debug('Replacing the listen address : ' + listenAddress + ' with the IP Address of : ' + machineName + '\n')
            listenAddressReplaced = java.net.InetAddress.getByName(fullyQualifiedHostName).getHostAddress()
            log.debug('Setting listen address for NodeManager of machine : ' + machineName + ' to : ' + listenAddressReplaced + '\n')
            set("ListenAddress", listenAddressReplaced)
            set("ListenPort", "6666")
        elif str(listenAddress).find("REPLACE_HOSTNAME") != -1:
            log.debug('Replacing the listen address : ' + listenAddress + ' with the host name : ' + fullyQualifiedHostName + '\n')
            set("ListenAddress", fullyQualifiedHostName)
            set("ListenPort", "6666")
        else:
            log.debug('Setting listen address for NodeManager of machine : ' + machineName + ' to : ' + listenAddress + '\n')
            set("ListenAddress", listenAddress)
            set("ListenPort", "6666")
        saveAndActivateChanges()

        log.info('Successfully set the listen address for NodeManager of machine : ' + machineName + '\n')
    except Exception, e:
        log.error('Error in setting the listen address for NodeManager of machine : ' + machineName + ' to : ' + listenAddress + '\n')
        dumpStack()
        discardChanges()

#Function for creating a Unix machine in Weblogic configuration
def createUnixMachine(machineName, fullyQualifiedHostName, listenAddress):
    cd('/')

    try:
        log.debug('Checking if a Unix machine : ' + machineName + ' exists in the domain ...\n')

        theBean = cmo.lookupMachine(machineName)

        if theBean == None:
            log.info('A Unix machine with name ' + machineName + ' does not exist in the domain. Creating a new Unix machine ...\n')

            startEditSession()
            cd('/')
            cmo.createUnixMachine(machineName)
            saveAndActivateChanges()

            log.debug('Successfully created Unix machine with name ' + machineName + ' in the domain...\n')
            
            domainMachinesDictionary[str(machineName)]='Machine'

            log.debug('Successfully added machine with name ' + machineName + ' to the machines dictionary...\n')
            
            log.debug('Setting the properties for machine with name ' + machineName + '...\n')
            
            setPropertiesForUnixMachine(machineName, fullyQualifiedHostName, listenAddress)
            
            log.info('Successfully set the properties for machine with name ' + machineName + '...\n')
        else:
            log.info('A Unix machine with name ' + machineName + ' already exists in the domain. Bypassing creating it again ...\n')
            
            domainMachinesDictionary[str(machineName)]='Machine'

            log.debug('Successfully added machine with name ' + machineName + ' to the machines dictionary...\n')

            log.debug('Setting the properties for machine with name ' + machineName + '...\n')
            
            setPropertiesForUnixMachine(machineName, fullyQualifiedHostName, listenAddress)
            
            log.info('Successfully set the properties for machine with name ' + machineName + '...\n')
    except java.lang.UnsupportedOperationException, usoe:
        dumpStack()
        pass
    except weblogic.descriptor.BeanAlreadyExistsException, bae:
        log.info('A Unix machine with name ' + machineName + ' already exists in the domain. Bypassing creating it again ...\n')
        pass
    except java.lang.reflect.UndeclaredThrowableException, udt:
        dumpStack()
        pass
    except Exception, e:
        log.error('Error in creating the Unix machine with name ' + machineName + ' in the domain...\n')
        dumpStack()
        discardChanges()

#Function for creating a cluster
def createCluster(clusterName):
    cd('/')
    
    try:
        log.debug('Checking if a cluster with name : ' + clusterName + ' exists in the domain ...\n')

        theBean = cmo.lookupCluster(clusterName)

        if theBean == None:
            log.debug('A cluster with name ' + clusterName + ' does not exist in the domain. Creating a new cluster ...\n')

            startEditSession()
            cmo.createCluster(clusterName)
            saveAndActivateChanges()

            log.info('Successfully created a cluster with name ' + clusterName + ' in the domain...\n')

            domainClustersDictionary[str(clusterName)]='Cluster'
            
            log.debug('Successfully added cluster with name ' + clusterName + ' to the clusters dictionary...\n')
        else:
            log.info('A cluster with name ' + clusterName + ' already exists in the domain. Bypassing creating it again ...\n')
            
            domainClustersDictionary[str(clusterName)]='Cluster'
            
            log.debug('Successfully added cluster with name ' + clusterName + ' to the clusters dictionary...\n')
    except java.lang.UnsupportedOperationException, usoe:
        dumpStack()
        pass
    except weblogic.descriptor.BeanAlreadyExistsException, bae:
        log.info('A cluster with name ' + clusterName + ' already exists in the domain. Bypassing creating it again ...\n')
        domainClustersDictionary[str(clusterName)]='Cluster'
        log.debug('Successfully added cluster with name ' + clusterName + ' to the clusters dictionary...\n')
        pass
    except java.lang.reflect.UndeclaredThrowableException, udt:
        dumpStack()
        pass
    except Exception, e:
        log.error('Error in creating a cluster with name ' + clusterName + ' in the domain...')
        dumpStack()
        discardChanges()

#Function for setting properties of cluster
def setAttributesForCluster(clusterName, clusterChannelName):
    try:    
        log.info('Setting attributes for cluster : ' + clusterName + '\n')

        startEditSession()
        cd('/Clusters/' + clusterName)

        log.debug('Setting broadcast channel for the cluster : ' + clusterName + '\n')
        set("ClusterBroadcastChannel", clusterChannelName)

        log.debug('Setting messaging mode for the cluster : ' + clusterName + '\n')
        set("ClusterMessagingMode", "unicast")
    
        saveAndActivateChanges()
    except Exception, e:
        log.error('Error in setting the attributes for the cluster : ' + clusterName + '...\n')
        dumpStack()
        discardChanges()

#Function for creating a managed server
def createManagedServer(serverName):
    cd('/')
    
    try:
        log.info('Checking if a managed server : ' + serverName + ' exists in the domain ...\n')

        theBean = cmo.lookupServer(serverName)
        if theBean == None:
            log.debug('A managed server with name ' + serverName + ' does not exist in the domain. Creating a new server ...\n')

            startEditSession()
            cmo.createServer(serverName)
            saveAndActivateChanges()

            log.info('Successfully created a managed server with name ' + serverName + ' in the domain...\n')
            
            domainServersDictionary[str(serverName)]='Server'
            
            log.debug('Successfully added server with name ' + serverName + ' to the servers dictionary...\n')
        else:
            log.info('A managed server with name ' + serverName + ' already exists in the domain. Bypassing creating it again ...\n')

            domainServersDictionary[str(serverName)]='Server'
            
            log.debug('Successfully added server with name ' + serverName + ' to the servers dictionary...\n')
    except java.lang.UnsupportedOperationException, usoe:
        dumpStack()
        pass
    except weblogic.descriptor.BeanAlreadyExistsException, bae:
        log.info('A  managed server with name ' + serverName + ' already exists in the domain. Bypassing creating it again ...\n')
            
        domainServersDictionary[str(serverName)]='Server'
            
        log.debug('Successfully added server with name ' + serverName + ' to the servers dictionary...\n')
        pass
    except java.lang.reflect.UndeclaredThrowableException, udt:
        dumpStack()
        pass
    except Exception, e:
        log.error('Error in creating a managed server with name ' + serverName + ' in the domain...\n')
        dumpStack()
        discardChanges()

#Function to create a Network Access Point for a managed server
def createNetworkAccessPoint(serverName, clusterChannelName):
    cd('/Servers/' + serverName)

    try:
        log.debug('Checking if a network access point already exists for the managed server : ' + serverName + '...\n')

        theBean = cmo.lookupNetworkAccessPoint(clusterChannelName)
        if theBean == None:
            log.debug('A network access point by the name : ' + clusterChannelName + ' does not exist for the managed server : ' + serverName + '...\n')

            startEditSession()
            cmo.createNetworkAccessPoint(clusterChannelName)
            #saveAndActivateChanges()

            log.info('Successfully created a network access point by name : ' + clusterChannelName + ' for the managed server : ' + serverName + '...\n')
        else:
            log.info('Network access point ' + clusterChannelName + ' already exists for the managed server ' + serverName + '...\n')

    except java.lang.UnsupportedOperationException, usoe:
        dumpStack()
        pass
    except weblogic.descriptor.BeanAlreadyExistsException,bae:
        log.info('Network access point ' + clusterChannelName + ' already exists for the managed server : ' + serverName + '...\n')
        pass
    except java.lang.reflect.UndeclaredThrowableException,udt:
        dumpStack()
        pass
    except Exception, e:
        log.error('Error in creating a network access point by name : ' + clusterChannelName + ' for the managed server : ' + serverName + '...\n')
        dumpStack()
        discardChanges()

#Function for assigning a managed server to a cluster
def assignServerToCluster(serverName, clusterName):
    try:    
        if (not domainClustersDictionary.has_key(str(clusterName))):
            log.info('Cluster : ' + clusterName + ' does not exist in the domain. So managed server : ' + serverName + ' cannot be assigned to it...\n')
            log.debug('Aborting...\n')
            discardChanges()

        log.debug('Getting a reference to cluster : ' + clusterName + ' so that managed server : ' + serverName + ' can be assigned to it...\n')

        cd('/Servers/' + serverName)
        clusterReference = getMBean('/Clusters/' + clusterName)

        startEditSession()
        log.info('Assigning managed server : ' + serverName + ' to cluster : ' + clusterName + ' ...\n')
        cd('/Servers/' + serverName)
        cmo.setCluster(clusterReference)
        saveAndActivateChanges()
    
        domainServersClusterMappingDictionary[str(serverName)] = clusterName
    
        log.debug('Successfully added server with name ' + serverName + ' to the dictionary containing mapping between servers and clusters...\n')
    except Exception, e:
        log.error('Error in assigning managed server : ' + serverName + ' to cluster : ' + clusterName + ' ...\n')
        dumpStack()
        discardChanges()

#Function for assigning a managed server to a machine
def assignServerToMachine(serverName, machineName):
    try:    
        #if (not domainMachinesDictionary.has_key(str(machineName))):
        #    log.debug('Machine : ' + machineName + ' does not exist in the domain. So managed server : ' + serverName + ' cannot be assigned to it...\n')
        #    log.debug('Aborting...\n')
        #    discardChanges()

        log.debug('Getting a reference to machine : ' + machineName + ' so that managed server : ' + serverName + ' can be assigned to it...\n')

        cd('/Servers/' + serverName)
        machineReference = getMBean('/Machines/' + machineName)

        startEditSession()
        cd('/Servers/' + serverName)
        log.info('Assigning managed server : ' + serverName + ' to machine : ' + machineName + ' ...\n')
        cmo.setMachine(machineReference)
        saveAndActivateChanges()

        log.debug('\nSuccessfully assigned managed server : ' + serverName + ' to machine : ' + machineName + ' ...\n')

        domainServersMachineMappingDictionary[serverName] = machineName

        log.debug('\nSuccessfully added the managed server to server - machine mapping dictionary...\n')
    except Exception, e:
        log.error('Error in assigning managed server : ' + serverName + ' to machine : ' + machineName + ' ...\n')
        dumpStack()
        discardChanges()

#Function for setting the HTTP configuration for a managed server
def setHttpConfigurationForServer(serverName, httpListenPort, managedServerListenAddress):
    try:    
        log.info('Setting the HTTP configuration for : ' + serverName + ' ...\n')

        startEditSession()
        cd('/Servers/' + serverName)
    
        #log.debug('Setting HTTP listen port for : ' + serverName + ' to : ' + httpListenPort + ' ...\n')
        set("ListenPort", str(httpListenPort))

        if managedServerListenAddress != None:
            log.debug('Setting HTTP Listen address for : ' + serverName + ' to : ' + managedServerListenAddress + '\n')
            set("ListenAddress", managedServerListenAddress)
        else:
            log.debug('Setting HTTP Listen address for : ' + serverName + ' to empty so that it can listen on all addresses on the host...\n')
            set("ListenAddress", "")
    
        saveAndActivateChanges()

        log.debug('\nSuccessfully set the HTTP configuration for : ' + serverName + ' ...\n')
    except Exception, e:
        log.error('Error in setting the HTTP configuration for : ' + serverName + ' ...\n')
        dumpStack()
        discardChanges()

#Function for setting the SSL configuration for a managed server
def setSSLConfigurationForServer(serverName, sslListenPort, sslEnabled, twoWaySSLEnabled, nonSSLDisabled):
    try:    
        log.info('Setting the SSL configuration for : ' + serverName + ' ...\n')
    
        startEditSession()
        cd('/Servers/' + serverName + '/SSL/' + serverName)

        log.debug('Setting the name for the SSL MBean for : ' + serverName + ' to : ' + serverName + ' ...\n')
        set("Name", serverName)

        log.debug('Setting SSL enabled flag for : ' + serverName + ' to : ' + sslEnabled + ' ...\n')
        set("Enabled", sslEnabled)
    
        log.debug('Setting SSL listen port for : ' + serverName + ' to : ' + sslListenPort + ' ...\n')
        set("ListenPort", sslListenPort)

        log.debug('Setting login timeout for : ' + serverName + ' to : 25000 milliseconds...\n')
        set("LoginTimeoutMillis", "25000")

        log.debug('Setting HostnameVerifier to null for the managed server\n')
        cmo.setHostnameVerifier(None)
    
        log.debug('Setting the flag for ignoring hostname verification to true for : ' + serverName + ' ...\n')
        set("HostnameVerificationIgnored", "true")
    
        log.debug('Setting the two way ssl enabled flag to false for : ' + serverName + ' ...\n')
        set("TwoWaySSLEnabled", "false")
    
        log.debug('Setting client certificate enforced flag to false for : ' + serverName + ' ...\n')
        set("ClientCertificateEnforced", "false")

        if (twoWaySSLEnabled != None) and (twoWaySSLEnabled == "true"):
            log.debug('Setting two way SSL flag for : ' + serverName + ' to : ' + twoWaySSLEnabled + ' ...\n')
            set("TwoWaySSLEnabled", twoWaySSLEnabled)
            set("ClientCertificateEnforced", "true")
    
        cd('/Servers/' + serverName)

        log.debug('Setting the flag for allowing reverse DNS lookups to true for : ' + serverName + ' ...\n')
        set("ReverseDNSAllowed", "true")
        if (nonSSLDisabled != None) and (nonSSLDisabled == "true"):
            log.debug('Disabling the non-SSL port for : ' + serverName + ' to : ' + nonSSLDisabled + ' ...\n')
            set("ListenPortEnabled", "false")
    
        saveAndActivateChanges()

        log.debug('Successfully set the SSL configuration for : ' + serverName + ' ...\n')
    except Exception, e:
        log.error('Error in setting the SSL configuration for : ' + serverName + ' ...\n')
        dumpStack()
        discardChanges()

#Function for setting the logging properties for a managed server
def setLoggingPropertiesForServer(serverName, logFileLocation, fileCount):
    try:    
        log.info('Setting the logging file properties for : ' + serverName + ' ...\n')
    
        startEditSession()
        cd('/Servers/' + serverName + '/Log/' + serverName)
    
        log.debug('Setting flag to rotate the log files by time ...\n')
        set("RotationType", "byTime")
    
        log.debug('Setting flag to rotate the log files on startup to false ...\n')
        set("RotateLogOnStartup", "false")
    
        #log.debug('Setting count of the log files to  ' + fileCount + ' ...\n')
        set("FileCount", "14")

        if (str(logFileLocation).find("REPLACE_MANAGED_SERVER_NAME") != -1) or (str(logFileLocation).find("REPLACE_DOMAIN_NAME") != -1):
            log.debug('Replacing managed server name/domain name in the log file location...\n')
            logFileLocation = str(logFileLocation).replace('REPLACE_MANAGED_SERVER_NAME', serverName)
            logFileLocation = str(logFileLocation).replace('REPLACE_DOMAIN_NAME', domainName)
        log.debug('Setting log file location for managed server : ' + serverName + ' to : ' + logFileLocation + '/' + serverName + '/' + serverName + '.log ...\n')
        set("FileName", logFileLocation + '/' + serverName + '.log')
    
        saveAndActivateChanges()

        log.debug('\nSuccessfully set the logging file properties for : ' + serverName + ' ...\n')
    except Exception, e:
        log.error('Error in setting the logging file properties for : ' + serverName + ' ...\n')
        dumpStack()
        discardChanges()

#Function for setting the logging properties for the web server on a managed server
def setLoggingPropertiesForWebServer(serverName, logFileLocation, fileCount):
    try:    
        log.info('Setting the logging file properties for the web server on : ' + serverName + ' ...\n')
    
        startEditSession()
        cd('/Servers/' + serverName + '/WebServer/' + serverName + '/WebServerLog/' + serverName)
    
        log.debug('Setting flag to rotate the log files by time ...\n')
        set("RotationType", "byTime")
    
        log.debug('Setting flag to rotate the log files on startup to false ...\n')
        set("RotateLogOnStartup", "false")
    
        log.debug('Setting count of the log files to  ' + str(fileCount) + ' ...\n')
        set("FileCount", fileCount)

        #log.debug('Setting the flag for limiting the number of log files to false...\n')
        #set("NumberOfFilesLimited", "false")

        if (str(logFileLocation).find("REPLACE_MANAGED_SERVER_NAME") != -1) or (str(logFileLocation).find("REPLACE_DOMAIN_NAME") != -1):
            log.debug('Replacing managed server name in the log file location...\n')
            logFileLocation = str(logFileLocation).replace('REPLACE_MANAGED_SERVER_NAME', serverName)
            logFileLocation = str(logFileLocation).replace('REPLACE_DOMAIN_NAME', domainName)

        log.debug('Setting log file location for managed server : ' + serverName + ' to : ' + logFileLocation + '/' + serverName + '/access.log...\n')
        set("FileName", logFileLocation + '/access.log')
    
        saveAndActivateChanges()

        log.debug('Successfully set the logging file properties for the web server on : ' + serverName + ' ...\n')
    except Exception, e:
        log.error('Error in setting the logging file properties for the web server on : ' + serverName + ' ...\n')
        dumpStack()
        discardChanges()

#Function for setting the server start arguments for a managed server
#def setServerStartArguments(serverName, javaHome, javaVendor, beaHome, rootDirectory, classpath, adminUserName, adminPassword, serverStartArguments): 
def setServerStartArguments(serverName, javaHome, javaVendor, beaHome, rootDirectory, classpath, adminUserName, adminPassword, serverStartArguments, hostName):
    try:    
        log.info('Setting the server start arguments for : ' + serverName + ' ...\n')

        startEditSession()
        cd('/Servers/' + serverName + '/ServerStart/' + serverName)
	hostName=hostName.upper()
        
        if javaHome != None:
            log.debug('Setting Java Home for : ' + serverName + ' ...\n')
            set("JavaHome", javaHome)
    
        if javaVendor != None:
            log.debug('Setting Java Vendor for : ' + serverName + ' ...\n')
            set("JavaVendor", javaVendor)
    
        if beaHome != None:
            log.debug('Setting BEA Home for : ' + serverName + ' ...\n')
            set("BeaHome", beaHome)
    
        if rootDirectory != None:
            log.debug('Setting root directory for : ' + serverName + ' ...\n')
            set("RootDirectory", rootDirectory)
    
        if classpath != None:
            log.debug('Setting class path for : ' + serverName + ' ...\n')
            set("ClassPath", classpath)
    
        if adminUserName != None:
            log.debug('Setting Weblogic administrator username for managed server : ' + serverName + '\n')
            set("Username", adminUserName)
    
        if adminPassword != None:
            log.debug('Setting Weblogic administrator password for managed server : ' + serverName + '\n')
            set("Password", adminPassword)
    
        if serverStartArguments != None:
            log.debug('Server start arguments for managed server : ' + serverName +  ' are specified as : ' + str(serverStartArguments) + '\n')
            if (str(serverStartArguments).find("REPLACE_MANAGED_SERVER_NAME") != -1):
                log.debug('Replacing managed server name/domain name in the server start arguments...\n')
                serverStartArguments = str(serverStartArguments).replace('REPLACE_MANAGED_SERVER_NAME', serverName)
                serverStartArguments = str(serverStartArguments).replace('REPLACE_DOMAIN_NAME', domainName)
		serverStartArguments = str(serverStartArguments).replace('REPLACE_HOSTNAME', hostName)
            log.debug('Setting server start arguments for managed server : ' + serverName +  ' to : ' + str(serverStartArguments) + '\n')
            set("Arguments", serverStartArguments)
    
        saveAndActivateChanges()

        log.debug('Successfully set the server start arguments for : ' + serverName + ' ...\n')
    except Exception, e:
        log.error('Error in setting the server start arguments for : ' + serverName + ' ...\n')
        dumpStack()
        discardChanges()

def setAttributesForClusterChannelForManagedServer(serverName, clusterChannelName, listenPort, listenAddress):
    try:    
        log.info('Setting attributes for cluster channel : ' + clusterChannelName + ' on server : ' + serverName + '\n')
    
        cd('/Servers/' + serverName + '/NetworkAccessPoints/' + clusterChannelName)
    
        startEditSession()
    
        log.debug('Setting TwoWaySSLEnabled to false for channel : ' + clusterChannelName + ' on server : ' + serverName + '\n')
        set("TwoWaySSLEnabled", "false")
    
        log.debug('Setting HttpEnabledForThisProtocol to true for channel : ' + clusterChannelName + ' on server : ' + serverName + '\n')
        set("HttpEnabledForThisProtocol", "true")
    
        log.debug('Setting OutboundEnabled to true for channel : ' + clusterChannelName + ' on server : ' + serverName + '\n')
        set("OutboundEnabled", "true")
    
        log.debug('Setting Enabled to true for channel : ' + clusterChannelName + ' on server : ' + serverName + '\n')
        set("Enabled", "true")
    
        portMask = int("21" + listenPort[1:])
        set("ListenPort", listenPort)
        log.debug('Setting ListenPort to : ' + str(portMask) + ' for channel : ' + clusterChannelName + ' on server : ' + serverName + '\n')
        set("ListenPort", portMask)
    
        log.debug('Setting ListenAddress to : ' + listenAddress + ' for channel : ' + clusterChannelName + ' on server : ' + serverName + '\n')
        set("ListenAddress", listenAddress)
    
        log.debug('Setting Protocol to  : cluster-broadcast for channel : ' + clusterChannelName + ' on server : ' + serverName + '\n')
        set("Protocol", "cluster-broadcast")
    
        log.debug('Setting TunnelingEnabled to false for channel : ' + clusterChannelName + ' on server : ' + serverName + '\n')
        set("TunnelingEnabled", "false")
    
        log.debug('Setting ChannelIdentityCustomized to false for channel : ' + clusterChannelName + ' on server : ' + serverName + '\n')
        set("ChannelIdentityCustomized", "false")
    
        log.debug('Setting PublicPort to ' + str(portMask) + ' for channel : ' + clusterChannelName + ' on server : ' + serverName + '\n')
        set("PublicPort", portMask)
    
        log.debug('Setting PublicAddress to : ' + listenAddress + ' for channel : ' + clusterChannelName + ' on server : ' + serverName + '\n')
        set("PublicAddress", listenAddress)
    
        log.debug('Setting ClientCertificateEnforced to false for channel : ' + clusterChannelName + ' on server : ' + serverName + '\n')
        set("ClientCertificateEnforced", "false")

        #saveAndActivateChanges()

        log.debug('\nSuccessfully set the attributes for the cluster channel : ' + clusterChannelName + ' ...' + ' on server : ' + serverName + '\n')
    except Exception, e:
        log.error('Error in setting the attributes for the cluster channel : ' + clusterChannelName + ' ...' + ' on server : ' + serverName + '\n')
        dumpStack()
        discardChanges()

#Function to set the attributes for JTA Migratable target
def setAttributesForJTAMigratableTarget(serverName, clusterName):
    try:    
        log.info('Setting attributes for migratable target for server : ' + serverName + '\n')

        cd('/Servers/' + serverName + '/JTAMigratableTarget/' + serverName)
        
        startEditSession()
        bean = getMBean('/Clusters/' + clusterName)
        cmo.setCluster(bean)

        bean = getMBean('/Servers/' + serverName)
        cmo.setUserPreferredServer(bean)

        saveAndActivateChanges()

        log.debug('Successfully set attributes for migratable target for server : ' + serverName + '\n')
    except Exception, e:
        log.error('Error in setting attributes for migratable target for server : ' + serverName + '\n')
        dumpStack()
        discardChanges()

#Function to set the attributes for migrating the managed server
def setAttributesForDefaultMigratableTarget(serverName, clusterName):
    try:    
        log.info('Setting attributes for system generated default migratable target for server : ' + serverName + '\n')

        cd('/MigratableTargets/' + serverName + ' (migratable)')
        
        startEditSession()
        
        log.debug('Setting notes for server : ' + serverName + '\n')
        set("Notes", "This is a system generated default migratable target for a server. Do not delete manually.")

        bean = getMBean('/Clusters/' + clusterName)
        cmo.setCluster(bean)

        bean = getMBean('/Servers/' + serverName)
        cmo.setUserPreferredServer(bean)

        saveAndActivateChanges()

        log.debug('Successfully set attributes for system generated default migratable target for server : ' + serverName + '\n')
    except Exception, e:
        log.error('Error in setting attributes for system generated default migratable target for server : ' + serverName + '\n')
        dumpStack()
        discardChanges()

#Function for creating a JMS Server
def createJMSServer(jmsServerName, targetName):
    cd('/')
    try:
        log.debug('Checking if a JMS server : ' + jmsServerName + ' exists in the domain ...\n')
        
        theBean = cmo.lookupJMSServer(jmsServerName)
        if theBean == None:
            log.info('A JMS server with name ' + jmsServerName + ' does not exist in the domain. Creating a new JMS server ...\n')
            
            startEditSession()
            cmo.createJMSServer(jmsServerName)
            saveAndActivateChanges()

            log.debug('Successfully created a JMS server with name ' + jmsServerName + ' in the domain...\n')

            setPropertiesForJMSServer(jmsServerName, targetName)

            log.debug('Successfully set the properties for JMS server with name ' + jmsServerName + '\n')
        else:
            log.info('A JMS server with name ' + jmsServerName + ' already exists in the domain. Bypassing creating it again ...\n')

            setPropertiesForJMSServer(jmsServerName, targetName)

            log.debug('Successfully set the properties for JMS server with name ' + jmsServerName + '\n')
    
    except java.lang.UnsupportedOperationException, usoe:
        dumpStack()
        pass
    except weblogic.descriptor.BeanAlreadyExistsException, bae:
        log.info('A JMS server with name ' + machineName + ' already exists in the domain. Bypassing creating it again ...\n')
        pass
    except java.lang.reflect.UndeclaredThrowableException, udt:
        dumpStack()
        pass
    except Exception, e:
        log.error('Error in creating a JMS server with name ' + jmsServerName + ' in the domain...\n')
        dumpStack()
        discardChanges()

#Function for setting properties for a JMS Server
def setPropertiesForJMSServer(jmsServerName, targetName):
    try:    
        log.info('Setting the properties for the JMS server : ' + jmsServerName + ' ...\n')

        startEditSession()
        cd('/JMSServers/' + jmsServerName)

        log.debug('Setting the property InsertionPausedAtStartup to false for the JMS server : ' + jmsServerName + ' ...\n')
        set("InsertionPausedAtStartup", "false")
    
        log.debug('Setting the property StoreEnabled to false for the JMS server : ' + jmsServerName + ' ...\n')
        set("StoreEnabled", "false")
    
        log.debug('Setting the property AllowsPersistentDowngrade to false for the JMS server : ' + jmsServerName + ' ...\n')
        set("AllowsPersistentDowngrade", "true")
    
        log.debug('Setting the property ProductionPausedAtStartup to false for the JMS server : ' + jmsServerName + ' ...\n')
        set("ProductionPausedAtStartup", "false")
    
        log.debug('Setting the property ConsumptionPausedAtStartup to false for the JMS server : ' + jmsServerName + ' ...\n')
        set("ConsumptionPausedAtStartup", "false")

        if (not domainServersDictionary.has_key(str(targetName))) and (not domainClustersDictionary.has_key(str(targetName))):
            log.debug(targetName + ' is not a valid managed server/cluster. So JMS server : ' + jmsServerName + ' cannot be assigned to it...\n')
            log.debug('Aborting...\n')
            discardChanges()

        log.debug('Getting a reference to : ' + targetName + ' to set it as a target for JMS Server : ' + jmsServerName + ' ...\n')
        refBean0 = getMBean('/Servers/' + targetName)
        theValue = jarray.array([refBean0], Class.forName("weblogic.management.configuration.TargetMBean"))

        log.debug('Targeting JMSServer : ' + jmsServerName + ' to : ' + targetName + '\n')
        cmo.setTargets(theValue)
    
        saveAndActivateChanges()

        log.debug('Successfully set the properties for the JMS server : ' + jmsServerName + ' ...\n')
    except Exception, e:
        log.error('Error in setting the properties for the JMS server : ' + jmsServerName + ' ...\n')
        dumpStack()
        discardChanges()

#Function for creating a JMS Module
def createJMSSystemResource(jmsSystemResourceName):
    try:
        log.debug('Checking if a JMS system resource : ' + jmsSystemResourceName + ' exists in the domain ...\n')
        cd('/')
        theBean = cmo.lookupJMSSystemResource(jmsSystemResourceName)
        if theBean == None:
            log.info('A JMS system resource with name ' + jmsSystemResourceName + ' does not exist in the domain. Creating a new JMS system resource ...\n')
        
            startEditSession()
            cmo.createJMSSystemResource(jmsSystemResourceName)
            saveAndActivateChanges()
        
            log.debug('Successfully created the JMS system resource with name ' + jmsSystemResourceName + ' in the domain...\n')
        else:
            log.info('A JMS System resource with name ' + jmsSystemResourceName + ' already exists in the domain. Bypassing creating it again ...\n')

    except java.lang.UnsupportedOperationException, usoe:
        dumpStack()
        pass
    except weblogic.descriptor.BeanAlreadyExistsException, bae:
        log.info('A JMS System resource with name ' + jmsSystemResourceName + ' already exists in the domain. Bypassing creating it again ...\n')
        pass
    except java.lang.reflect.UndeclaredThrowableException, udt:
        dumpStack()
        pass
    except Exception, e:
        log.error('Error in creating the JMS system resource with name ' + jmsSystemResourceName + ' in the domain...\n')
        dumpStack()
        discardChanges()

#Function for setting the target for a JMS Module
def setTargetForJMSSystemResource(moduleName, targetName):
    try:    
        if (not domainServersDictionary.has_key(str(targetName))) and (not domainClustersDictionary.has_key(str(targetName))):
            log.error(targetName + ' is not a valid managed server/cluster. So JMSSystemResource : ' + moduleName + ' cannot be assigned to it...\n')
            log.debug('Aborting...\n')
            discardChanges()
    
        log.debug('Getting a reference to : ' + targetName + ' so that it can be added as a target for JMS Module : ' + moduleName + '\n')
    
        if (domainServersDictionary.has_key(str(targetName))):
            targetType = 'Server'
        elif (domainClustersDictionary.has_key(str(targetName))):
            targetType = 'Cluster'

        if targetType == 'Server':
            refBean = getMBean('/Servers/' + targetName)
        if targetType == 'Cluster':
            refBean = getMBean('/Clusters/' + targetName)
    
        cd('/JMSSystemResources/' + moduleName)
        
        log.debug('Getting the current targets of the JMS Module : ' + moduleName + '\n')
        currentTargets = cmo.getTargets()
    
        log.debug('The current targets of the JMS Module : ' + moduleName + ' are : ' + str(currentTargets) + '\n')

        startEditSession()
        log.debug('Adding : ' + targetName + ' to the current targets of JMS modules : ' + moduleName)
        cmo.addTarget(refBean)
        saveAndActivateChanges()

        log.debug('Successfully added ' + targetName + ' as a target for JMSSystemResource : ' + moduleName + '\n')
    except Exception, e:
        log.error('Error in setting ' + targetName + ' as a target for JMSSystemResource : ' + moduleName + '\n')
        dumpStack()
        discardChanges()

#Function for creating a subdeployment
def createSubDeployment(subDeploymentName, moduleName):
    try:
        log.debug('Checking if a subdeployment : ' + subDeploymentName + ' exists in the domain ...\n')
    
        cd('/JMSSystemResources/' + moduleName)
        theBean = cmo.lookupSubDeployment(subDeploymentName)
        if theBean == None:
            log.info('A subdeployment with name ' + subDeploymentName + ' does not exist in the domain. Creating a new sub deployment ...\n')
    
            startEditSession()
            cmo.createSubDeployment(subDeploymentName)
            saveAndActivateChanges()
            
            log.debug('Successfully created a sub deployment with name ' + subDeploymentName + '...\n')
        else:
            log.info('A sub deployment with name ' + subDeploymentName + ' already exists in the domain. Bypassing creating it again ...\n')

    except java.lang.UnsupportedOperationException, usoe:
        dumpStack()
        pass
    except weblogic.descriptor.BeanAlreadyExistsException, bae:
        log.info('A sub deployment with name ' + subDeploymentName + ' already exists in the domain. Bypassing creating it again ...\n')
        pass
    except java.lang.reflect.UndeclaredThrowableException, udt:
        dumpStack()
        pass
    except Exception, e:
        log.error('Error in createing a sub deployment with name ' + subDeploymentName + '...\n')
        dumpStack()
        discardChanges()

#Function for setting the targets for a subdeployment
def setTargetsForSubdeployment(subdeploymentName, targetName, moduleName):
    try:    
        log.info('Getting a reference to : ' + targetName + ' so that it can be set as a target for sub deployment : ' + subdeploymentName + '\n')

        refBean = None

        if getMBean('/JMSServers/' + targetName) != None:
            log.debug('The target specified for the sub deployment : ' + subdeploymentName + ' is a JMS server\n')
            refBean = getMBean('/JMSServers/' + targetName)
        elif getMBean('/Servers/' + targetName) != None:
            log.debug('The target specified for the sub deployment : ' + subdeploymentName + ' is a server\n')
            refBean = getMBean('/Servers/' + targetName)
        elif getMBean('/Clusters/' + targetName) != None:
            log.debug('The target specified for the sub deployment : ' + subdeploymentName + ' is a cluster\n')
            refBean = getMBean('/Clusters/' + targetName)
        else:
            log.error('The target specified for the sub deployment : ' + subdeploymentName + ' is invalid\n')
            discardChanges()

        theValue = jarray.array([refBean], Class.forName("weblogic.management.configuration.TargetMBean"))

        cd('/JMSSystemResources/' + moduleName + '/SubDeployments/' + subdeploymentName)

        startEditSession()
        log.debug('Adding ' + targetName + ' as a target for subdeployment : ' + subdeploymentName + '\n')
        cmo.addTarget(refBean)
        saveAndActivateChanges()

        log.debug('Successfully set ' + targetName + ' as a target for subdeployment : ' + subdeploymentName + '\n')
    except Exception, e:
        log.error('Error in setting ' + targetName + ' as a target for subdeployment : ' + subdeploymentName + '\n')
        dumpStack()
        discardChanges()

#Function for creating a local topic
def createLocalTopic(topicName, moduleName):
    try:
        log.debug('Checking if a topic : ' + topicName + ' exists in the domain ...\n')
        
        cd('/JMSSystemResources/' + moduleName + '/JMSResource/' + moduleName)
        theBean = cmo.lookupTopic(topicName)
        if theBean == None:
            log.info('A topic with name ' + topicName + ' does not exist in the domain. Creating a new topic ...\n')
        
            startEditSession()
            cmo.createTopic(topicName)
            saveAndActivateChanges()
        
            log.debug('Successfully created a local topic with name ' + topicName + '...\n')
        else:
            log.info('A topic with name ' + topicName + ' already exists in the domain. Bypassing creating it again ...\n')

    except java.lang.UnsupportedOperationException, usoe:
        dumpStack()
        pass
    except weblogic.descriptor.BeanAlreadyExistsException, bae:
        log.info('A topic with name ' + topicName + ' already exists in the domain. Bypassing creating it again ...\n')
        pass
    except java.lang.reflect.UndeclaredThrowableException, udt:
        dumpStack()
        pass
    except Exception, e:
        log.error('Error in creating a local topic with name ' + topicName + '...\n')
        dumpStack()
        discardChanges()

#Function for setting properties for a local topic
def setPropertiesForTopic(topicName, moduleName, jndiName, subDeploymentName):
    try:    
        log.info('Setting properties for topic : ' + topicName + '\n')
    
        startEditSession()
        cd('/JMSSystemResources/' + moduleName + '/JMSResource/' + moduleName + '/Topics/' + topicName)
        
        if topicName != None:
            log.debug('Setting name for topic : ' + topicName + '\n')
            set("Name", topicName)
    
        if jndiName != None:
            log.debug('Setting JNDI name for topic : ' + topicName + ' to : ' + jndiName + '\n')
            set("JNDIName", jndiName)
    
        if subDeploymentName != None:
            log.debug('Setting subdeployment for topic : ' + topicName + ' to : ' + subDeploymentName + '\n')
            set("SubDeploymentName", subDeploymentName)
    
        saveAndActivateChanges()
    
        log.debug('Successfully set the properties for topic : ' + topicName + '\n')
    except Exception, e:
        log.error('Error in setting the properties for topic : ' + topicName + '\n')
        dumpStack()
        discardChanges()

#Function for creating a distributed topic
def createDistributedTopic(topicName, moduleName):
    try:
        log.debug('Checking if a uniform distributed topic : ' + topicName + ' exists in the domain ...\n')
        
        cd('/JMSSystemResources/' + moduleName + '/JMSResource/' + moduleName)
        theBean = cmo.lookupUniformDistributedTopic(topicName)
        if theBean == None:
            log.info('A uniform distributed topic with name ' + topicName + ' does not exist in the domain. Creating a new topic ...\n')
        
            startEditSession()
            cmo.createUniformDistributedTopic(topicName)
            saveAndActivateChanges()
        
            log.debug('Successfully created a uniform distributed topic with name ' + topicName + '...\n')
        else:
            log.info('A uniform distributed topic with name ' + topicName + ' already exists in the domain. Bypassing creating it again ...\n')

    except java.lang.UnsupportedOperationException, usoe:
        dumpStack()
        pass
    except weblogic.descriptor.BeanAlreadyExistsException, bae:
        log.info('A uniform distributed topic with name ' + topicName + ' already exists in the domain. Bypassing creating it again ...\n')
        pass
    except java.lang.reflect.UndeclaredThrowableException, udt:
        dumpStack()
        pass
    except Exception, e:
        log.error('Error in creating a uniform distributed topic with name ' + topicName + '...\n')
        dumpStack()
        discardChanges()

#Function for setting properties for a distributed topic
def setPropertiesForDistributedTopic(topicName, moduleName, jndiName, subDeploymentName, jmsTopicRedeliveryDelay, jmsTopicRedeliveryLimit, jmsTopicLoadBalancingPolicy):
    try:    
        log.info('Setting properties for uniform distributed topic : ' + topicName + '\n')
    
        startEditSession()
        cd('/JMSSystemResources/' + moduleName + '/JMSResource/' + moduleName + '/UniformDistributedTopics/' + topicName)
        
        if topicName != None:
            log.debug('Setting name for topic : ' + topicName + '\n')
            set("Name", topicName)
    
        if jndiName != None:
            log.debug('Setting JNDI name for topic : ' + topicName + ' to : ' + jndiName + '\n')
            set("JNDIName", jndiName)
    
        if subDeploymentName != None:
            log.debug('Setting subdeployment for topic : ' + topicName + ' to : ' + subDeploymentName + '\n')
            set("SubDeploymentName", subDeploymentName)
    
        if jmsTopicLoadBalancingPolicy != None:
            log.debug('Setting load balancing policy for topic : ' + topicName + ' to : ' + jmsTopicLoadBalancingPolicy + '\n')
            set("LoadBalancingPolicy", jmsTopicLoadBalancingPolicy)
   
        if jmsTopicRedeliveryLimit != None:
            cd('/JMSSystemResources/' + moduleName + '/JMSResource/' + moduleName + '/UniformDistributedTopics/' + topicName + '/DeliveryFailureParams/' + topicName)
            log.debug('Setting redelivery limit for topic : ' + topicName + ' to : ' + jmsTopicRedeliveryLimit + '\n')
            set("RedeliveryLimit", jmsTopicRedeliveryLimit)

        if jmsTopicRedeliveryDelay != None:
            cd('/JMSSystemResources/' + moduleName + '/JMSResource/' + moduleName + '/UniformDistributedTopics/' + topicName + '/DeliveryParamsOverrides/' + topicName)
            log.debug('Setting redelivery delay for topic : ' + topicName + ' to : ' + jmsTopicRedeliveryDelay + '\n')
            set("RedeliveryDelay", jmsTopicRedeliveryDelay)

        saveAndActivateChanges()
    
        log.debug('Successfully set the properties for uniform distributed topic : ' + topicName + '\n')
    except Exception, e:
        log.error('Error in setting the properties for uniform distributed topic : ' + topicName + '\n')
        dumpStack()
        discardChanges()

#Function for creating a uniform distributed queue
def createDistributedQueue(queueName, moduleName):
    try:
        log.debug('Checking if a uniform distributed queue : ' + queueName + ' exists in the domain ...\n')
        
        cd('/JMSSystemResources/' + moduleName + '/JMSResource/' + moduleName)
        theBean = cmo.lookupUniformDistributedQueue(queueName)
        if theBean == None:
            log.info('A uniform distributed queue with name ' + queueName + ' does not exist in the domain. Creating a new queue ...\n')
        
            startEditSession()
            cmo.createUniformDistributedQueue(queueName)
            saveAndActivateChanges()
        
            log.debug('Successfully created a uniform distributed queue with name ' + queueName + '...\n')
        else:
            log.info('A uniform distributed queue with name ' + queueName + ' already exists in the domain. Bypassing creating it again ...\n')

    except java.lang.UnsupportedOperationException, usoe:
        dumpStack()
        pass
    except weblogic.descriptor.BeanAlreadyExistsException, bae:
        log.info('A uniform distributed queue with name ' + queueName + ' already exists in the domain. Bypassing creating it again ...\n')
        pass
    except java.lang.reflect.UndeclaredThrowableException, udt:
        dumpStack()
        pass
    except Exception, e:
        log.error('Error in creating a uniform distributed queue with name ' + queueName + '...\n')
        dumpStack()
        discardChanges()

#Function for setting properties for a unifrom distributed queue topic
def setPropertiesForDistributedQueue(queueName, jndiName, subDeploymentName, moduleName, jmsQueueRedeliveryDelay, jmsQueueRedeliveryLimit, jmsQueueLoadBalancingPolicy, jmsQueueErrorDestination, jmsQueueMaximumMessageSize, jmsQueueForwardDelay, jmsQueueExpirationPolicy, jmsQueueTimeToLive):
    try:    
        log.info('Setting properties for queue : ' + queueName + '\n')
   
        startEditSession()
   
        cd('/JMSSystemResources/' + str(moduleName) + '/JMSResource/' + str(moduleName) + '/UniformDistributedQueues/' + str(queueName))
        if queueName != None:
            log.debug('Setting name for queue : ' + queueName + '\n')
            set("Name", str(queueName))
    
        if jndiName != None:
            log.debug('Setting JNDI name for queue : ' + queueName + ' to : ' + jndiName + '\n')
            set("JNDIName", jndiName)
    
        if subDeploymentName != None:
            log.debug('Setting subdeployment for queue : ' + queueName + ' to : ' + subDeploymentName + '\n')
            set("SubDeploymentName", subDeploymentName)
    
        if jmsQueueLoadBalancingPolicy != None:
            log.debug('Setting load balancing policy for queue : ' + queueName + ' to : ' + jmsQueueLoadBalancingPolicy + '\n')
            set("LoadBalancingPolicy", jmsQueueLoadBalancingPolicy)
        
        if jmsQueueForwardDelay != None:
            log.debug('Setting the Forward Delay for the queue : ' + queueName + ' to : ' + jmsQueueForwardDelay + '\n')
            set("ForwardDelay", jmsQueueForwardDelay)

        if jmsQueueMaximumMessageSize != None:
            log.debug('Setting the maximum message size for the queue : ' + queueName + ' to : ' + jmsQueueMaximumMessageSize + '\n')
            set("MaximumMessageSize", jmsQueueMaximumMessageSize)
   
        cd('/JMSSystemResources/' + moduleName + '/JMSResource/' + moduleName + '/UniformDistributedQueues/' + queueName + '/DeliveryParamsOverrides/' + queueName)
   
        if jmsQueueTimeToLive != None:
            log.debug('Setting the time to live for the queue : ' + queueName + ' to : ' + jmsQueueTimeToLive + '\n')
            set("TimeToLive", jmsQueueTimeToLive)

        if jmsQueueRedeliveryDelay != None:
            log.debug('Setting the redelivery delay for the queue : ' + queueName + ' to : ' + jmsQueueRedeliveryDelay + '\n')
            set("RedeliveryDelay", jmsQueueRedeliveryDelay)

        cd('/JMSSystemResources/' + moduleName + '/JMSResource/' + moduleName + '/UniformDistributedQueues/' + queueName + '/DeliveryFailureParams/' + queueName)
   
        if jmsQueueRedeliveryLimit != None:
            log.debug('Setting the redelivery limit for the queue : ' + queueName + ' to : ' + jmsQueueRedeliveryLimit + '\n')
            set("RedeliveryLimit", jmsQueueRedeliveryLimit)

        if jmsQueueExpirationPolicy != None:
            log.debug('Setting the expiration policy for the queue : ' + queueName + ' to : ' + jmsQueueExpirationPolicy + '\n')
            set("ExpirationPolicy", jmsQueueExpirationPolicy)

        if jmsQueueErrorDestination != None:
            log.debug('Setting the error destination for the queue : ' + queueName + ' to : ' + jmsQueueErrorDestination + '\n')
            cmo.setErrorDestination(getMBean('/JMSSystemResources/' + moduleName + '/JMSResource/' + moduleName + '/UniformDistributedQueues/' + jmsQueueErrorDestination))

        saveAndActivateChanges()
    
        log.debug('Successfully set the properties for queue : ' + queueName + '\n')
    except Exception, e:
        log.error('Error in setting the properties for queue : ' + queueName + '\n')
        dumpStack()
        discardChanges()

#Function for creating a connection factory
def createConnectionFactory(connectionFactoryName, moduleName):
    try:
        log.debug('Checking if a connection factory :  ' + connectionFactoryName + ' exists in the domain ...\n')
    
        cd('/JMSSystemResources/' + moduleName + '/JMSResource/' + moduleName)
        theBean = cmo.lookupConnectionFactory(connectionFactoryName)
        if theBean == None:
            log.info('A connection factory with name ' + connectionFactoryName + ' does not exist in the domain. Creating a new connection factory ...\n')
        
            startEditSession()
            cmo.createConnectionFactory(connectionFactoryName)
            saveAndActivateChanges()
            
            log.debug('Successfully created a connection factory with name ' + connectionFactoryName + '...\n')
        else:
            log.info('A connection factory with name ' + connectionFactoryName + ' already exists in the domain. Bypassing creating it again ...\n')
    except java.lang.UnsupportedOperationException, usoe:
        dumpStack()
        pass
    except weblogic.descriptor.BeanAlreadyExistsException, bae:
        log.info('A connection factory with name ' + connectionFactoryName + ' already exists in the domain. Bypassing creating it again ...\n')
        pass
    except java.lang.reflect.UndeclaredThrowableException, udt:
        dumpStack()
        pass
    except Exception, e:
        log.error('Error in createing a connection factory with name ' + connectionFactoryName + '...\n')
        dumpStack()
        discardChanges()

#Function for setting properties for a connection factory
def setPropertiesForConnectionFactory(moduleName, connectionFactoryName, jndiName, subDeploymentName, defaultDeliveryMode, attachJMXUserID, jmsConnectionFactoryXAConnectionFactoryEnabled):
    try:    
        log.info('Setting properties for connection factory : ' + connectionFactoryName + '\n')
    
        startEditSession()
        cd('/JMSSystemResources/' + moduleName + '/JMSResource/' + moduleName + '/ConnectionFactories/' + connectionFactoryName)
        
        if connectionFactoryName != None:
            log.debug('Setting the name for the connection factory : ' + connectionFactoryName + ' to : ' + connectionFactoryName + '\n')
            set("Name", connectionFactoryName)
    
        if jndiName != None:
            log.debug('Setting the JNDI name for the connection factory : ' + connectionFactoryName + ' to : ' + jndiName + '\n')
            set("JNDIName", jndiName)

        if subDeploymentName != None:
            log.debug('Setting the subdeplyment for the connection factory : ' + connectionFactoryName + ' to : ' + subDeploymentName + '\n')
            set("SubDeploymentName", subDeploymentName)

        if attachJMXUserID != None:
            log.debug('Setting the parameter AttachJMSXUserId for the connection factory : ' + connectionFactoryName + ' to : ' + attachJMXUserID + '\n')
            cd('/JMSSystemResources/' + moduleName + '/JMSResource/' + moduleName + '/ConnectionFactories/' + connectionFactoryName + '/SecurityParams/' + connectionFactoryName)
            set("AttachJMSXUserId", attachJMXUserID)

        if jmsConnectionFactoryXAConnectionFactoryEnabled != None:
            log.debug('Setting the parameter XAConnectionFactoryEnabled for the connection factory : ' + connectionFactoryName + ' to : ' + jmsConnectionFactoryXAConnectionFactoryEnabled + '\n')
            cd('/JMSSystemResources/' + moduleName + '/JMSResource/' + moduleName + '/ConnectionFactories/' + connectionFactoryName + '/TransactionParams/' + connectionFactoryName)
            set("XAConnectionFactoryEnabled", jmsConnectionFactoryXAConnectionFactoryEnabled)

        if defaultDeliveryMode != None:
            log.debug('Setting the parameter DefaultDeliveryMode for the connection factory : ' + connectionFactoryName + ' to : ' + defaultDeliveryMode + '\n')
            cd('/JMSSystemResources/' + moduleName + '/JMSResource/' + moduleName + '/ConnectionFactories/' + connectionFactoryName + '/DefaultDeliveryParams/' + connectionFactoryName)
            set("DefaultDeliveryMode", defaultDeliveryMode)

        saveAndActivateChanges()

        log.debug('Successfully set the properties for connection factory : ' + connectionFactoryName + '\n')
    except Exception, e:
        log.error('Error in setting the properties for connection factory : ' + connectionFactoryName + '\n')
        dumpStack()
        discardChanges()

#Function for creating a property and setting the value for the property
def createProperty(path, propertyName, propertyValue):
    try:
        log.info('Creating property by name : ' + propertyName + ' under ' + path + ' ...\n')
        
        cd(path)
        theBean = cmo.lookupProperty(propertyName)
        if theBean == None:
            cmo.createProperty(propertyName)
            cd(path + '/Properties/' + propertyName)            
            set("Name", propertyName)
            set("Value", propertyValue)
            log.debug('Successfully created a property with name : ' + propertyName + ' and assigned the value : ' + propertyValue + '\n')
        else:
            log.debug('A property with name ' + propertyName + ' already exists under path : ' + path + ' Bypassing creating it again ...\n')
            log.debug('Setting the value for the property...')
            cd(path + '/Properties/' + propertyName)            
            set("Name", propertyName)
            set("Value", propertyValue)
            log.debug('Successfully set the value of the property with name : ' + propertyName + ' to : ' + propertyValue + '\n')
    except java.lang.UnsupportedOperationException, usoe:
        dumpStack()
        pass
    except weblogic.descriptor.BeanAlreadyExistsException, bae:
        log.info('A property with name ' + propertyName + ' already exists under path : ' + path + ' Bypassing creating it again ...\n')
        log.debug('Setting the value for the property...')
        cd(path + '/Properties/' + propertyName)            
        set("Name", propertyName)
        set("Value", propertyValue)
        log.debug('Successfully set the value of the property with name : ' + propertyName + ' to : ' + propertyValue + '\n')
    except java.lang.reflect.UndeclaredThrowableException, udt:
        dumpStack()
        pass
    except TypeError:
        propertyRef = cmo.createProperty()
        propertyRef.setName(propertyName)
        propertyRef.setValue(propertyValue)
    except Exception, e:
        log.error('Error in creating a property with name ' + propertyName + ' already exists under path : ' + path + '\n')
        dumpStack()
        discardChanges()

#Function for creating the data source if it is not already created
def createJDBCSystemResource(dataSourceName):
    try:
        log.debug('Checking if a JDBC system resource :  ' + dataSourceName + ' exists in the domain ...\n')
        cd('/')

        theBean = cmo.lookupJDBCSystemResource(dataSourceName)
        if theBean == None:
            log.info('A JDBC data source with name ' + dataSourceName + ' does not exist in the domain. Creating a new JDBC data source ...')

            cmo.createJDBCSystemResource(dataSourceName)
            log.debug('Successfully created a JDBC data source with name ' + dataSourceName + ' ...')
            return 1
        else:
            log.info('A JDBC resource with name ' + dataSourceName + ' already exists in the domain. Bypassing creating it again ...')
            return 0
    except java.lang.UnsupportedOperationException, usoe:
        dumpStack()
        discardChanges()
    except weblogic.descriptor.BeanAlreadyExistsException, bae:
        log.info('A JDBC resource with name ' + dataSourceName + ' already exists in the domain. Bypassing creating it again ...')
        return 0
    except java.lang.reflect.UndeclaredThrowableException, udt:
        dumpStack()
        discardChanges()
    except Exception, e:
        log.error('Error in creating a JDBC data source with name ' + dataSourceName + ' ...')
        dumpStack()
        discardChanges()

#Function for targetting the data source to a server or cluster
def setTargetsForDataSource(dataSourceName, targetName):
    try:   
        targetType = None   

        if (domainServersDictionary.has_key(targetName)):
            targetType = 'Server'   
        elif (domainClustersDictionary.has_key(targetName)):
            targetType = 'Cluster'   
        else:
            log.error(str(targetName) + ' is not a valid managed server/cluster. So the data source : ' + dataSourceName + ' cannot be assigned to it...\n')
            log.debug('Aborting...\n')
            discardChanges()

        log.info('Getting a reference to : ' + str(targetName) + ' so that it can be set as a target for data source : ' + dataSourceName + '\n')
    
        if targetType == 'Server':   
            refBean = getMBean('/Servers/' + str(targetName))
        if targetType == 'Cluster':   
            refBean = getMBean('/Clusters/' + str(targetName))
   
        cd('/JDBCSystemResources/' + dataSourceName)
        log.debug('Setting ' + targetName + ' as a target for data source : ' + dataSourceName)
        cmo.addTarget(refBean)

        log.debug('Successfully set ' + targetName + ' as a target for data source : ' + dataSourceName)
    except Exception, e:
        log.error('Error in setting ' + targetName + ' as a target for data source : ' + dataSourceName)
        dumpStack()
        discardChanges()

#Function for setting parameters associated with the data source
def setPropertiesForJDBCDataSource(dataSourceName, dataSourceJNDIName, dataSourceURI, dataSourceUser, dataSourcePassword, dataSourceInitialCapacity, dataSourceMaximumCapacity, dataSourceConnectionCreationRetryFrequency, dataSourceCapacityIncrement, dataSourceRowPrefetchEnabled, dataSourceRowPrefetchSize, dataSourceStreamChunkSize):
    try:    
        log.info('Setting the properties for JDBC data source : ' + dataSourceName)
    
        cd('/JDBCSystemResources/' + dataSourceName + '/JDBCResource/' + dataSourceName)

        log.debug('Setting name for JDBC data source : ' + dataSourceName)
        set("Name", dataSourceName)

        cd('/JDBCSystemResources/' + dataSourceName + '/JDBCResource/' + dataSourceName + '/JDBCConnectionPoolParams/' + dataSourceName)

        log.debug('Setting up the test table name for JDBC data source : ' + dataSourceName)
        set("TestTableName", "SQL SELECT 1 FROM DUAL")

        log.debug('Setting up the JDBC data source : ' + dataSourceName + ' to test connections on reserve\n')
        set("TestConnectionsOnReserve", "true")

        if dataSourceInitialCapacity != None:
            log.debug('Setting initial capacity for JDBC data source : ' + dataSourceName)
            set("InitialCapacity", dataSourceInitialCapacity)
        else:
            log.debug('Bypassing setting initial capacity for JDBC data source : ' + dataSourceName + '\n')

        cd('/JDBCSystemResources/' + dataSourceName + '/JDBCResource/' + dataSourceName + '/JDBCConnectionPoolParams/' + dataSourceName)

        if dataSourceMaximumCapacity != None:
            log.debug('Setting maximum capacity for JDBC data source : ' + dataSourceName + ' to : ' + dataSourceMaximumCapacity + '\n')
            set("MaxCapacity", dataSourceMaximumCapacity)
        else:
            log.debug('Bypassing setting the maximum capacity for JDBC data source : ' + dataSourceName + '\n')

        if dataSourceConnectionCreationRetryFrequency != None:
            log.debug('Setting connection creation retry frequency for JDBC data source : ' + dataSourceName + ' to : ' + dataSourceConnectionCreationRetryFrequency + '\n')
            set("ConnectionCreationRetryFrequencySeconds", dataSourceConnectionCreationRetryFrequency)
        else:
            log.debug('Bypassing setting the connection creation retry frequency for JDBC data source : ' + dataSourceName + '\n')

        cd('/JDBCSystemResources/' + dataSourceName + '/JDBCResource/' + dataSourceName + '/JDBCConnectionPoolParams/' + dataSourceName)

        if dataSourceCapacityIncrement != None:
            log.debug('Setting capacity increment for JDBC data source : ' + dataSourceName  + ' to : ' + dataSourceMaximumCapacity + '\n')
            set("CapacityIncrement", dataSourceCapacityIncrement)
        else:
            log.debug('Bypassing setting the capacity increment for JDBC data source : ' + dataSourceName + '\n')

        cd('/JDBCSystemResources/' + dataSourceName + '/JDBCResource/' + dataSourceName + '/JDBCDataSourceParams/' + dataSourceName)

        log.debug('Setting the Global Transaction Protocol to OnePhaseCommit for JDBC data source : ' + dataSourceName + '\n')
        set("GlobalTransactionsProtocol", "OnePhaseCommit")

        if dataSourceJNDIName != None:
            log.debug('Setting the JNDI name to : ' +  dataSourceJNDIName + ' for data source : ' + dataSourceName + '\n')
            set("JNDINames", jarray.array([ '' + dataSourceJNDIName ], String))
        else:
            log.debug('The JNDI name for the data source cannot be empty...\n')
            log.debug('Aborting...\n')
            discardChanges()

        if dataSourceRowPrefetchEnabled != None:
            log.debug('Setting row prefecth flag to ' + dataSourceRowPrefetchEnabled + ' for data source : ' + dataSourceName + '\n')
            set("RowPrefetch", dataSourceRowPrefetchEnabled)
        else:
            log.debug('Bypassing setting the row prefetch enabled flag for JDBC data source : ' + dataSourceName + '\n')

        if dataSourceRowPrefetchSize != None:
            log.debug('Setting row prefecth size to ' + dataSourceRowPrefetchSize + ' for data source : ' + dataSourceName + '\n')
            set("RowPrefetchSize", dataSourceRowPrefetchSize)
        else:
            log.debug('Bypassing setting the row prefetch size for JDBC data source : ' + dataSourceName + '\n')
    
        if dataSourceStreamChunkSize != None:
            log.debug('Setting stream chunk size for data source : ' + dataSourceName  + ' to : ' + dataSourceStreamChunkSize + '\n')
            set("StreamChunkSize", dataSourceStreamChunkSize)
        else:
            log.debug('Bypassing setting the stream chunk size for JDBC data source : ' + dataSourceName + '\n')

        cd('/JDBCSystemResources/' + dataSourceName + '/JDBCResource/' + dataSourceName + '/JDBCDriverParams/' + dataSourceName)
        
        if dataSourceURI != None:
            log.debug('Setting URI for data source : ' + dataSourceName + ' to : ' + dataSourceURI + '\n')
            set("Url", dataSourceURI)
        
        log.debug('Setting driver for data source : ' + dataSourceName + ' to : oracle.jdbc.OracleDriver\n')
        set("DriverName", "oracle.jdbc.OracleDriver")

        if dataSourcePassword != None:
            log.debug('Setting password for data source : ' + dataSourceName + '\n')
            set("Password", dataSourcePassword)
        else:
            log.debug('Bypassing setting the password for JDBC data source : ' + dataSourceName + '\n')
        
        #createProperty('/JDBCSystemResources/' + dataSourceName + '/JDBCResource/' + dataSourceName + '/JDBCDriverParams/' + dataSourceName + '/Properties/' + dataSourceName)
        
        if dataSourceUser != None:
            createProperty('/JDBCSystemResources/' + dataSourceName + '/JDBCResource/' + dataSourceName + '/JDBCDriverParams/' + dataSourceName + '/Properties/' + dataSourceName, "user", dataSourceUser)
    
        log.debug('Successfully set the properties for JDBC data source : ' + dataSourceName + '\n')
    except Exception, e:
        log.error('Error in setting the properties for JDBC data source : ' + dataSourceName + '\n')
        dumpStack()
        discardChanges()

def readConfigurationFileAndCreateJMSServers(parentNode, managedServerName, hostName, managedServerIndex):
    jmsServersNodeCount = parentNode.getElementsByTagName("JMSServers").length

    if jmsServersNodeCount == 0:
        log.debug('There is no JMSServerName tag under the parent Node tag. Bypassing creating any JMS servers...\n')
        return

    #Get the name of the Weblogic Admin Server for the domain
    cd('/')
    adminServerName=cmo.getAdminServerName()

    #Initialize a regular expression for getting the last number in a string
    continuousNumberSequenceAtEndOfStringRegex = re.compile('(\d+)$')

    numberSuffix = ''

    jmsServerNodeList = parentNode.getElementsByTagName("JMSServers")

    for i in range(jmsServerNodeList.length):
        individualJMSServerNode = jmsServerNodeList.item(i);

        jmsServerNameNodeCount = individualJMSServerNode.getElementsByTagName("Name").length

        if jmsServerNameNodeCount == 0:
            log.debug('\nThe Name node is missing in the from the parent JMSServers node. Bypassing creating any JMS servers\n')
            discardChanges()
        else:
            if individualJMSServerNode.getElementsByTagName("Name").item(0).childNodes.item(0) != None:    
                jmsServerName = individualJMSServerNode.getElementsByTagName("Name").item(0).childNodes.item(0).data
            else:
                log.debug('Bypassing creating JMS servers since the Name tag is empty...\n')
                discardChanges()
        
        if (str(jmsServerName).find("REPLACE_MACHINE_SUFFIX") != -1) or (str(jmsServerName).find("REPLACE_MANAGED_SERVER_INDEX") != -1 ):
        
            log.debug('\nThe JMS server name is of the pattern : ' + jmsServerName + 'The pattern needs replacment to get a final JMS server name\n')
        
            log.debug('Replacing patterns in the JMS server name : ' + jmsServerName + '\n')

            jmsServerName = str(jmsServerName).replace('REPLACE_MANAGED_SERVER_INDEX', str(managedServerIndex))
           
            hostSuffixTemp = continuousNumberSequenceAtEndOfStringRegex.search(str(hostName))

            if hostSuffixTemp != None:
               hostSuffix = hostSuffixTemp.group(1)
               jmsServerName = str(jmsServerName).replace('REPLACE_MACHINE_SUFFIX', hostSuffix)
            else:
                if (str(hostName)[-3:])[0].isdigit():
                    jmsServerName = str(jmsServerName).replace('REPLACE_MACHINE_SUFFIX', str(hostName)[-3:])
                else:
                    jmsServerName = str(jmsServerName).replace('REPLACE_MACHINE_SUFFIX', str(hostName)[-2:])
                            
        log.debug('The JMS server : ' + jmsServerName + ' will be targetted to : ' + managedServerName + '\n')
        
        #Create JMS servers and target them to respective JVM's
        log.info('Creating JMS server : ' + str(jmsServerName) + ' on managed server ' + managedServerName + '\n')
        createJMSServer(str(jmsServerName), managedServerName)

def readConfigurationFileAndCreateJMSTopics(individualJMSModuleNode, managedServerName, hostName, managedServerIndex, jmsModuleName):
    #Initialize a regular expression for getting the last number in a string
    continuousNumberSequenceAtEndOfStringRegex = re.compile('(\d+)$')
    
    jmsTopicNodeCount = individualJMSModuleNode.getElementsByTagName("Topic").length

    if jmsTopicNodeCount == 0:
        log.debug('There is no Topic tag under the parent JMSModules for JMS module : ' + str(jmsModuleName) + ' . Bypassing creating any JMS topics...\n')
        return

    jmsTopicNodeList = individualJMSModuleNode.getElementsByTagName("Topic")

    for i in range(jmsTopicNodeList.length):
        individualJMSTopicNode = jmsTopicNodeList.item(i);

        jmsTopicNameNodeCount = individualJMSTopicNode.getElementsByTagName("Name").length
    
        if jmsTopicNameNodeCount == 0:
            log.debug('There is no Name tag under the parent Topic tag. Bypassing creating any JMS topics...\n')
            return
        else:
            #Get the name for JMS subdeployment     
            if individualJMSTopicNode.getElementsByTagName("Name").item(0).childNodes.item(0) != None:    
                jmsTopicName = individualJMSTopicNode.getElementsByTagName("Name").item(0).childNodes.item(0).data
            else:
                log.debug('The Name tag under the parent Topic tag is empty. Bypassing creating any JMS topics...\n')
                return

        log.debug('The JMS topic name is of the pattern : ' + jmsTopicName + '\n')
   
        if (str(jmsTopicName).find("REPLACE_MACHINE_SUFFIX") != -1) or (str(jmsTopicName).find("REPLACE_MANAGED_SERVER_INDEX") != -1 ):
            log.debug('Replacing patterns in the JMS topic name : ' + jmsTopicName + '\n')
                   
            jmsTopicName = str(jmsTopicName).replace('REPLACE_MANAGED_SERVER_INDEX', str(managedServerIndex))
           
            hostSuffixTemp = continuousNumberSequenceAtEndOfStringRegex.search(str(hostName))

            if hostSuffixTemp != None:
                hostSuffix = hostSuffixTemp.group(1)
                jmsTopicName = str(jmsTopicName).replace('REPLACE_MACHINE_SUFFIX', hostSuffix)
            else:
                if (str(hostName)[-3:])[0].isdigit():
                    jmsTopicName = str(jmsTopicName).replace('REPLACE_MACHINE_SUFFIX', str(hostName)[-3:])
                else:
                    jmsTopicName = str(jmsTopicName).replace('REPLACE_MACHINE_SUFFIX', str(hostName)[-2:])

        jmsTopicJNDINameNodeCount = individualJMSTopicNode.getElementsByTagName("JNDIName").length
    
        if jmsTopicJNDINameNodeCount == 0:
            log.debug('There is no JNDIName tag under the parent Topic tag. Setting it to empty...\n')
            jmsTopicJNDIName = None
        else: 
            #Get the name for JMS subdeployment     
            if individualJMSTopicNode.getElementsByTagName("JNDIName").item(0).childNodes.item(0) != None:    
                jmsTopicJNDIName = individualJMSTopicNode.getElementsByTagName("JNDIName").item(0).childNodes.item(0).data
            else:
                log.debug('The JNDIName tag under the parent Topic tag is empty...\n')
                jmsTopicJNDIName = None

        jmsTopicSubDeploymentNameNodeCount = individualJMSTopicNode.getElementsByTagName("SubDeploymentName").length
    
        if jmsTopicSubDeploymentNameNodeCount == 0:
            log.debug('There is no sub deployment name tags under the parent Topic tag. Not targetting the JMS topic to any sub deployment...\n')
            jmsTopicSubDeploymentName = None
        else: 
            #Get the name for JMS subdeployment     
            if individualJMSTopicNode.getElementsByTagName("SubDeploymentName").item(0).childNodes.item(0) != None:    
                jmsTopicSubDeploymentName = individualJMSTopicNode.getElementsByTagName("SubDeploymentName").item(0).childNodes.item(0).data
            else:
                log.debug('The SubDeploymentName tag under the parent Topic tag is empty. Not targetting the JMS topic to any sub deployment...\n')
                jmsTopicSubDeploymentName = None

        if (str(jmsTopicSubDeploymentName).find("REPLACE_MACHINE_SUFFIX") != -1) or (str(jmsTopicSubDeploymentName).find("REPLACE_MANAGED_SERVER_INDEX") != -1 ):
            log.debug('Replacing patterns in the sub deployment name : ' + jmsTopicSubDeploymentName + '\n')
            
            jmsTopicSubDeploymentName = str(jmsTopicSubDeploymentName).replace('REPLACE_MANAGED_SERVER_INDEX', str(managedServerIndex))
           
            hostSuffixTemp = continuousNumberSequenceAtEndOfStringRegex.search(str(hostName))

            if hostSuffixTemp != None:
                hostSuffix = hostSuffixTemp.group(1)
                jmsTopicSubDeploymentName = str(jmsTopicSubDeploymentName).replace('REPLACE_MACHINE_SUFFIX', hostSuffix)
            else:
                if (str(hostName)[-3:])[0].isdigit():
                    jmsTopicSubDeploymentName = str(jmsTopicSubDeploymentName).replace('REPLACE_MACHINE_SUFFIX', str(hostName)[-3:])
                else:
                    jmsTopicSubDeploymentName = str(jmsTopicSubDeploymentName).replace('REPLACE_MACHINE_SUFFIX', str(hostName)[-2:])

        jmsTopicTypeNodeCount = individualJMSTopicNode.getElementsByTagName("Type").length
    
        if jmsTopicTypeNodeCount == 0:
            log.debug('There is no Type tag under the parent Topic tag. Bypassing creating any JMS topics...\n')
            return
        else:
            #Get the name for JMS subdeployment     
            if individualJMSTopicNode.getElementsByTagName("Type").item(0).childNodes.item(0) != None:    
                jmsTopicType = individualJMSTopicNode.getElementsByTagName("Type").item(0).childNodes.item(0).data
            else:
                log.debug('The Type tag under the parent Topic tag is empty. Bypassing creating any JMS topics...\n')
                return

        if jmsTopicType == "Local":
            #Create JMS topic
            log.debug('Creating JMS topic : ' + jmsTopicName + ' and targetting it to : ' + jmsModuleName + '\n')
            createLocalTopic(jmsTopicName, jmsModuleName)
       
            log.debug('Setting properties for JMS topics : ' + str(jmsTopicName) + '\n')
            setPropertiesForTopic(jmsTopicName, jmsModuleName, jmsTopicJNDIName, jmsTopicSubDeploymentName)
        
        elif jmsTopicType == "Distributed":
            #Create JMS topic
            log.debug('Creating JMS topic : ' + jmsTopicName + ' and targetting it to : ' + jmsModuleName + '\n')
            createDistributedTopic(jmsTopicName, jmsModuleName)
       
            jmsTopicReDeliveryDelayNodeCount = individualJMSTopicNode.getElementsByTagName("ReDeliveryDelay").length
    
            if jmsTopicReDeliveryDelayNodeCount == 0:
                log.debug('There is no ReDeliveryDelay tag under the parent Topic tag. Will not change the default value...\n')
                jmsTopicRedeliveryDelay = None
            else:
                #Get the name for JMS subdeployment     
                if individualJMSTopicNode.getElementsByTagName("ReDeliveryDelay").item(0).childNodes.item(0) != None:    
                    jmsTopicRedeliveryDelay = individualJMSTopicNode.getElementsByTagName("ReDeliveryDelay").item(0).childNodes.item(0).data
                else:
                    log.debug('The ReDeliveryDelay tag under the parent Topic tag is empty. Will not change the default value...\n')
                    jmsTopicRedeliveryDelay = None

            jmsTopicRedeliveryLimitNodeCount = individualJMSTopicNode.getElementsByTagName("ReDeliveryLimit").length
    
            if jmsTopicRedeliveryLimitNodeCount == 0:
                log.debug('There is no ReDeliveryLimit tag under the parent Topic tag. Will not change the default value...\n')
                jmsTopicRedeliveryLimit = None
            else:
                #Get the name for JMS subdeployment     
                if individualJMSTopicNode.getElementsByTagName("ReDeliveryLimit").item(0).childNodes.item(0) != None:    
                    jmsTopicRedeliveryLimit = individualJMSTopicNode.getElementsByTagName("ReDeliveryLimit").item(0).childNodes.item(0).data
                else:
                    log.debug('The ReDeliveryLimit tag under the parent Topic tag is empty. Will not change the default value...\n')
                    jmsTopicRedeliveryLimit = None

            jmsTopicLoadBalancingPolicyNodeCount = individualJMSTopicNode.getElementsByTagName("LoadBalancingPolicy").length
    
            if jmsTopicLoadBalancingPolicyNodeCount == 0:
                log.debug('There is no LoadBalancingPolicy tag under the parent Topic tag. Will not change the default value...\n')
                jmsTopicLoadBalancingPolicy = None
            else:
                #Get the name for JMS subdeployment     
                if individualJMSTopicNode.getElementsByTagName("LoadBalancingPolicy").item(0).childNodes.item(0) != None:    
                    jmsTopicLoadBalancingPolicy = individualJMSTopicNode.getElementsByTagName("LoadBalancingPolicy").item(0).childNodes.item(0).data
                else:
                    log.debug('The LoadBalancingPolicy tag under the parent Topic tag is empty. Will not change the default value...\n')
                    jmsTopicLoadBalancingPolicy = None

            log.info('Setting properties for JMS topics : ' + str(jmsTopicName) + '\n')
            setPropertiesForDistributedTopic(jmsTopicName, jmsModuleName, jmsTopicJNDIName, jmsTopicSubDeploymentName, jmsTopicRedeliveryDelay, jmsTopicRedeliveryLimit, jmsTopicLoadBalancingPolicy)

def readConfigurationFileAndCreateJMSQueue(individualJMSModuleNode, managedServerName, hostName, managedServerIndex, jmsModuleName):
    #Initialize a regular expression for getting the last number in a string
    continuousNumberSequenceAtEndOfStringRegex = re.compile('(\d+)$')
    
    jmsQueueNodeCount = individualJMSModuleNode.getElementsByTagName("Queue").length

    if jmsQueueNodeCount == 0:
        log.debug('There is no Queue tag under the parent JMSModules for JMS module : ' + str(jmsModuleName) + ' . Bypassing creating any JMS queues...\n')
        return

    jmsQueueNodeList = individualJMSModuleNode.getElementsByTagName("Queue")

    for i in range(jmsQueueNodeList.length):
        individualJMSQueueNode = jmsQueueNodeList.item(i);

        jmsQueueNameNodeCount = individualJMSQueueNode.getElementsByTagName("Name").length
    
        if jmsQueueNameNodeCount == 0:
            log.debug('There is no Name tag under the parent Queue tag. Bypassing creating any JMS queues...\n')
            return
        else:
            #Get the name for JMS subdeployment     
            if individualJMSQueueNode.getElementsByTagName("Name").item(0).childNodes.item(0) != None:    
                jmsQueueName = individualJMSQueueNode.getElementsByTagName("Name").item(0).childNodes.item(0).data
            else:
                log.debug('The Name tag under the parent Queue tag is empty. Bypassing creating any JMS queues...\n')
                return

        log.debug('The JMS queue name is of the pattern : ' + jmsQueueName + '\n')
   
        if (str(jmsQueueName).find("REPLACE_MACHINE_SUFFIX") != -1) or (str(jmsQueueName).find("REPLACE_MANAGED_SERVER_INDEX") != -1 ):
            log.debug('Replacing patterns in the JMS queue name : ' + jmsQueueName + '\n')
                   
            jmsQueueName = str(jmsQueueName).replace('REPLACE_MANAGED_SERVER_INDEX', str(managedServerIndex))
           
            hostSuffixTemp = continuousNumberSequenceAtEndOfStringRegex.search(str(hostName))

            if hostSuffixTemp != None:
                hostSuffix = hostSuffixTemp.group(1)
                jmsQueueName = str(jmsQueueName).replace('REPLACE_MACHINE_SUFFIX', hostSuffix)
            else:
                if (str(hostName)[-3:])[0].isdigit():
                    jmsQueueName = str(jmsQueueName).replace('REPLACE_MACHINE_SUFFIX', str(hostName)[-3:])
                else:
                    jmsQueueName = str(jmsQueueName).replace('REPLACE_MACHINE_SUFFIX', str(hostName)[-2:])

        jmsQueueJNDINameNodeCount = individualJMSQueueNode.getElementsByTagName("JNDIName").length
    
        if jmsQueueJNDINameNodeCount == 0:
            log.debug('There is no JNDIName tag under the parent Queue tag. Setting it to empty...\n')
            jmsQueueJNDIName = None
        else: 
            #Get the name for JMS subdeployment     
            if individualJMSQueueNode.getElementsByTagName("JNDIName").item(0).childNodes.item(0) != None:    
                jmsQueueJNDIName = individualJMSQueueNode.getElementsByTagName("JNDIName").item(0).childNodes.item(0).data
            else:
                log.debug('The JNDIName tag under the parent Queue tag is empty...\n')
                jmsQueueJNDIName = None

        jmsQueueSubDeploymentNameNodeCount = individualJMSQueueNode.getElementsByTagName("SubDeploymentName").length
    
        if jmsQueueSubDeploymentNameNodeCount == 0:
            log.debug('There is no sub deployment name tags under the parent Queue tag. Not targetting the JMS queue to any sub deployment...\n')
            jmsQueueSubDeploymentName = None
        else: 
            #Get the name for JMS subdeployment     
            if individualJMSQueueNode.getElementsByTagName("SubDeploymentName").item(0).childNodes.item(0) != None:    
                jmsQueueSubDeploymentName = individualJMSQueueNode.getElementsByTagName("SubDeploymentName").item(0).childNodes.item(0).data
            else:
                log.debug('The SubDeploymentName tag under the parent Queue tag is empty. Not targetting the JMS queue to any sub deployment...\n')
                jmsQueueSubDeploymentName = None

        if (str(jmsQueueSubDeploymentName).find("REPLACE_MACHINE_SUFFIX") != -1) or (str(jmsQueueSubDeploymentName).find("REPLACE_MANAGED_SERVER_INDEX") != -1 ):
            log.debug('Replacing patterns in the sub deployment name : ' + jmsQueueSubDeploymentName + '\n')
            
            jmsQueueSubDeploymentName = str(jmsQueueSubDeploymentName).replace('REPLACE_MANAGED_SERVER_INDEX', str(managedServerIndex))
           
            hostSuffixTemp = continuousNumberSequenceAtEndOfStringRegex.search(str(hostName))

            if hostSuffixTemp != None:
                hostSuffix = hostSuffixTemp.group(1)
                jmsQueueSubDeploymentName = str(jmsQueueSubDeploymentName).replace('REPLACE_MACHINE_SUFFIX', hostSuffix)
            else:
                if (str(hostName)[-3:])[0].isdigit():
                    jmsQueueSubDeploymentName = str(jmsQueueSubDeploymentName).replace('REPLACE_MACHINE_SUFFIX', str(hostName)[-3:])
                else:
                    jmsQueueSubDeploymentName = str(jmsQueueSubDeploymentName).replace('REPLACE_MACHINE_SUFFIX', str(hostName)[-2:])

        jmsQueueTypeNodeCount = individualJMSQueueNode.getElementsByTagName("Type").length
    
        if jmsQueueTypeNodeCount == 0:
            log.debug('There is no Type tag under the parent Queue tag. Bypassing creating any JMS queues...\n')
            return
        else:
            #Get the name for JMS subdeployment     
            if individualJMSQueueNode.getElementsByTagName("Type").item(0).childNodes.item(0) != None:    
                jmsQueueType = individualJMSQueueNode.getElementsByTagName("Type").item(0).childNodes.item(0).data
            else:
                log.debug('The Type tag under the parent Queue tag is empty. Bypassing creating any JMS queues...\n')
                return

        if jmsQueueType == "Distributed":
            #Create JMS queue
            log.debug('Creating JMS queue : ' + jmsQueueName + ' and targetting it to : ' + jmsModuleName + '\n')
            createDistributedQueue(jmsQueueName, jmsModuleName)
       
            jmsQueueReDeliveryDelayNodeCount = individualJMSQueueNode.getElementsByTagName("ReDeliveryDelay").length
    
            if jmsQueueReDeliveryDelayNodeCount == 0:
                log.debug('There is no ReDeliveryDelay tag under the parent Queue tag. Will not change the default value...\n')
                jmsQueueRedeliveryDelay = None
            else:
                #Get the name for JMS subdeployment     
                if individualJMSQueueNode.getElementsByTagName("ReDeliveryDelay").item(0).childNodes.item(0) != None:    
                    jmsQueueRedeliveryDelay = individualJMSQueueNode.getElementsByTagName("ReDeliveryDelay").item(0).childNodes.item(0).data
                else:
                    log.debug('The ReDeliveryDelay tag under the parent Queue tag is empty. Will not change the default value...\n')
                    jmsQueueRedeliveryDelay = None

            jmsQueueRedeliveryLimitNodeCount = individualJMSQueueNode.getElementsByTagName("ReDeliveryLimit").length
    
            if jmsQueueRedeliveryLimitNodeCount == 0:
                log.debug('There is no ReDeliveryLimit tag under the parent Queue tag. Will not change the default value...\n')
                jmsQueueRedeliveryLimit = None
            else:
                #Get the name for JMS subdeployment     
                if individualJMSQueueNode.getElementsByTagName("ReDeliveryLimit").item(0).childNodes.item(0) != None:    
                    jmsQueueRedeliveryLimit = individualJMSQueueNode.getElementsByTagName("ReDeliveryLimit").item(0).childNodes.item(0).data
                else:
                    log.debug('The ReDeliveryLimit tag under the parent Queue tag is empty. Will not change the default value...\n')
                    jmsQueueRedeliveryLimit = None

            jmsQueueLoadBalancingPolicyNodeCount = individualJMSQueueNode.getElementsByTagName("LoadBalancingPolicy").length
    
            if jmsQueueLoadBalancingPolicyNodeCount == 0:
                log.debug('There is no LoadBalancingPolicy tag under the parent Queue tag. Will not change the default value...\n')
                jmsQueueLoadBalancingPolicy = None
            else:
                #Get the name for JMS subdeployment     
                if individualJMSQueueNode.getElementsByTagName("LoadBalancingPolicy").item(0).childNodes.item(0) != None:    
                    jmsQueueLoadBalancingPolicy = individualJMSQueueNode.getElementsByTagName("LoadBalancingPolicy").item(0).childNodes.item(0).data
                else:
                    log.debug('The LoadBalancingPolicy tag under the parent Queue tag is empty. Will not change the default value...\n')
                    jmsQueueLoadBalancingPolicy = None

            jmsQueueErrorDestinationNodeCount = individualJMSQueueNode.getElementsByTagName("ErrorDestination").length
    
            if jmsQueueErrorDestinationNodeCount == 0:
                log.debug('There is no ErrorDestination tag under the parent Queue tag. Will not change the default value...\n')
                jmsQueueErrorDestination = None
            else:
                #Get the name for JMS subdeployment     
                if individualJMSQueueNode.getElementsByTagName("ErrorDestination").item(0).childNodes.item(0) != None:    
                    jmsQueueErrorDestination = individualJMSQueueNode.getElementsByTagName("ErrorDestination").item(0).childNodes.item(0).data
                else:
                    log.debug('The ErrorDestination tag under the parent Queue tag is empty. Will not change the default value...\n')
                    jmsQueueErrorDestination = None

            jmsQueueMaximumMessageSizeNodeCount = individualJMSQueueNode.getElementsByTagName("MaximumMessageSize").length
    
            if jmsQueueMaximumMessageSizeNodeCount == 0:
                log.debug('There is no MaximumMessageSize tag under the parent Queue tag. Will not change the default value...\n')
                jmsQueueMaximumMessageSize = None
            else:
                #Get the name for JMS subdeployment     
                if individualJMSQueueNode.getElementsByTagName("MaximumMessageSize").item(0).childNodes.item(0) != None:    
                    jmsQueueMaximumMessageSize = individualJMSQueueNode.getElementsByTagName("MaximumMessageSize").item(0).childNodes.item(0).data
                else:
                    log.debug('The MaximumMessageSize tag under the parent Queue tag is empty. Will not change the default value...\n')
                    jmsQueueMaximumMessageSize = None
           
            jmsQueueForwardDelayNodeCount = individualJMSQueueNode.getElementsByTagName("ForwardDelay").length

            if jmsQueueForwardDelayNodeCount == 0:
                log.debug('There is no ForwardDelay tag under the parent Queue tag. Will not change the default value...\n')
                jmsQueueForwardDelay = None
            else:
                #Get the name for JMS subdeployment
                if individualJMSQueueNode.getElementsByTagName("ForwardDelay").item(0).childNodes.item(0) != None:
                    jmsQueueForwardDelay = individualJMSQueueNode.getElementsByTagName("ForwardDelay").item(0).childNodes.item(0).data
                else:
                    log.debug('The ForwardDelat tag under the parent Queue tag is empty. Will not change the default value...\n')
                    jmsQueueForwardDelay = None

            jmsQueueExpirationPolicyNodeCount = individualJMSQueueNode.getElementsByTagName("ExpirationPolicy").length
    
            if jmsQueueExpirationPolicyNodeCount == 0:
                log.debug('There is no ExpirationPolicy tag under the parent Queue tag. Will not change the default value...\n')
                jmsQueueExpirationPolicy = None
            else:
                #Get the name for JMS subdeployment     
                if individualJMSQueueNode.getElementsByTagName("ExpirationPolicy").item(0).childNodes.item(0) != None:    
                    jmsQueueExpirationPolicy = individualJMSQueueNode.getElementsByTagName("ExpirationPolicy").item(0).childNodes.item(0).data
                else:
                    log.debug('The ExpirationPolicy tag under the parent Queue tag is empty. Will not change the default value...\n')
                    jmsQueueExpirationPolicy = None

            jmsQueueTimeToLiveNodeCount = individualJMSQueueNode.getElementsByTagName("TimeToLive").length
    
            if jmsQueueTimeToLiveNodeCount == 0:
                log.debug('There is no TimeToLive tag under the parent Queue tag. Will not change the default value...\n')
                jmsQueueTimeToLive = None
            else:
                #Get the name for JMS subdeployment     
                if individualJMSQueueNode.getElementsByTagName("TimeToLive").item(0).childNodes.item(0) != None:    
                    jmsQueueTimeToLive = individualJMSQueueNode.getElementsByTagName("TimeToLive").item(0).childNodes.item(0).data
                else:
                    log.debug('The TimeToLive tag under the parent Queue tag is empty. Will not change the default value...\n')
                    jmsQueueTimeToLive = None

            log.info('Setting properties for JMS queues : ' + str(jmsQueueName) + '\n')
            setPropertiesForDistributedQueue(jmsQueueName, jmsQueueJNDIName, jmsQueueSubDeploymentName, jmsModuleName, jmsQueueRedeliveryDelay, jmsQueueRedeliveryLimit, jmsQueueLoadBalancingPolicy, jmsQueueErrorDestination, jmsQueueMaximumMessageSize, jmsQueueForwardDelay, jmsQueueExpirationPolicy, jmsQueueTimeToLive)

def readConfigurationFileAndCreateJMSConnectionFactories(individualJMSModuleNode, managedServerName, hostName, managedServerIndex, jmsModuleName):
    #Initialize a regular expression for getting the last number in a string
    continuousNumberSequenceAtEndOfStringRegex = re.compile('(\d+)$')
    
    jmsConnectionFactoryNodeCount = individualJMSModuleNode.getElementsByTagName("ConnectionFactory").length

    if jmsConnectionFactoryNodeCount == 0:
        log.debug('There is no ConnectionFactory tag under the parent JMSModules for JMS module : ' + str(jmsModuleName) + ' . Bypassing creating any connection factories...\n')
        return

    jmsConnectionFactoryNodeList = individualJMSModuleNode.getElementsByTagName("ConnectionFactory")

    for i in range(jmsConnectionFactoryNodeList.length):
        individualJMSConnectionFactoryNode = jmsConnectionFactoryNodeList.item(i);

        jmsConnectionFactoryNameNodeCount = individualJMSConnectionFactoryNode.getElementsByTagName("Name").length
    
        if jmsConnectionFactoryNameNodeCount == 0:
            log.debug('There is no Name tag under the parent ConnectionFactory tag. Bypassing creating any JMS connection factories...\n')
            return
        else:        
            #Get the name for JMS subdeployment     
            if individualJMSConnectionFactoryNode.getElementsByTagName("Name").item(0).childNodes.item(0) != None:    
                jmsConnectionFactoryName = individualJMSConnectionFactoryNode.getElementsByTagName("Name").item(0).childNodes.item(0).data
            else:
                log.debug('The Name tag under the parent ConnectionFactory tag is empty. Bypassing creating any JMS connection factories...\n')
                return

        log.debug('The JMS connection factory name is of the pattern : ' + jmsConnectionFactoryName + '\n')
   
        if (str(jmsConnectionFactoryName).find("REPLACE_MACHINE_SUFFIX") != -1) or (str(jmsConnectionFactoryName).find("REPLACE_MANAGED_SERVER_INDEX") != -1 ):
            log.debug('Replacing patterns in the JMS connection factory name : ' + jmsConnectionFactoryName + '\n')
                   
            jmsConnectionFactoryName = str(jmsConnectionFactoryName).replace('REPLACE_MANAGED_SERVER_INDEX', str(managedServerIndex))
           
            hostSuffixTemp = continuousNumberSequenceAtEndOfStringRegex.search(str(hostName))

            if hostSuffixTemp != None:
                hostSuffix = hostSuffixTemp.group(1)
                jmsConnectionFactoryName = str(jmsConnectionFactoryName).replace('REPLACE_MACHINE_SUFFIX', hostSuffix)
            else:
                if (str(hostName)[-3:])[0].isdigit():
                    jmsConnectionFactoryName = str(jmsConnectionFactoryName).replace('REPLACE_MACHINE_SUFFIX', str(hostName)[-3:])
                else:
                    jmsConnectionFactoryName = str(jmsConnectionFactoryName).replace('REPLACE_MACHINE_SUFFIX', str(hostName)[-2:])

        jmsConnectionFactoryJNDINameNodeCount = individualJMSConnectionFactoryNode.getElementsByTagName("JNDIName").length
    
        if jmsConnectionFactoryJNDINameNodeCount == 0:
            log.debug('There is no JNDIName tag under the parent ConnectionFactory tag. Setting it to empty...\n')
            jmsConnectionFactoryJNDIName = None
        else: 
            #Get the name for JMS subdeployment     
            if individualJMSConnectionFactoryNode.getElementsByTagName("JNDIName").item(0).childNodes.item(0) != None:    
                jmsConnectionFactoryJNDIName = individualJMSConnectionFactoryNode.getElementsByTagName("JNDIName").item(0).childNodes.item(0).data
            else:
                log.debug('The JNDIName tag under the parent ConnectionFactory tag is empty...\n')
                jmsConnectionFactoryJNDIName = None

        jmsConnectionFactoryDefaultDeliveryModeNodeCount = individualJMSConnectionFactoryNode.getElementsByTagName("DefaultDeliveryMode").length
    
        if jmsConnectionFactoryDefaultDeliveryModeNodeCount == 0:
            log.debug('There is no DefaultDeliveryMode tag under the parent ConnectionFactory tag. Setting it to default...\n')
            jmsConnectionFactoryDefaultDeliveryMode = None
        else: 
            #Get the name for JMS subdeployment     
            if individualJMSConnectionFactoryNode.getElementsByTagName("DefaultDeliveryMode").item(0).childNodes.item(0) != None:    
                jmsConnectionFactoryDefaultDeliveryMode = individualJMSConnectionFactoryNode.getElementsByTagName("DefaultDeliveryMode").item(0).childNodes.item(0).data
            else:
                log.debug('The DefaultDeliveryMode tag under the parent ConnectionFactory tag is empty...\n')
                jmsConnectionFactoryDefaultDeliveryMode = None

        jmsConnectionFactoryXAConnectionFactoryEnabledNodeCount = individualJMSConnectionFactoryNode.getElementsByTagName("XAConnectionFactoryEnabled").length
    
        if jmsConnectionFactoryXAConnectionFactoryEnabledNodeCount == 0:
            log.debug('There is no XAConnectionFactoryEnabled tag under the parent ConnectionFactory tag. Setting it to default...\n')
            jmsConnectionFactoryXAConnectionFactoryEnabled = None
        else: 
            #Get the name for JMS subdeployment     
            if individualJMSConnectionFactoryNode.getElementsByTagName("XAConnectionFactoryEnabled").item(0).childNodes.item(0) != None:    
                jmsConnectionFactoryXAConnectionFactoryEnabled = individualJMSConnectionFactoryNode.getElementsByTagName("XAConnectionFactoryEnabled").item(0).childNodes.item(0).data
            else:
                log.debug('The XAConnectionFactoryEnabled tag under the parent ConnectionFactory tag is empty...\n')
                jmsConnectionFactoryXAConnectionFactoryEnabled = None

        jmsConnectionFactoryAttachJMXUserIDNodeCount = individualJMSConnectionFactoryNode.getElementsByTagName("AttachJMXUserID").length
    
        if jmsConnectionFactoryAttachJMXUserIDNodeCount == 0:
            log.debug('There is no AttachJMXUserID tag under the parent ConnectionFactory tag. Setting it to default...\n')
            jmsConnectionFactoryAttachJMXUserID = None
        else: 
            #Get the name for JMS subdeployment     
            if individualJMSConnectionFactoryNode.getElementsByTagName("AttachJMXUserID").item(0).childNodes.item(0) != None:    
                jmsConnectionFactoryAttachJMXUserID = individualJMSConnectionFactoryNode.getElementsByTagName("AttachJMXUserID").item(0).childNodes.item(0).data
            else:
                log.debug('The AttachJMXUserID tag under the parent ConnectionFactory tag is empty...\n')
                jmsConnectionFactoryAttachJMXUserID = None

        jmsConnectionFactorySubDeploymentNameNodeCount = individualJMSConnectionFactoryNode.getElementsByTagName("SubDeploymentName").length
    
        if jmsConnectionFactorySubDeploymentNameNodeCount == 0:
            log.debug('There is no sub deployment name tags under the parent ConnectionFactory tag. Not targetting the connection factory to any sub deployment...\n')
            jmsConnectionFactorySubDeploymentName = None
        else: 
            #Get the name for JMS subdeployment     
            if individualJMSConnectionFactoryNode.getElementsByTagName("SubDeploymentName").item(0).childNodes.item(0) != None:    
                jmsConnectionFactorySubDeploymentName = individualJMSConnectionFactoryNode.getElementsByTagName("SubDeploymentName").item(0).childNodes.item(0).data
            else:
                log.debug('The SubDeploymentName tag under the parent ConnectionFactory tag is empty. Not targetting the connection factory to any sub deployment...\n')
                jmsConnectionFactorySubDeploymentName = None

        if (str(jmsConnectionFactorySubDeploymentName).find("REPLACE_MACHINE_SUFFIX") != -1) or (str(jmsConnectionFactorySubDeploymentName).find("REPLACE_MANAGED_SERVER_INDEX") != -1 ):
            log.debug('Replacing patterns in the connection factory name : ' + jmsConnectionFactorySubDeploymentName + '\n')
            
            jmsConnectionFactorySubDeploymentName = str(jmsConnectionFactorySubDeploymentName).replace('REPLACE_MANAGED_SERVER_INDEX', str(managedServerIndex))
           
            hostSuffixTemp = continuousNumberSequenceAtEndOfStringRegex.search(str(hostName))

            if hostSuffixTemp != None:
                hostSuffix = hostSuffixTemp.group(1)
                jmsConnectionFactorySubDeploymentName = str(jmsConnectionFactorySubDeploymentName).replace('REPLACE_MACHINE_SUFFIX', hostSuffix)
            else:
                if (str(hostName)[-3:])[0].isdigit():
                    jmsConnectionFactorySubDeploymentName = str(jmsConnectionFactorySubDeploymentName).replace('REPLACE_MACHINE_SUFFIX', str(hostName)[-3:])
                else:
                    jmsConnectionFactorySubDeploymentName = str(jmsConnectionFactorySubDeploymentName).replace('REPLACE_MACHINE_SUFFIX', str(hostName)[-2:])

                  
        #Create JMS sub deployment
        log.info('Creating subdeployment : ' + str(jmsConnectionFactoryName) + ' and targetting it to : ' + str(jmsModuleName) + '\n')
        createConnectionFactory(str(jmsConnectionFactoryName), str(jmsModuleName))
       
        log.info('Setting properties for connection factory : ' + str(jmsConnectionFactoryName) + '\n')
        setPropertiesForConnectionFactory(jmsModuleName, jmsConnectionFactoryName, jmsConnectionFactoryJNDIName, jmsConnectionFactorySubDeploymentName, jmsConnectionFactoryDefaultDeliveryMode, jmsConnectionFactoryAttachJMXUserID, jmsConnectionFactoryXAConnectionFactoryEnabled)

def readConfigurationFileAndCreateJMSSubDeployments(individualJMSModuleNode, managedServerName, hostName, managedServerIndex, jmsModuleName):
    #Initialize a regular expression for getting the last number in a string
    continuousNumberSequenceAtEndOfStringRegex = re.compile('(\d+)$')
    
    jmsSubDeploymentNodeCount = individualJMSModuleNode.getElementsByTagName("SubDeployment").length

    if jmsSubDeploymentNodeCount == 0:
        log.debug('There is no jmsSubDeploymentNodeCount tag under the parent JMSModules for JMS module : ' + str(jmsModuleName) + ' . Bypassing creating any JMS modules...\n')
        return

    jmsSubDeploymentNodeList = individualJMSModuleNode.getElementsByTagName("SubDeployment")

    for i in range(jmsSubDeploymentNodeList.length):
        individualJMSSubDeploymentNode = jmsSubDeploymentNodeList.item(i);

        jmsSubDeploymentNameNodeCount = individualJMSSubDeploymentNode.getElementsByTagName("Name").length
    
        if jmsSubDeploymentNameNodeCount == 0:
            log.debug('There is no Name tag under the parent SubDeployment tag. Bypassing creating any JMS sub-deployments...\n')
            return
        else:        
            #Get the name for JMS subdeployment     
            if individualJMSSubDeploymentNode.getElementsByTagName("Name").item(0).childNodes.item(0) != None:    
                jmsSubDeploymentName = individualJMSSubDeploymentNode.getElementsByTagName("Name").item(0).childNodes.item(0).data
            else:
                log.debug('The Name tag under the parent SubDeployment tag is empty. Bypassing creating any JMS sub-deployments...\n')
                return

        log.debug('The JMS subdeployment name is of the pattern : ' + jmsSubDeploymentName + '\n')
   
        if (str(jmsSubDeploymentName).find("REPLACE_MACHINE_SUFFIX") != -1) or (str(jmsSubDeploymentName).find("REPLACE_MANAGED_SERVER_INDEX") != -1 ):
            log.debug('Replacing patterns in the JMS sub deployment name : ' + jmsSubDeploymentName + '\n')
                   
            jmsSubDeploymentName = str(jmsSubDeploymentName).replace('REPLACE_MANAGED_SERVER_INDEX', str(managedServerIndex))
           
            hostSuffixTemp = continuousNumberSequenceAtEndOfStringRegex.search(str(hostName))

            if hostSuffixTemp != None:
                hostSuffix = hostSuffixTemp.group(1)
                jmsSubDeploymentName = str(jmsSubDeploymentName).replace('REPLACE_MACHINE_SUFFIX', hostSuffix)
            else:
                if (str(hostName)[-3:])[0].isdigit():
                    jmsSubDeploymentName = str(jmsSubDeploymentName).replace('REPLACE_MACHINE_SUFFIX', str(hostName)[-3:])
                else:
                    jmsSubDeploymentName = str(jmsSubDeploymentName).replace('REPLACE_MACHINE_SUFFIX', str(hostName)[-2:])

        jmsSubDeploymentTargetsNodeCount = individualJMSSubDeploymentNode.getElementsByTagName("Targets").length
    
        if jmsSubDeploymentTargetsNodeCount == 0:
            log.debug('There is no Targets tag under the parent SubDeployment tag. Bypassing creating any JMS sub-deployments...\n')
            return
        else:        
            #Get the name for JMS subdeployment     
            if individualJMSSubDeploymentNode.getElementsByTagName("Targets").item(0).childNodes.item(0) != None:    
                targets = individualJMSSubDeploymentNode.getElementsByTagName("Targets").item(0).childNodes.item(0).data
            else:
                log.debug('The Targets tag under the parent SubDeployment tag is empty. Bypassing creating any JMS sub-deployments...\n')
                return

        log.debug('The JMS subdeployment target is of the pattern : ' + targets + '\n')

        #Create JMS sub deployment
        log.debug('Creating subdeployment : ' + str(jmsSubDeploymentName) +  '\n')
        createSubDeployment(jmsSubDeploymentName, jmsModuleName)
        
        spaceSeparatedSubDeploymentTarget = str(targets).replace(",", " ")
        spaceSeparatedSubDeploymentTargetList = spaceSeparatedSubDeploymentTarget.split() 

        for jmsSubDeploymentTargets in spaceSeparatedSubDeploymentTargetList:
            if (str(jmsSubDeploymentTargets).find("REPLACE_MACHINE_SUFFIX") != -1) or (str(jmsSubDeploymentTargets).find("REPLACE_MANAGED_SERVER_INDEX") != -1 ):
                log.debug('Replacing patterns in the JMS sub deployment targets : ' + jmsSubDeploymentTargets + '\n')
                   
                jmsSubDeploymentTargets = str(jmsSubDeploymentTargets).replace('REPLACE_MANAGED_SERVER_INDEX', str(managedServerIndex))
           
                hostSuffixTemp = continuousNumberSequenceAtEndOfStringRegex.search(str(hostName))

                if hostSuffixTemp != None:
                    hostSuffix = hostSuffixTemp.group(1)
                    jmsSubDeploymentTargets = str(jmsSubDeploymentTargets).replace('REPLACE_MACHINE_SUFFIX', hostSuffix)
                else:
                    if (str(hostName)[-3:])[0].isdigit():
                        jmsSubDeploymentTargets = str(jmsSubDeploymentTargets).replace('REPLACE_MACHINE_SUFFIX', str(hostName)[-3:])
                    else:
                        jmsSubDeploymentTargets = str(jmsSubDeploymentTargets).replace('REPLACE_MACHINE_SUFFIX', str(hostName)[-2:])
                            
            log.debug('Targetting subdeployment : ' + str(jmsSubDeploymentName) + ' to : ' + str(jmsSubDeploymentTargets) + '\n')
            setTargetsForSubdeployment(jmsSubDeploymentName, jmsSubDeploymentTargets, jmsModuleName)

def readConfigurationFileAndCreateJMSModules(parentNode, managedServerName, hostName, managedServerIndex):
    #Initialize a regular expression for getting the last number in a string
    continuousNumberSequenceAtEndOfStringRegex = re.compile('(\d+)$')

    jmsModulesNodeCount = parentNode.getElementsByTagName("JMSModules").length

    if jmsModulesNodeCount == 0:
        log.debug('There is no JMSModules tag under the parent JMSResources tag. Bypassing creating any JMS modules...\n')
        return

    jmsModulesNodeList = parentNode.getElementsByTagName("JMSModules")

    for i in range(jmsModulesNodeList.length):
        individualJMSModuleNode = jmsModulesNodeList.item(i);

        jmsModuleNameNodeCount = individualJMSModuleNode.getElementsByTagName("Name").length

        if jmsModuleNameNodeCount == 0:
            log.debug('\nThe Name node is missing in the from the parent JMSModules node. Bypassing creating any JMS modules\n')
            discardChanges()

        if individualJMSModuleNode.getElementsByTagName("Name").item(0).childNodes.item(0) != None:
            jmsModuleName = individualJMSModuleNode.getElementsByTagName("Name").item(0).childNodes.item(0).data
        else:
            log.debug('Bypassing creating JMS modules since the Name tag is empty...\n')
            discardChanges()

        jmsModuleTargetsNodeCount = individualJMSModuleNode.getElementsByTagName("Targets").length

        if jmsModuleTargetsNodeCount == 0:
            log.debug('\nThe Targets node is missing in the from the parent JMSServers node. Aborting...\n')
            discardChanges()

        if individualJMSModuleNode.getElementsByTagName("Targets").item(0).childNodes.item(0) != None:
            targets = individualJMSModuleNode.getElementsByTagName("Targets").item(0).childNodes.item(0).data
        else:
            log.debug('\nThe Targets node is missing in the from the parent JMSModules node. Aborting...\n')
            discardChanges()

        #Create JMS module
        log.debug('Creating JMS module : ' + str(jmsModuleName) + '\n')
        createJMSSystemResource(str(jmsModuleName))
        log.debug('Successfully created JMS module : ' + str(jmsModuleName) + '\n')

        spaceSeparatedModuleTarget = str(targets).replace(",", " ")
        spaceSeparatedModuleTargetList = spaceSeparatedModuleTarget.split() 

        for jmsModuleTargets in spaceSeparatedModuleTargetList:
            if (str(jmsModuleTargets).find("REPLACE_HOSTNAME") != -1) or (str(jmsModuleTargets).find("REPLACE_MANAGED_SERVER_INDEX") != -1 ):
                log.debug('Replacing patterns in the JMS module targets : ' + jmsModuleTargets + '\n')
                   
                jmsModuleTargets = str(jmsModuleTargets).replace('REPLACE_HOSTNAME', str(hostName))
           
                hostSuffixTemp = continuousNumberSequenceAtEndOfStringRegex.search(str(managedServerName))

                if hostSuffixTemp != None:
                    hostSuffix = hostSuffixTemp.group(1)
                    jmsModuleTargets = str(jmsModuleTargets).replace('REPLACE_MANAGED_SERVER_INDEX', hostSuffix)
                
            log.debug('Setting targets for JMS module : ' + str(jmsModuleName) + ' to : ' + str(jmsModuleTargets) + '\n')
            setTargetForJMSSystemResource(jmsModuleName, jmsModuleTargets)
            log.debug('Successfully set the targets for JMS module : ' + str(jmsModuleName) + ' to : ' + str(jmsModuleTargets) + '\n')

        readConfigurationFileAndCreateJMSSubDeployments(individualJMSModuleNode, managedServerName, hostName, managedServerIndex, jmsModuleName)

        readConfigurationFileAndCreateJMSConnectionFactories(individualJMSModuleNode, managedServerName, hostName, managedServerIndex, jmsModuleName)

        readConfigurationFileAndCreateJMSTopics(individualJMSModuleNode, managedServerName, hostName, managedServerIndex, jmsModuleName)

        readConfigurationFileAndCreateJMSQueue(individualJMSModuleNode, managedServerName, hostName, managedServerIndex, jmsModuleName)

def readConfigurationFileAndCreateJDBCDataSources(individualNode, managedServerName, hostName, managedServerIndex):
    #Initialize a regular expression for getting the last number in a string
    continuousNumberSequenceAtEndOfStringRegex = re.compile('(\d+)$')

    dataSourceNodeCount = individualNode.getElementsByTagName("DataSource").length
    
    if dataSourceNodeCount == 0:
        log.debug('There are no tags of type DataSource. Bypassing creating any data sources...\n')
        return
    
    dataSourceList = individualNode.getElementsByTagName("DataSource")
    
    for i in range(dataSourceList.length):
        individualDataSource = dataSourceList.item(i);
    
        dataSourceNameNodeCount = individualDataSource.getElementsByTagName("Name").length

        if dataSourceNameNodeCount == 0:
            log.debug('There is no Name tag under the parent DataSource tag. Aborting...\n')
            discardChanges()
        else:
            if individualDataSource.getElementsByTagName("Name").item(0).childNodes.item(0) != None:    
                dataSourceName = individualDataSource.getElementsByTagName("Name").item(0).childNodes.item(0).data
            else:
                log.debug('DataSource Name tag is empty. Aborting...\n')
                discardChanges()

        startEditSession()
        returnValue = createJDBCSystemResource(dataSourceName)

        dataSourceJNDINameNodeCount = individualDataSource.getElementsByTagName("JNDIName").length

        if dataSourceJNDINameNodeCount == 0:
            log.debug('There is no JNDIName tag under the parent DataSource tag. Bypassing setting the JNDI name for the data source...\n')
            dataSourceJNDIName = None
        else:
            if individualDataSource.getElementsByTagName("JNDIName").item(0).childNodes.item(0) != None:    
                dataSourceJNDIName = individualDataSource.getElementsByTagName("JNDIName").item(0).childNodes.item(0).data
            else:
                log.debug('DataSource JNDIName tag is empty. Bypassing setting the JNDI name for the data source...\n')
                dataSourceJNDIName = None

        dataSourceTargetsNodeCount = individualDataSource.getElementsByTagName("Targets").length

        if dataSourceTargetsNodeCount == 0:
            log.debug('There is no Targets tag under the parent DataSource tag. Byapssing setting targets for the data source...\n')
            dataSourceTargets = None
        else:
            if individualDataSource.getElementsByTagName("Targets").item(0).childNodes.item(0) != None:    
                dataSourceTargets = individualDataSource.getElementsByTagName("Targets").item(0).childNodes.item(0).data
            else:
                log.debug('DataSource Targets tag is empty. Byapssing setting targets for the data source...\n')
                dataSourceTargets = None

        dataSourceUserNodeCount = individualDataSource.getElementsByTagName("User").length

        if dataSourceUserNodeCount == 0:
            log.debug('There is no User tag under the parent DataSource tag. Byapssing setting the user for the data source...\n')
            dataSourceUser = None
        else:
            if individualDataSource.getElementsByTagName("User").item(0).childNodes.item(0) != None:    
                dataSourceUser = individualDataSource.getElementsByTagName("User").item(0).childNodes.item(0).data
            else:
                log.debug('DataSource User tag is empty. Byapssing setting the user for the data source...\n')
                dataSourceUser = None

        dataSourcePasswordNodeCount = individualDataSource.getElementsByTagName("Password").length

        if dataSourcePasswordNodeCount == 0:
            log.debug('There is no Password tag under the parent DataSource tag. Byapssing setting the user for the data source...\n')
            dataSourcePassword = None
        else:
            if individualDataSource.getElementsByTagName("Password").item(0).childNodes.item(0) != None:    
                dataSourcePassword = individualDataSource.getElementsByTagName("Password").item(0).childNodes.item(0).data
            else:
                log.debug('DataSource Password tag is empty. Byapssing setting the password for the data source...\n')
                dataSourcePassword = None

        dataSourceURINodeCount = individualDataSource.getElementsByTagName("URI").length

        if dataSourceURINodeCount == 0:
            if returnValue == 1: 
                log.debug('There is no URI tag under the parent DataSource tag. Prompting the user to enter the details...\n')
                
                dataSourceURI = 'jdboracle:thin:'

                dataSourceDatabaseHost = raw_input("Enter the hostname for the data base server : ")
                if (dataSourceDatabaseHost == None) or (len(dataSourceDatabaseHost) == 0):
                    log.debug('You entered an empty database server name. Bypassing asking other details...\n')
                    dataSourceURI = None
                else:
                    dataSourceURI = dataSourceURI + '@' + dataSourceDatabaseHost

                    dataSourceDatabaseListenerPort = raw_input("Enter the port on which the listener is tunning on the dtabase server : ")
                    if (dataSourceDatabaseListenerPort == None) or (len(dataSourceDatabaseListenerPort) == 0):
                        log.debug('You entered an empty port number. Bypassing asking other details...\n')
                        dataSourceURI = None
                    else:
                        dataSourceURI = dataSourceURI + ':' + dataSourceDatabaseListenerPort

                        dataSourceDatabaseName = raw_input("Enter the name of the data base you want to connect to : ")
                        if (dataSourceDatabaseName == None) or (len(dataSourceDatabaseName) == 0):
                            log.debug('You entered an empty database name. Bypassing asking other details...\n')
                            dataSourceURI = None
                        else:
                            dataSourceURI = dataSourceURI + ':' + dataSourceDatabaseName
                   
                if (dataSourceUserNodeCount == 0) or (dataSourceUser == None):  
                    dataSourceUser = raw_input("Enter the username with which to connect to the database : ")
                    if (dataSourceUser == None) or (len(dataSourceUser) == 0):
                        log.debug('You entered an empty database user name. Bypassing setting the username in the data source...\n')
                        dataSourceUser = None
    
                if (dataSourcePasswordNodeCount == 0) or (dataSourcePassword == None):  
                    DoNotRevealPasswordThread = DoNotRevealPassword()
                    DoNotRevealPasswordThread.start()
                    dataSourcePassword = raw_input("Enter the password for the with which to connect to the database : ")
                    DoNotRevealPasswordThread.stopThread()
                    if (dataSourcePassword == None) or (len(dataSourcePassword) == 0):
                        log.debug('You entered an empty database user name. Bypassing setting the password in the data source...\n')
                        dataSourcePassword = None
    
                if dataSourceURI == None:
                    log.debug('The URI for the data source does not contain all the necessary properties.\n')
                    log.debug('If we target the data source to managed servers/clusters, there will be a problem in brining up the servers.\n')
                    log.debug('The data source needs to be targetted to appropriate servers/clusters at later.\n')
                    dataSourceTargets = None
            else: 
                log.debug('There is no URI tag under the parent DataSource tag. Bypassing setting the URI for the datasource...\n')
                dataSourceURI = None
        else:
            if individualDataSource.getElementsByTagName("URI").item(0).childNodes.item(0) != None:    
                dataSourceURI = individualDataSource.getElementsByTagName("URI").item(0).childNodes.item(0).data
            else:
                if returnValue == 1: 
                    log.debug('DataSource URI tag is empty. Prompting the user to enter details...\n')
                
                    dataSourceURI = 'jdboracle:thin:'

                    dataSourceDatabaseHost = raw_input("Enter the hostname for the data base server : ")
                    if (dataSourceDatabaseHost == None) or (len(dataSourceDatabaseHost) == 0):
                        log.debug('You entered an empty database server name. Bypassing asking other details...\n')
                        dataSourceURI = None
                    else:
                        dataSourceURI = dataSourceURI + '@' + dataSourceDatabaseHost

                        dataSourceDatabaseListenerPort = raw_input("Enter the port on which the listener is tunning on the dtabase server : ")
                        if (dataSourceDatabaseListenerPort == None) or (len(dataSourceDatabaseListenerPort) == 0):
                            log.debug('You entered an empty port number. Bypassing asking other details...\n')
                            dataSourceURI = None
                        else:
                            dataSourceURI = dataSourceURI + ':' + dataSourceDatabaseListenerPort

                            dataSourceDatabaseName = raw_input("Enter the name of the data base you want to connect to : ")
                            if (dataSourceDatabaseName == None) or (len(dataSourceDatabaseName) == 0):
                                log.debug('You entered an empty database name. Bypassing asking other details...\n')
                                dataSourceURI = None
                            else:
                                dataSourceURI = dataSourceURI + ':' + dataSourceDatabaseName
                   
                    if (dataSourceUserNodeCount == 0) or (dataSourceUser == None):  
                        dataSourceUser = raw_input("Enter the username with which to connect to the database : ")
                        if (dataSourceUser == None) or (len(dataSourceUser) == 0):
                            log.debug('You entered an empty database user name. Bypassing setting the username in the data source...\n')
                            dataSourceUser = None
    
                    if (dataSourcePasswordNodeCount == 0) or (dataSourcePassword == None):  
                        DoNotRevealPasswordThread = DoNotRevealPassword()
                        DoNotRevealPasswordThread.start()
                        dataSourcePassword = raw_input("Enter the password for the with which to connect to the database : ")
                        DoNotRevealPasswordThread.stopThread()
                        if (dataSourcePassword == None) or (len(dataSourcePassword) == 0):
                            log.debug('You entered an empty database user name. Bypassing setting the password in the data source...\n')
                            dataSourcePassword = None
       
                    if dataSourceURI == None:
                        log.debug('The URI for the data source does not contain all the necessary properties.\n')
                        log.debug('If we target the data source to managed servers/clusters, there will be a problem in brining up the servers.\n')
                        log.debug('The data source needs to be targetted to appropriate servers/clusters at later.\n')
                        dataSourceTargets = None
 
        dataSourceInitialCapacityNodeCount = individualDataSource.getElementsByTagName("InitialCapacity").length

        if dataSourceInitialCapacityNodeCount == 0:
            log.debug('There is no InitialCapacity tag under the parent DataSource tag. Byapssing setting the initial capacity for the data source...\n')
            dataSourceInitialCapacity = None
        else:
            if individualDataSource.getElementsByTagName("InitialCapacity").item(0).childNodes.item(0) != None:    
                dataSourceInitialCapacity = individualDataSource.getElementsByTagName("InitialCapacity").item(0).childNodes.item(0).data
            else:
                log.debug('DataSource InitialCapacity tag is empty. Byapssing setting the initial capacity for the data source...\n')
                dataSourceInitialCapacity = None
  
        dataSourceMaximumCapacityNodeCount = individualDataSource.getElementsByTagName("MaximumCapacity").length

        if dataSourceMaximumCapacityNodeCount == 0:
            log.debug('There is no MaximumCapacity tag under the parent DataSource tag. Byapssing setting the maximum capacity for the data source...\n')
            dataSourceMaximumCapacity = None
        else:
            if individualDataSource.getElementsByTagName("MaximumCapacity").item(0).childNodes.item(0) != None:    
                dataSourceMaximumCapacity = individualDataSource.getElementsByTagName("MaximumCapacity").item(0).childNodes.item(0).data
            else:
                log.debug('DataSource MaximumCapacity tag is empty.. Byapssing setting the maximum capacity for the data source...\n')
                dataSourceMaximumCapacity = None

        dataSourceConnectionCreationRetryFrequencyNodeCount = individualDataSource.getElementsByTagName("ConnectionCreationRetryFrequency").length

        if dataSourceConnectionCreationRetryFrequencyNodeCount == 0:
            log.debug('There is no ConnectionCreationRetryFrequency tag under the parent DataSource tag. Byapssing setting the connection creation retry frequency for the data source...\n')
            dataSourceConnectionCreationRetryFrequency = None
        else:
            if individualDataSource.getElementsByTagName("ConnectionCreationRetryFrequency").item(0).childNodes.item(0) != None:    
                dataSourceConnectionCreationRetryFrequency = individualDataSource.getElementsByTagName("ConnectionCreationRetryFrequency").item(0).childNodes.item(0).data
            else:
                log.debug('DataSource ConnectionCreationRetryFrequency tag is empty.. Byapssing setting the connection creation retry frequency for the data source...\n')
                dataSourceConnectionCreationRetryFrequency = None

        dataSourceCapacityIncrementNodeCount = individualDataSource.getElementsByTagName("CapacityIncrement").length

        if dataSourceMaximumCapacityNodeCount == 0:
            log.debug('There is no CapacityIncrement tag under the parent DataSource tag. Byapssing setting the capacity increment for the data source...\n')
            dataSourceCapacityIncrement = None
        else:
            if individualDataSource.getElementsByTagName("CapacityIncrement").item(0).childNodes.item(0) != None:    
                dataSourceCapacityIncrement = individualDataSource.getElementsByTagName("CapacityIncrement").item(0).childNodes.item(0).data
            else:
                log.debug('DataSource CapacityIncrement tag is empty.. Byapssing setting the capacity increment for the data source...\n')
                dataSourceCapacityIncrement = None
        
        dataSourceRowPrefetchEnabledNodeCount = individualDataSource.getElementsByTagName("RowPrefetchEnabled").length

        if dataSourceRowPrefetchEnabledNodeCount == 0:
            log.debug('There is no RowPrefetchEnabled tag under the parent DataSource tag. Byapssing setting the row prefetch enabled flag for the data source...\n')
            dataSourceRowPrefetchEnabled = None
        else:
            if individualDataSource.getElementsByTagName("RowPrefetchEnabled").item(0).childNodes.item(0) != None:    
                dataSourceRowPrefetchEnabled = individualDataSource.getElementsByTagName("RowPrefetchEnabled").item(0).childNodes.item(0).data
            else:
                log.debug('DataSource RowPrefetchEnabled tag is empty. Byapssing setting the row prefetch enabled flag for the data source...\n')
                dataSourceRowPrefetchEnabled = None

        dataSourceRowPrefetchSizeNodeCount = individualDataSource.getElementsByTagName("RowPrefetchSize").length

        if dataSourceRowPrefetchSizeNodeCount == 0:
            log.debug('There is no RowPrefetchSize tag under the parent DataSource tag. Byapssing setting the row prefetch size for the data source...\n')
            dataSourceRowPrefetchSize = None
        else:
            if individualDataSource.getElementsByTagName("RowPrefetchSize").item(0).childNodes.item(0) != None:    
                dataSourceRowPrefetchSize = individualDataSource.getElementsByTagName("RowPrefetchSize").item(0).childNodes.item(0).data
            else:
                log.debug('DataSource RowPrefetchSize tag is empty. Byapssing setting the row prefetch size for the data source...\n')
                dataSourceRowPrefetchSize = None

        dataSourceStreamChunkSizeNodeCount = individualDataSource.getElementsByTagName("StreamChunkSize").length

        if dataSourceStreamChunkSizeNodeCount == 0:
            log.debug('There is no StreamChunkSize under the parent DataSource tag. Byapssing setting the stream chunk size for the data source...\n')
            dataSourceStreamChunkSize = None
        else:
            if individualDataSource.getElementsByTagName("StreamChunkSize").item(0).childNodes.item(0) != None:    
                dataSourceStreamChunkSize = individualDataSource.getElementsByTagName("StreamChunkSize").item(0).childNodes.item(0).data
            else:
                log.debug('DataSource StreamChunkSize tag is empty. Byapssing setting the stream chunk size for the data source...\n')
                dataSourceStreamChunkSize = None

        setPropertiesForJDBCDataSource(dataSourceName, dataSourceJNDIName, dataSourceURI, dataSourceUser, dataSourcePassword, dataSourceInitialCapacity, dataSourceMaximumCapacity, dataSourceConnectionCreationRetryFrequency, dataSourceCapacityIncrement, dataSourceRowPrefetchEnabled, dataSourceRowPrefetchSize, dataSourceStreamChunkSize)

        if dataSourceTargets != None:
            log.debug('Setting the targets for the dataSource : ' + dataSourceName + ' to : ' + dataSourceTargets + '...\n')

            spaceSeparateddataSourceTargets = str(dataSourceTargets).replace(",", " ")
            spaceSeparateddataSourceTargetsList = spaceSeparateddataSourceTargets.split() 

            for jdbcDataSourceTarget in spaceSeparateddataSourceTargetsList:
                if (str(jdbcDataSourceTarget).find("REPLACE_HOSTNAME") != -1) or (str(jdbcDataSourceTarget).find("REPLACE_MANAGED_SERVER_INDEX") != -1 ):
                    log.debug('Replacing patterns in the JDBC data source targets : ' + jdbcDataSourceTarget + '\n')
                   
                    jdbcDataSourceTarget = str(jdbcDataSourceTarget).replace('REPLACE_HOSTNAME', str(hostName))
           
                    hostSuffixTemp = continuousNumberSequenceAtEndOfStringRegex.search(str(managedServerName))

                    if hostSuffixTemp != None:
                        hostSuffix = hostSuffixTemp.group(1)
                        jdbcDataSourceTarget = str(jdbcDataSourceTarget).replace('REPLACE_MANAGED_SERVER_INDEX', hostSuffix)
                
                setTargetsForDataSource(dataSourceName, jdbcDataSourceTarget)
                save()
        else:
            log.debug('Bypassing setting the targets for the dataSource : ' + dataSourceName + ' since the targets are not specified in the configuration file...\n')

        saveAndActivateChanges()

def readConfigurationFileAndCreateManagedServers(domXMLParser, weblogicAdminUsername, weblogicAdminPassword):
    clusterName = None

    nodeCount = domXMLParser.getElementsByTagName("Node").length

    if nodeCount == 0:
        log.debug('There are no elements of tag Node. Bypassing creating any managed servers and associated JMS resources\n')
        return

    log.debug('There are ' + str(nodeCount) + ' elements of tag Node...\nThe managed servers wand associated resources will be created on the hosts contained in these nodes...\n')

    nodeList = domXMLParser.getElementsByTagName("Node")
    
    for i in range(nodeList.length):
        individualNode = nodeList.item(i);

        hostNamenodeCount = individualNode.getElementsByTagName("Hostname").length

        if hostNamenodeCount == 0:
            log.debug('There is no Hostname tag under the parent Node tag. Aborting...\n')
            discardChanges()
        else:
            if individualNode.getElementsByTagName("Hostname").item(0).childNodes.item(0) != None:    
                hostName = individualNode.getElementsByTagName("Hostname").item(0).childNodes.item(0).data
            else:
                log.debug('Hostname tag is empty. Aborting...\n')
                discardChanges()

        spaceSeparatedHostNames = str(hostName).replace(",", " ")
        spaceSeparatedHostNamesList = spaceSeparatedHostNames.split() 

        log.debug('Processing node with hostnames : ' + hostName + '\n')

        clusterNameNodeCount = individualNode.getElementsByTagName("ClusterName").length

        if clusterNameNodeCount == 0:
            log.debug('There is no ClusterName tag under the parent Node tag. The managed servers will be created as stand alone on host(s) : ' + hostName + '\n')
            clusterName = None
        else:
            if individualNode.getElementsByTagName("ClusterName").item(0).childNodes.item(0) != None:    
                log.debug('ClusterName tag is not empty. Getting the value of ClusterName tag\n')
                clusterName = individualNode.getElementsByTagName("ClusterName").item(0).childNodes.item(0).data
                log.debug('The managed servers on host(s) : ' + hostName + ' will be created as part of cluster : ' + clusterName + '\n')
                createCluster(clusterName)
            else:
                log.debug('ClusterName tag is empty. The managed servers will be created as stand alone on host(s) : ' + hostName + '\n')
                clusterName = None

        numOfManagedServersNodeCount = individualNode.getElementsByTagName("NumOfManagedServers").length

        if numOfManagedServersNodeCount == 0:
            log.debug('There is no NumOfManagedServers tag under the parent Node tag. Aborting...\n')
            discardChanges()
        else:
            if individualNode.getElementsByTagName("NumOfManagedServers").item(0).childNodes.item(0) != None:    
                log.debug('NumOfManagedServers tag is not empty. Getting the value of NumOfManagedServers tag\n')
                numberOfManagedServers = individualNode.getElementsByTagName("NumOfManagedServers").item(0).childNodes.item(0).data
                log.debug(numberOfManagedServers + ' will be created on each host of : ' + hostName + '\n')
            else:
                log.debug('NumOfManagedServers tag is empty. Aborting...\n')
                discardChanges()

        spaceSeparatedNumberOfManagedServer = str(numberOfManagedServers).replace(",", " ")
        spaceSeparatedNumberOfManagedServerList = spaceSeparatedNumberOfManagedServer.split() 

        if (len(spaceSeparatedNumberOfManagedServerList) != 1) and (len(spaceSeparatedNumberOfManagedServerList) != len(spaceSeparatedHostNamesList)):
            log.debug('The value for NumOfManagedServers tag can either be 1 or equal to the number of hosts in the Hostname tag. Aborting...\n')
            discardChanges()

        hostListenAddressForNodeManagerNodeCount = individualNode.getElementsByTagName("HostListenAddressForNodeManager").length

        if hostListenAddressForNodeManagerNodeCount == 0:
            log.debug('There is no HostListenAddressForNodeManager tag under the parent Node tag. The node manager in Weblogic is configured to be listening on all addresses available on that host...\n')
            hostListenAddress = None
        else:
            if individualNode.getElementsByTagName("HostListenAddressForNodeManager").item(0).childNodes.item(0) != None:    
                log.debug('HostListenAddressForNodeManager tag is not empty. The node manager in Weblogic is configured to be listen on a specific address each host...\n')
                hostListenAddress = individualNode.getElementsByTagName("HostListenAddressForNodeManager").item(0).childNodes.item(0).data
            else:
                log.debug('HostListenAddressForNodeManager tag is empty for one of the nodes. The node manager in Weblogic is configured to be listening on all addresses available on that host...\n')
                hostListenAddress = None
             
        sslPortIncrement = None

        for individualHostName,individualNumberOfManagedServers in map(None, spaceSeparatedHostNamesList,spaceSeparatedNumberOfManagedServerList):
            if individualNumberOfManagedServers == None:
                numberOfManagedServers = int(previousNumberOfManagedServers)
            else:
                numberOfManagedServers = int(individualNumberOfManagedServers)


            if (str(individualHostName).find("REPLACE_HOSTNAME") != -1):
                log.debug('Replacing patterns in the host name : ' + individualHostName + '\n')
                   
                individualHostName = str(individualHostName).replace('REPLACE_HOSTNAME', java.net.InetAddress.getLocalHost().getCanonicalHostName())

            hostName = individualHostName
            
            fullyQualifiedHostName = individualHostName

            #From a fully qualified domain name get host name
            hostName = str(hostName).split('.')[0]

            #Initialize a regular expression for getting the last number in a string
            continuousNumberSequenceAtEndOfStringRegex = re.compile('(\d+)$')

            createUnixMachine(hostName, fullyQualifiedHostName, hostListenAddress)

            startListenPortForHostNodeCount = individualNode.getElementsByTagName("StartListenPortForHost").length

            if startListenPortForHostNodeCount == 0:
                log.debug('There is no StartListenPortForHost tag under the parent Node tag. Aborting...\n')
                discardChanges()
            else:
                if individualNode.getElementsByTagName("StartListenPortForHost").item(0).childNodes.item(0) != None:
                    httpListenPort = individualNode.getElementsByTagName("StartListenPortForHost").item(0).childNodes.item(0).data
                else:
                    log.debug('StartListenPortForHost tag is empty for one of the nodes. Aborting...\n')
                    discardChanges()

            httpListenPortIncrementPerHostNodeCount = individualNode.getElementsByTagName("HttpListenPortIncrementPerHost").length

            if httpListenPortIncrementPerHostNodeCount == 0:
                log.debug('There is no HttpListenPortIncrementPerHost tag under the parent Node tag. Defaulting to 2...\n')
                httpListenPortIncrementPerHost = 2
            else:
                if individualNode.getElementsByTagName("HttpListenPortIncrementPerHost").item(0).childNodes.item(0) != None:
                    httpListenPortIncrementPerHost = individualNode.getElementsByTagName("HttpListenPortIncrementPerHost").item(0).childNodes.item(0).data
                else:
                    log.debug('HttpListenPortIncrementPerHost tag is empty for one of the nodes. Defaulting to 2...\n')
                    httpListenPortIncrementPerHost = 2

            sslListenPortIncrementOverHttpPortNodeCount = individualNode.getElementsByTagName("SSLListenPortIncrementOverHttpPort").length

            if sslListenPortIncrementOverHttpPortNodeCount == 0:
                log.debug('There is no SSLListenPortIncrementOverHttpPort tag under the parent Node tag. SSL will not be enabled on the managed servers on these hosts...\n')
                sslListenPortIncrementOverHttpPort = None
            else:
                if individualNode.getElementsByTagName("SSLListenPortIncrementOverHttpPort").item(0).childNodes.item(0) != None:
                    sslListenPortIncrementOverHttpPort = individualNode.getElementsByTagName("SSLListenPortIncrementOverHttpPort").item(0).childNodes.item(0).data
                else:
                    log.debug('SSLListenPortIncrementOverHttpPort tag is empty for one of the nodes. SSL will not be enabled on the managed servers on these hosts...\n')
                    sslListenPortIncrementOverHttpPort = None

            twoWaySSLEnabledNodeCount = individualNode.getElementsByTagName("TwoWaySSLEnabled").length

            if twoWaySSLEnabledNodeCount == 0:
                log.debug('There is no TwoWaySSLEnabled tag under the parent Node tag. Two way SSL will not be enabled on these hosts...\n')
                twoWaySSLEnabled = None
            else:
                if individualNode.getElementsByTagName("TwoWaySSLEnabled").item(0).childNodes.item(0) != None:
                    twoWaySSLEnabled = individualNode.getElementsByTagName("TwoWaySSLEnabled").item(0).childNodes.item(0).data
                else:
                    log.debug('There is no TwoWaySSLEnabled tag under the parent Node tag. Two way SSL will not be enabled on these hosts...\n')
                    twoWaySSLEnabled = None
            nonSSLDisabledNodeCount = individualNode.getElementsByTagName("NonSSLDisabled").length

            if nonSSLDisabledNodeCount == 0:
                log.debug('There is no nonSSLDisabled tag under the parent Node tag. Non SSL port will not be disabled on these hosts...\n')
                nonSSLDisabled = None
            else:
                if individualNode.getElementsByTagName("NonSSLDisabled").item(0).childNodes.item(0) != None:
                    nonSSLDisabled = individualNode.getElementsByTagName("NonSSLDisabled").item(0).childNodes.item(0).data
                else:
                    log.debug('There is no nonSSLDisbled tag under the parent Node tag. Two way SSL will not be enabled on these hosts...\n')
                    nonSSLDisabled = None

            managedServerListenAddressNodeCount = individualNode.getElementsByTagName("ManagedServerListenAddress").length

            if managedServerListenAddressNodeCount == 0:
                log.debug('There is no ManagedServerListenAddress tag under the parent Node tag. The listen address will be empty for the managed servers on this host...\n')
                managedServerListenAddress = None
            else:
                if individualNode.getElementsByTagName("ManagedServerListenAddress").item(0).childNodes.item(0) != None:
                    managedServerListenAddress = individualNode.getElementsByTagName("ManagedServerListenAddress").item(0).childNodes.item(0).data
                    
                    if (str(managedServerListenAddress).find("REPLACE_HOSTNAME") != -1) or (str(managedServerListenAddress).find("REPLACE_IP_ADDRESS") != -1 ):
                        log.debug('The listen address for the managed server on this host is of the pattern : ' + managedServerListenAddress + '\n')

                        log.debug('Replacing hostname or the IP address...\n')

                        log.debug('Getting the IP address of machine : ' + fullyQualifiedHostName + '\n')
                        listenAddressReplaced = java.net.InetAddress.getByName(fullyQualifiedHostName).getHostAddress()
                        
                        managedServerListenAddress = str(managedServerListenAddress).replace('REPLACE_HOSTNAME', hostName)
                        managedServerListenAddress = str(managedServerListenAddress).replace('REPLACE_IP_ADDRESS', listenAddressReplaced)
        
                else:
                    log.debug('There is no ManagedServerListenAddress tag under the parent Node tag. The listen address will be empty for the managed servers on this host\n')
                    managedServerListenAddress = None

            logFileLocationNodeCount = individualNode.getElementsByTagName("LogFileLocation").length

            if logFileLocationNodeCount == 0:
                log.debug('There is no LogFileLocation tag under the parent Node tag. The log file location will be set to default...\n')
                logFileLocation = None
            else:
                if individualNode.getElementsByTagName("LogFileLocation").item(0).childNodes.item(0) != None:
                    logFileLocation = individualNode.getElementsByTagName("LogFileLocation").item(0).childNodes.item(0).data
                else:
                    log.debug('There is no LogFileLocation tag under the parent Node tag. The log file location will be set to default...\n')
                    logFileLocation = None

            log.debug('Trying to create ' + str(numberOfManagedServers) + ' managed servers and associated resources on host ' + str(individualHostName) + '\n')

            log.debug('The listen port for the managed servers on this host will start from port : ' + httpListenPort + '\n')

            if sslListenPortIncrementOverHttpPort != None:
                log.debug('The SSL listen port for the managed servers on this host will start from port : ' + str(int(httpListenPort) + int(sslListenPortIncrementOverHttpPort)) + '\n')

            for j in range(1, int(numberOfManagedServers)+1): 
                managedServerNameNodeCount = individualNode.getElementsByTagName("ManagedServerName").length

                if managedServerNameNodeCount == 0:
                    log.debug('There is no ManagedServerName tag under the parent Node tag. Aborting...\n')
                    discardChanges()
                else:
                    if individualNode.getElementsByTagName("ManagedServerName").item(0).childNodes.item(0) != None:    
                        managedServerName = individualNode.getElementsByTagName("ManagedServerName").item(0).childNodes.item(0).data
                    else:
                        log.debug('ManagedServerName tag is empty for under the parent Node tag. Aborting...\n')
                        discardChanges()

                if (str(managedServerName).find("REPLACE_HOSTNAME") != -1) or (str(managedServerName).find("REPLACE_MANAGED_SERVER_INDEX") != -1 ):
                    log.debug('The managed server name is of the pattern : ' + managedServerName + '\n')

                    log.debug('Replacing hostname and/or managed server index...\n')

                    managedServerName = str(managedServerName).replace('REPLACE_HOSTNAME', hostName)
                    managedServerName = str(managedServerName).replace('REPLACE_MANAGED_SERVER_INDEX', str(j))
        
                #Create managed servers on the respective machines
                log.info('Creating managed server : ' + str(managedServerName) + ' on host : ' + hostName + '\n')
                createManagedServer(str(managedServerName))
 
                if clusterName != None:

                    clusterChannelNameNodeCount = individualNode.getElementsByTagName("ClusterChannelName").length

                    if clusterChannelNameNodeCount == 0:
                        log.debug('There is no ClusterChannelName tag under the parent Node tag. Bypassing creating any network access points for the managed servers in the cluster...\n')
                    else:
                        log.debug('ClusterName is not empty for the current node. Reading the value for ClusterChannelName from the configuration file for this node\n')

                        if individualNode.getElementsByTagName("ClusterChannelName").item(0).childNodes.item(0) != None:    
                            clusterChannelName = individualNode.getElementsByTagName("ClusterChannelName").item(0).childNodes.item(0).data
        
                            #Create network access point for the managed server
                            log.info('Creating network access point : ' + str(clusterChannelName) + ' for server : ' + str(managedServerName) + '\n')
                            createNetworkAccessPoint(str(managedServerName), clusterChannelName)

                            #Set the properties for the network access point for the managed server
                            log.debug('Setting the properties for network access point : ' + str(clusterChannelName) + ' for server : ' + str(managedServerName) + '\n')
                            setAttributesForClusterChannelForManagedServer(str(managedServerName), clusterChannelName, str(httpListenPort), hostName)

                            log.debug('Assigning the cluster channel : ' + clusterChannelName + ' to cluster : ' + clusterName + '\n')
                            setAttributesForCluster(clusterName, clusterChannelName)
                        else:
                            log.debug('ClusterChannelName tag is empty under the parent Node tag. Bypassing creating any network access points for the managed servers in the cluster...\n')
                else:
                    log.debug('Bypassing reading the value for ClusterChannelName from the configuration file for this node since the ClusterName is empty for this node\n')
                
                if clusterName != None:
                    #Assign the managed server to the cluster
                    log.info('Creating managed server : ' + str(managedServerName) + ' to cluster : ' + clusterName + '\n')
                    assignServerToCluster(str(managedServerName), clusterName)
                    #Set the attributes for default migratable target for the managed server
                    log.debug('Setting the attributes for JTA migratable target for the managed server : ' + str(managedServerName) + '\n')
                    setAttributesForJTAMigratableTarget(str(managedServerName), clusterName)

                    #Set the attributes for default migratable target for the managed server
                    log.debug('Setting the attributes for default migratable target for the managed server : ' + str(managedServerName) + '\n')
                    setAttributesForDefaultMigratableTarget(str(managedServerName), clusterName)
                else:
                    log.debug('Bypassing assigning managed server : ' + str(managedServerName) + ' to cluster since cluster name is empty for current node...\n')

                #Assign the managed server to the respective machine
                log.info('Assigning managed server : ' + str(managedServerName) + ' to host : ' + hostName + '\n')
                assignServerToMachine(str(managedServerName), hostName)

                #Set the HTTP configuration for the managed server
                log.debug('Setting the HTTP configuration for managed server : ' + str(managedServerName) + '\n')
                setHttpConfigurationForServer(str(managedServerName), str(httpListenPort), managedServerListenAddress)

                sslListenPort = 0
                #Set the SSL configuration for the managed server
                if sslListenPortIncrementOverHttpPort != None:
                    log.info('Setting the SSL configuration for managed server : ' + str(managedServerName) + '\n')
                    sslListenPort = int(httpListenPort) + int(sslListenPortIncrementOverHttpPort)
                    setSSLConfigurationForServer(str(managedServerName), str(sslListenPort), "true", twoWaySSLEnabled, nonSSLDisabled)

                #Set the log file configuration for the managed server
                if logFileLocation != None:
                    log.debug('Setting the log file configuration for managed server : ' + str(managedServerName) + '\n')
                    setLoggingPropertiesForServer(str(managedServerName), logFileLocation, 14)
                else:
                    log.debug('Bypassing changing the log file configuration for managed server : ' + str(managedServerName) + '\n')

                #Set the log file configuration for the managed server
                if logFileLocation != None:
                    log.debug('Setting the log file configuration for web server on the managed server : ' + str(managedServerName) + '\n')
                    setLoggingPropertiesForWebServer(str(managedServerName), logFileLocation, 14)
                else:
                    log.debug('Bypassing changing the log file configuration for the web server on managed server : ' + str(managedServerName) + '\n')

                serverStartArgumentsNodeCount = individualNode.getElementsByTagName("ServerStartArguments").length

                if serverStartArgumentsNodeCount == 0:
                    log.debug('There is no ServerStartArguments tag under the parent Node tag. The managed servers on each host will have no custom server start arguments...\n')
                    serverStartArguments = None
                else:
                    if individualNode.getElementsByTagName("ServerStartArguments").item(0).childNodes.item(0) != None:    
                        serverStartArguments = individualNode.getElementsByTagName("ServerStartArguments").item(0).childNodes.item(0)
                    else:
                        log.debug('The ServerStartArguments tag under the parent Node tag is empty. The managed servers on each host will have no custom server start arguments...\n')
                        serverStartArguments = None
    
                javaHomeNodeCount = individualNode.getElementsByTagName("JavaHome").length

                if javaHomeNodeCount == 0:
                    log.debug('There is no JavaHome tag under the parent ServerStartArguments tag. Will not set the Java Home for the managed servers...\n')
                    javaHome = None
                else:
                    if individualNode.getElementsByTagName("JavaHome").item(0).childNodes.item(0) != None:    
                        javaHome = individualNode.getElementsByTagName("JavaHome").item(0).childNodes.item(0).data
                    else:
                        log.debug('There is no JavaHome tag under the parent ServerStartArguments tag. Will not set the Java Home for the managed servers...\n')
                        javaHome = None
                
                javaVendorNodeCount = individualNode.getElementsByTagName("JavaVendor").length

                if javaVendorNodeCount == 0:
                    log.debug('There is no JavaVendor tag under the parent ServerStartArguments tag. Will not set the Java Vendor for the managed servers...\n')
                    javaVendor = None
                else:
                    if individualNode.getElementsByTagName("JavaVendor").item(0).childNodes.item(0) != None:    
                        javaVendor = individualNode.getElementsByTagName("JavaVendor").item(0).childNodes.item(0).data
                    else:
                        log.debug('There is no JavaVendor tag under the parent ServerStartArguments tag. Will not set the Java Vendor for the managed servers...\n')
                        javaVendor = None

                beaHomeNodeCount = individualNode.getElementsByTagName("BEAHome").length

                if beaHomeNodeCount == 0:
                    log.debug('There is no BEAHome tag under the parent ServerStartArguments tag. Will not set the BEA Home for the managed servers...\n')
                    beaHome = None
                else:
                    if individualNode.getElementsByTagName("BEAHome").item(0).childNodes.item(0) != None:    
                        beaHome = individualNode.getElementsByTagName("BEAHome").item(0).childNodes.item(0).data
                    else:
                        log.debug('There is no BEAHome tag under the parent ServerStartArguments tag. Will not set the BEA Home for the managed servers...\n')
                        beaHome = None

                rootDirectoryNodeCount = individualNode.getElementsByTagName("RootDirectory").length

                if rootDirectoryNodeCount == 0:
                    log.debug('There is no RootDirectory tag under the parent ServerStartArguments tag. Will not set the RootDirectory for the managed servers...\n')
                    rootDirectory = None
                else:
                    if individualNode.getElementsByTagName("RootDirectory").item(0).childNodes.item(0) != None:    
                        rootDirectory = individualNode.getElementsByTagName("RootDirectory").item(0).childNodes.item(0).data
                    else:
                        log.debug('There is no RootDirectory tag under the parent ServerStartArguments tag. Will not set the Root Directory for the managed servers...\n')
                        rootDirectory = None

                classpathNodeCount = individualNode.getElementsByTagName("ClassPath").length

                if classpathNodeCount == 0:
                    log.debug('There is no Classpath tag under the parent ServerStartArguments tag. Will not set the Classpath for the managed servers...\n')
                    classpath = None
                else:
                    if individualNode.getElementsByTagName("Classpath").item(0).childNodes.item(0) != None:    
                        classpath = individualNode.getElementsByTagName("Classpath").item(0).childNodes.item(0).data
                    else:
                        log.debug('There is no Classpath tag under the parent ServerStartArguments tag. Will not set Classpath for the managed servers...\n')
                        classpath = None

                argumentsNodeCount = individualNode.getElementsByTagName("Arguments").length

                if argumentsNodeCount == 0:
                    log.debug('There is no Arguments tag under the parent ServerStartArguments tag. Will not set any arguments for the managed servers...\n')
                    arguments = None
                else:
                    if individualNode.getElementsByTagName("Arguments").item(0).childNodes.item(0) != None:    
                        arguments = individualNode.getElementsByTagName("Arguments").item(0).childNodes.item(0).data
                    else:
                        log.debug('There is no Arguments tag under the parent ServerStartArguments tag. Will not set any arguments for the managed servers...\n')
                        classpath = None

                log.info('Setting the server start configuration for managed server : ' + str(managedServerName) + '\n')
                #setServerStartArguments(str(managedServerName), javaHome, javaVendor, beaHome, rootDirectory, classpath, weblogicAdminUsername, weblogicAdminPassword, arguments)
		setServerStartArguments(str(managedServerName), javaHome, javaVendor, beaHome, rootDirectory, classpath, weblogicAdminUsername, weblogicAdminPassword, arguments, hostName)

                
                readConfigurationFileAndCreateJMSServers(individualNode, managedServerName, hostName, str(j))

                readConfigurationFileAndCreateJMSModules(individualNode, managedServerName, hostName, str(j))

                readConfigurationFileAndCreateJDBCDataSources(individualNode, managedServerName, hostName, str(j))

                httpListenPort = int(httpListenPort) + int(httpListenPortIncrementPerHost)

                if sslListenPortIncrementOverHttpPort != None:
                    sslListenPort = int(httpListenPort) + int(sslListenPortIncrementOverHttpPort)
            
                previousNumberOfManagedServers = int(numberOfManagedServers)

        
####MAIN STARTS HERE#########
def __createDomain(doc):
    documentBuilderFactoryInstance = DocumentBuilderFactory.newInstance()
    documnetBuilderFactory = documentBuilderFactoryInstance.newDocumentBuilder()
    #domXMLParser = documnetBuilderFactory.parse("" + sys.argv[1])
    #domXMLParser = documnetBuilderFactory.parse("" + xmlTemplate)
    #domXMLParser = documnetBuilderFactory.parse("" + doc)
    domXMLParser = doc
    #templatePops =  'domainTemplate.xml'
    #domXMLParser.writexml(open(templatePops, 'w'))
    #domXMLParser = doc
    
    if checkIfTagIsEmpty(domXMLParser, "OracleHome") == 0:
        log.debug('OracleHome tag is empty in the configuration file\n')
        exit(exitcode = -1)
    
    oracleHome = getTagValue(domXMLParser, "OracleHome")

    if checkIfTagIsEmpty(domXMLParser, "DomainName") == 0:
        log.debug('DomainName tag is empty in the configuration file\n')
        exit(exitcode = -1)

    domainNameFromConfigurationFile = getTagValue(domXMLParser, "DomainName")
    log.debug(domainNameFromConfigurationFile)

    if checkIfTagIsEmpty(domXMLParser, "DomainHome") == 0:
        log.debug('DomainName tag is empty in the configuration file\n')
        exit(exitcode = -1)
    
    domainHomeFromConfigurationFile = getTagValue(domXMLParser, "DomainHome")
    log.debug(domainHomeFromConfigurationFile)
    
    if checkIfTagIsEmpty(domXMLParser, "ClearTextCredentialAccessEnabled") == 0:
        log.debug('ClearTextCredentialAccessEnabled tag is empty in the configuration file\n')
    
    clearTextCredentialAccessEnabledFromConfigurationFile = getTagValue(domXMLParser, "ClearTextCredentialAccessEnabled")

    if checkIfTagIsEmpty(domXMLParser, "WeblogicAdminUsername") == 0:
        log.debug('WeblogicAdminUsername tag is empty in the configuration file.  Prompting the user for entering username\n')
    
        weblogicAdminUsername = raw_input("Enter the Weblogic Administration Username : ")
        if (weblogicAdminUsername == None) or (len(weblogicAdminUsername) == 0):
            log.debug('You entered an empty username. Aborting...\n')
            exit(exitcode = -1)
    else:
        weblogicAdminUsername = getTagValue(domXMLParser, "WeblogicAdminUsername")

    if checkIfTagIsEmpty(domXMLParser, "WeblogicAdminPassword") == 0:
        log.debug('WeblogicAdminPassword tag is empty in the configuration file. Prompting the user for entering password\n')

        DoNotRevealPasswordThread = DoNotRevealPassword()
        DoNotRevealPasswordThread.start()
        weblogicAdminPassword = raw_input("Enter the Weblogic Administration Password : ")
        DoNotRevealPasswordThread.stopThread()
    
        if (weblogicAdminPassword == None) or (len(weblogicAdminPassword) == 0):
            log.debug('You entered an empty password. Aborting...\n')
            exit(exitcode = -1)
    else:
        weblogicAdminPassword = getTagValue(domXMLParser, "WeblogicAdminPassword")

    if checkIfTagIsEmpty(domXMLParser, "Name") == 0:
        log.debug('adminServerName tag is empty in the configuration file\n')
        exit(exitcode = -1)
    else:
        adminServerName = getTagValue(domXMLParser, "Name")

    if checkIfTagIsEmpty(domXMLParser, "ListenPort") == 0:
        log.info('ListenPort tag is empty in the configuration file')
        log.info('Defaulting to HTTP ListenPort value of : 7001 for the Weblogic Admin Server\n')
        adminServerListenPort = 7001
    else:
        adminServerListenPort = getTagValue(domXMLParser, "ListenPort")

    if checkIfTagIsEmpty(domXMLParser, "SSLListenPort") == 0:
        log.debug('SSLListenPort tag is empty in the configuration file\n')
        adminServerSSLListenPort = None
    else:
        adminServerSSLListenPort = getTagValue(domXMLParser, "SSLListenPort")

    if checkIfTagIsEmpty(domXMLParser, "ServerStartArguments") == 0:
        log.debug('ServerStartArguments tag is empty in the configuration file\n')
        adminServerStartArguments = None
    else:
        adminServerStartArguments = getTagValue(domXMLParser, "ServerStartArguments")
    
    if checkIfTagIsEmpty(domXMLParser, "HostName") == 0:
        log.debug('HostName tag is empty for the Weblogic Admin Server in the configuration file\n')
        adminServerHostName = None
    else:
        adminServerHostName = getTagValue(domXMLParser, "HostName")

    if adminServerHostName != None:
        spaceSeparatedAdminServerHostName = str(adminServerHostName).replace(",", " ")
        spaceSeparatedAdminServerHostNameList = spaceSeparatedAdminServerHostName.split() 

        if spaceSeparatedAdminServerHostNameList[0] == "localhost":
            adminServerListenAddress = java.net.InetAddress.getLocalHost().getHostAddress()
        else:
            adminServerListenAddress = java.net.InetAddress.getByName(spaceSeparatedAdminServerHostNameList[0]).getHostAddress()
    else:
        adminServerListenAddress = java.net.InetAddress.getLocalHost().getHostAddress()

    createDomainAndStartAdminServer(oracleHome, domainNameFromConfigurationFile, domainHomeFromConfigurationFile, weblogicAdminUsername, weblogicAdminPassword, adminServerName, adminServerListenAddress, adminServerListenPort, adminServerStartArguments)
    
    if (adminServerListenAddress == java.net.InetAddress.getLocalHost().getHostAddress()) and (existingDomainFlag == 0):
        setAdminServerListenAddressConfiguration(adminServerName,adminServerListenAddress, domainNameFromConfigurationFile, clearTextCredentialAccessEnabledFromConfigurationFile, adminServerStartArguments)
        setAdminServerSSLConfiguration(adminServerName, adminServerSSLListenPort)
    
    readConfigurationFileAndCreateManagedServers(domXMLParser, weblogicAdminUsername, weblogicAdminPassword)
    
    shutdownAdminServer(adminServerName)
    
    disconnect()

    #exit()

def getKeyPassphrase(passPhraseType):
    adminHostname='STAGE2CPP124'
    domainServ='pegacspserv'
    key.authCode.password="tKgXSMiHQNu1HcxyuApw"
    PROTECTED_READER="/x/web/"+adminHostname+"/"+domainServ+"/protectedreader"
    PROTECTED_PROPS_FILE="/x/web/"+adminHostname+"/"+domainServ+"/protected/"+domainServ+"_protected.cfg"
    
    PLAIN_TEXT_KEYS_TO_BE_DECRYPTED_VALUE="encrypted_keystore_passphrase,encrypted_weblogic_keystore_passphrase"
    BASE64_KEYS_TO_BE_DECRYPTED_VALUE="encrypted_auth_key"
    
    os.environ["AUTHCODE"] = "tKgXSMiHQNu1HcxyuApw"
    RETURN_VALUE_CMD = PROTECTED_READER+" "+domainServ+" "+PROTECTED_PROPS_FILE+" "+PLAIN_TEXT_KEYS_TO_BE_DECRYPTED_VALUE+" "+BASE64_KEYS_TO_BE_DECRYPTED_VALUE
    RETURN_VALUE_OUT = os.popen(RETURN_VALUE_CMD).read()
    
    AS_PASSPHRASE_CMD = "return_value=\""+RETURN_VALUE_OUT+"\" ; echo $return_value | sed \"s/^.*encrypted_weblogic_keystore_passphrase=//;s/^[[:space:]]*//;s/[[:space:]].*$//\""
    MS_PASSPHRASE_CMD = "return_value=\""+RETURN_VALUE_OUT+"\" ; echo $return_value | sed \"s/^.*encrypted_keystore_passphrase=//;s/^[[:space:]]*//;s/[[:space:]].*$//\""
    
    AS_PASSPHRASE_OUT = os.popen(AS_PASSPHRASE_CMD).read()
    MS_PASSPHRASE_OUT = os.popen(MS_PASSPHRASE_CMD).read()
    
    print AS_PASSPHRASE_OUT.strip()
    print MS_PASSPHRASE_OUT.strip()
    
    if passPhraseType == "AS":
        return AS_PASSPHRASE_OUT.strip()
    elif passPhraseType == "MS":
        return MS_PASSPHRASE_OUT.strip()
    else:
        return str('false')