import common.assertions as assertions
import common.logredirect as logredirect
import os, socket, sys

from java.io import File
from xml.dom import minidom
  
doc = minidom.Document()

def run(cfg):
    #"""Create WebLogic Domain Templates"""
    assertions.sanityCheckDomainConfig(cfg)
    arg2 = sys.argv[3]
    templatePops='c:/x/'+arg2+'.xml'
    c=create_xml(cfg, templatePops)
    return c
    
def create_xml(configProperties, templatePops):
	domain_name=configProperties.getProperty('wls.domain.name')
	OracleBase=configProperties.getProperty('wls.oracle.base')
	JavaHome=configProperties.getProperty('wls.domain.javahome')
	OracleHome=configProperties.getProperty('wls.oracle.home')

	###Add Domain Element
	Domain_Tag = doc.createElement('Domain')
	addDomainElement(configProperties, Domain_Tag)
#	servers=configProperties.getProperty('wls.servers')
	createMSTag(configProperties, Domain_Tag)
	doc.writexml( open(templatePops, 'w'))
	return templatePops
    


######################
######################
######################
def createMSTag(configProperties, Domain_Tag):
	domain_name=configProperties.getProperty('wls.domain.name')
	servers=configProperties.getProperty('wls.servers')
	if not servers is None and len(servers)>0:
		ManagedServers_Tag = doc.createElement('ManagedServers')
		createXMLChild(Domain_Tag, ManagedServers_Tag)
		serverList = servers.split(',')
		for svr in serverList:
			addJvmElement(configProperties, svr, ManagedServers_Tag)

        
def createDomainTag(configProperties, domainName, WeblogicAdminUsername, WeblogicAdminPassword):
    OracleHome=configProperties.getProperty('wls.oracle.home')
    AdminServer_DomainHome=configProperties.getProperty('wls.domain.dir')
    Domain_Tag_dict = {'OracleHome':OracleHome, 
                       'DomainName':domainName, 
                       'DomainHome':AdminServer_DomainHome, 
                       'WeblogicAdminUsername':WeblogicAdminUsername, 
                       'WeblogicAdminPassword':WeblogicAdminPassword, 
                       'ClearTextCredentialAccessEnabled':'true'}
    return Domain_Tag_dict
    
def createAdminServerTag(configProperties, ListenPort):
    AdminServerName = configProperties.getProperty('wls.admin.name')
    SSLListenPortIncrementOverHttpPort = configProperties.getProperty('wls.admin.SSLListenPortIncrementOverHttpPort')
    SSLListenPort = int(ListenPort)+int(SSLListenPortIncrementOverHttpPort)
    AdminServer_StartArguments = configProperties.getProperty('wls.admin.vmarguments')
    hostname_fqdn = socket.getfqdn()
    ip_address=socket.gethostbyname(hostname_fqdn)
    ServerHostName = configProperties.getProperty('wls.admin.Hostname')
    #ServerHostName = configProperties.getProperty('wls.admin.listener.address')
    #ServerHostName=hostname_fqdn
    AdminServer_Tag_dict = {'Name':AdminServerName, 
                            'HostName':ServerHostName, 
                            'ListenPort':ListenPort, 
                            'SSLListenPort':SSLListenPort, 
                            'ServerStartArguments':AdminServer_StartArguments
                            }
    return AdminServer_Tag_dict

    
def createNodeTag(ms_ServerHostName, ip_address, StartListenPortForHost, ManagedServer_HttpListenPortIncrementPerHost, ManagedServer_SSLListenPortIncrementOverHttpPort, ManagedServer_TwoWaySSLEnabled, NumOfManagedServers, std_ManagedServerName, ManagedServer_LogLocation, ClusterName, ClusterChannelName):
    #print('Inside Node')

	#print ms_ServerHostName, ip_address, StartListenPortForHost, ManagedServer_HttpListenPortIncrementPerHost, ManagedServer_SSLListenPortIncrementOverHttpPort, ManagedServer_TwoWaySSLEnabled, NumOfManagedServers, std_ManagedServerName, ManagedServer_LogLocation, ClusterName, ClusterChannelName  

	Node_Tag_dict = {
					 'Hostname':ms_ServerHostName, 
					 'HostListenAddressForNodeManager':ip_address, 
					 'StartListenPortForHost':StartListenPortForHost, 
					 'HttpListenPortIncrementPerHost':int(ManagedServer_HttpListenPortIncrementPerHost), 
					 'SSLListenPortIncrementOverHttpPort':ManagedServer_SSLListenPortIncrementOverHttpPort, 
					 'TwoWaySSLEnabled':ManagedServer_TwoWaySSLEnabled,
					 'NumOfManagedServers':NumOfManagedServers, 
					 'ManagedServerName':std_ManagedServerName, 
					 'ManagedServerListenAddress':'REPLACE_IP_ADDRESS', 
					 'LogFileLocation':ManagedServer_LogLocation
					 }
	if not ClusterName is None and len(ClusterName)>0:
		Node_Tag_dict['ClusterName'] = ClusterName


	if not ClusterChannelName is None and len(ClusterChannelName)>0:
		Node_Tag_dict['ClusterChannelName'] = ClusterChannelName

			
	return Node_Tag_dict
    

def createServerStartArguments_Tag_dict(JavaHome, OracleHome, ManagedServer_Classpath, Arguments):
    #RootDirectory=''
    ServerStartArguments_Tag_dict = {
                                     'JavaHome':JavaHome, 
                                     'JavaVendor':'Oracle', 
                                     'BEAHome':OracleHome, 
                                     'Classpath':ManagedServer_Classpath,
                                     'Arguments':Arguments
                                     }
    return ServerStartArguments_Tag_dict    

def createDataSource_Tag_dict(dsName, dbUser, dbPassword, JNDIName, dbConnectionURL, dbTarget, InitialCapacity, MaximumCapacity, CapacityIncrement, ConnectionCreationRetryFrequency):
    DataSource_Tag_dict = {
                            'Name':dsName, 
                            'JNDIName':JNDIName, 
                            'User':dbUser,
                            'URI':dbConnectionURL, 
                            'Password':dbPassword, 
                            'Targets':dbTarget, 
                            'InitialCapacity':InitialCapacity, 
                            'MaximumCapacity':MaximumCapacity, 
                            'CapacityIncrement':CapacityIncrement, 
                            'ConnectionCreationRetryFrequency':ConnectionCreationRetryFrequency
                           }
                           
    return DataSource_Tag_dict    

    
def createJMSServers_Tag_dict(jmsServerName):
    
    JMSServers_Tag_dict = {
                           'Name':jmsServerName
                           }
    return JMSServers_Tag_dict
    
def createJMSModules_Tag_dict(jmsModuleName, jmsModuleTarget):
    #print
    JMSModules_Tag_dict = {
                          'Name':jmsModuleName,
                          'Targets':jmsModuleTarget
                          }
    return JMSModules_Tag_dict
    
def createSubDeployment_Tag_dict(SubDeploymentName, SubDeploymentTarget):
    SubDeployment_Tag_dict = {
                              'Name':SubDeploymentName,
                              'Targets':SubDeploymentTarget
                              }
    return SubDeployment_Tag_dict
    
def createConnectionFactory_Tag_dict(ConnectionFactoryName, ConnectionFactoryJNDIName, CF_SubDeploymentName):
    #ConnectionFactoryName = ConnectionFactoryName+'_REPLACE_MACHINE_SUFFIX_REPLACE_MANAGED_SERVER_INDEX'
    ConnectionFactory_Tag_dict = {
                                  'Name':ConnectionFactoryName,
                                  'JNDIName':ConnectionFactoryJNDIName,
                                  'DefaultDeliveryMode':'Non-Persistent',
                                  'AttachJMXUserID':'false',
                                  'SubDeploymentName':CF_SubDeploymentName
                                  }
    return ConnectionFactory_Tag_dict


def createTopic_Tag_dict(TopicType, TopicName, TopicJNDIName, Topic_SubDeploymentName, Topic_LoadBalancingPolicy=None, Topic_ReDeliveryDelay=None, Topic_ReDeliveryLimit=None, Topic_MaximumMessageSize=None):
    #TopicName = TopicName+'_REPLACE_MACHINE_SUFFIX_REPLACE_MANAGED_SERVER_INDEX'
	Topic_Tag_dict = {
					  'Type':TopicType,
					  'Name':TopicName,
					  'JNDIName':TopicJNDIName,
					  'SubDeploymentName':Topic_SubDeploymentName
					  }
					  
	if not Topic_ReDeliveryDelay is None and len(Topic_ReDeliveryDelay)>0:
		Topic_Tag_dict['ReDeliveryDelay'] = Topic_ReDeliveryDelay
	else:
		Topic_Tag_dict['ReDeliveryDelay'] = -1

	if not Topic_ReDeliveryLimit is None and len(Topic_ReDeliveryLimit)>0:
		Topic_Tag_dict['ReDeliveryLimit'] = Topic_ReDeliveryLimit
	else:
		Topic_Tag_dict['ReDeliveryLimit'] = -1
		
	if not Topic_LoadBalancingPolicy is None and len(Topic_LoadBalancingPolicy)>0:
		Topic_Tag_dict['LoadBalancingPolicy'] = Topic_LoadBalancingPolicy
	else:
		Topic_Tag_dict['LoadBalancingPolicy'] = 'Round-Robin'

	if not Topic_MaximumMessageSize is None and len(Topic_MaximumMessageSize)>0:
		Topic_Tag_dict['MaximumMessageSize'] = Topic_MaximumMessageSize
	else:
		Topic_Tag_dict['MaximumMessageSize'] = 2147483647
		
	return Topic_Tag_dict
	
def createQueue_Tag_dict(QueueType, QueueName, QueueJNDIName, Queue_SubDeploymentName, Queue_ExpirationPolicy=None, Queue_ForwardDelay=None, Queue_TimeToLive=None, Queue_LoadBalancingPolicy=None, Queue_ReDeliveryDelay=None, Queue_ReDeliveryLimit=None, Queue_MaximumMessageSize=None, Queue_ErrorDestination=None):
    #QueueName = QueueName+'_REPLACE_MACHINE_SUFFIX_REPLACE_MANAGED_SERVER_INDEX'
	Queue_Tag_dict = {
					  'Type':QueueType,
					  'Name':QueueName,
					  'JNDIName':QueueJNDIName,
					  'SubDeploymentName':Queue_SubDeploymentName
					  }
					  
	if not Queue_ReDeliveryDelay is None and len(Queue_ReDeliveryDelay)>0:
		Queue_Tag_dict['ReDeliveryDelay'] = Queue_ReDeliveryDelay
	else:
		Queue_Tag_dict['ReDeliveryDelay'] = -1

	if not Queue_ReDeliveryLimit is None and len(Queue_ReDeliveryLimit)>0:
		Queue_Tag_dict['ReDeliveryLimit'] = Queue_ReDeliveryLimit
	else:
		Queue_Tag_dict['ReDeliveryLimit'] = -1
		
	if not Queue_LoadBalancingPolicy is None and len(Queue_LoadBalancingPolicy)>0:
		Queue_Tag_dict['LoadBalancingPolicy'] = Queue_LoadBalancingPolicy
	else:
		Queue_Tag_dict['LoadBalancingPolicy'] = 'Round-Robin'

	if not Queue_TimeToLive is None and len(Queue_TimeToLive)>0:
		Queue_Tag_dict['TimeToLive'] = Queue_TimeToLive
	else:
		Queue_Tag_dict['TimeToLive'] = -1

	if not Queue_MaximumMessageSize is None and len(Queue_MaximumMessageSize)>0:
		Queue_Tag_dict['MaximumMessageSize'] = Queue_MaximumMessageSize
	else:
		Queue_Tag_dict['MaximumMessageSize'] = 2147483647

	if not Queue_ForwardDelay is None and len(Queue_ForwardDelay)>0:
		Queue_Tag_dict['ForwardDelay'] = Queue_ForwardDelay
	else:
		Queue_Tag_dict['ForwardDelay'] = -1
		
	if not Queue_ExpirationPolicy is None and len(Queue_ExpirationPolicy)>0:
		Queue_Tag_dict['ExpirationPolicy'] = Queue_ExpirationPolicy
	else:
		Queue_Tag_dict['ExpirationPolicy'] = 'Discard'

	if not Queue_ErrorDestination is None and len(Queue_ErrorDestination)>0:
		Queue_Tag_dict['ErrorDestination'] = Queue_ErrorDestination
		
	return Queue_Tag_dict

def createXMLElement(tagName, tagValues, r):
    tn = doc.createElement(str(tagName))
    tv = doc.createTextNode(tagValues.strip())
    tn.appendChild(tv)
    r.appendChild(tn)

def createXMLChild(parrentTagName, childTagName, tagDict={}):
    parrentTagName.appendChild(childTagName)
    for k,v in tagDict.items():
        createXMLElement(k, str(v), childTagName)
        

def addDomainElement(configProperties, domain_node):
    domain_name=configProperties.getProperty('wls.domain.name')
    adminUser = configProperties.getProperty('wls.admin.username')
    adminPassword = configProperties.getProperty('wls.admin.password')
    #Domain_Tag = doc.createElement('Domain')
    Domain_Tag_dict = createDomainTag(configProperties, domain_name, adminUser, adminPassword)
    createXMLChild(doc, domain_node, Domain_Tag_dict)
    addAdminServerElement(configProperties, domain_node)
    
def addAdminServerElement(configProperties, domain_node):
    adminListenPort = configProperties.getProperty('wls.admin.Port')
    AdminServer_Tag = doc.createElement('AdminServer')
    AdminServer_Tag_dict = createAdminServerTag(configProperties, adminListenPort)
    createXMLChild(domain_node, AdminServer_Tag, AdminServer_Tag_dict)
        
def addJvmElement(configProperties, server, msTag):

	hostname_fqdn = socket.getfqdn()
	ip_address=socket.gethostbyname(hostname_fqdn)

	serverName = configProperties.getProperty('wls.server.' + str(server) + '.name')
	#std_ManagedServerName='REPLACE_HOSTNAME_'+serverName+'_'+LANE+'_REPLACE_MANAGED_SERVER_INDEX'
	std_ManagedServerName=setServerName(configProperties, serverName)
	NumOfManagedServers=configProperties.getProperty('wls.server.'+str(server)+'.NumOfManagedServers')
	StartListenPortForHost=configProperties.getProperty('wls.server.'+str(server)+'.StartListenPortForHost')
	ManagedServer_HttpListenPortIncrementPerHost = configProperties.getProperty('wls.server.'+str(server)+'.HttpListenPortIncrementPerHost') 
	ManagedServer_SSLListenPortIncrementOverHttpPort = configProperties.getProperty('wls.server.'+str(server)+'.SSLListenPortIncrementOverHttpPort')
	ManagedServer_TwoWaySSLEnabled = configProperties.getProperty('wls.server.'+str(server)+'.TwoWaySSLEnabled')
	ManagedServer_LogLocation = configProperties.getProperty('wls.server.'+str(server)+'.log_loc')
	ms_ServerHostName = configProperties.getProperty('wls.server.'+str(server)+'.Hostname')
	#ms_ServerHostName=hostname_fqdn
	#ClusterName=configProperties.getProperty('wls.server.'+str(server)+'.ClusterName')
	rawClusterName=configProperties.getProperty('wls.server.'+str(server)+'.cluster.name')
	if not rawClusterName is None:
		ClusterName=setClusterName(configProperties, rawClusterName)

	rawClusterChannelName=configProperties.getProperty('wls.server.'+str(server)+'.ClusterChannelName')
	if not rawClusterChannelName is None:
		ClusterChannelName=setClusterChannelName(configProperties, rawClusterChannelName)
    
	###Node
	Node_Tag_dict = createNodeTag(ms_ServerHostName, ip_address, StartListenPortForHost, ManagedServer_HttpListenPortIncrementPerHost, ManagedServer_SSLListenPortIncrementOverHttpPort, ManagedServer_TwoWaySSLEnabled, NumOfManagedServers, std_ManagedServerName, ManagedServer_LogLocation, ClusterName, ClusterChannelName)
	Node_Tag = doc.createElement('Node')
	createXMLChild(msTag, Node_Tag, Node_Tag_dict)

	addSvrStartArgElement(configProperties, server, Node_Tag)
	if not ClusterName is None:
		addJDBCElement(configProperties, server, ClusterName, Node_Tag)
		addJMSElement(configProperties, server, serverName, ClusterName, Node_Tag, std_ManagedServerName)
	else:
		addJDBCElement(configProperties, server, std_ManagedServerName, Node_Tag)
		addJMSElement(configProperties, server, serverName, std_ManagedServerName, Node_Tag, std_ManagedServerName)
    

def addSvrStartArgElement(configProperties, server, nodeTag):
	JavaHome=configProperties.getProperty('wls.domain.javahome')
	OracleHome=configProperties.getProperty('wls.oracle.home')
	sslEnable=configProperties.getProperty('wls.domain.ssl.enable')
	if not server is None and len(server)>0:
		Arguments = configProperties.getProperty('wls.server.'+str(server)+'.vmarguments')
		sslArguments = configProperties.getProperty('wls.server.'+str(server)+'.ssl.vmarguments')
		if not sslEnable is None and sslEnable.lower() == 'true':
			Arguments = Arguments+' '+sslArguments
		#ManagedServer_GC_Log = configProperties.getProperty('wls.server.'+str(server)+'.gc_log_loc')
		#Arguments = ManagedServer_Arguments+' '+'-Xloggc:'+ManagedServer_GC_Log
		ManagedServer_Classpath=configProperties.getProperty('wls.server.'+str(server)+'.Classpath')
		ServerStartArguments_Tag_dict = createServerStartArguments_Tag_dict(JavaHome, OracleHome, ManagedServer_Classpath, Arguments)
		ServerStartArguments_Tag = doc.createElement('ServerStartArguments')
		createXMLChild(nodeTag, ServerStartArguments_Tag, ServerStartArguments_Tag_dict)
    
    
def addJDBCElement(configProperties, server, dbTarget, nodeTag):
    dataSources=configProperties.getProperty('wls.server.'+str(server)+'.datasource')
    if not dataSources is None and len(dataSources)>0:
        if not server is None:
            dataSourceList = dataSources.split(',')
            for ds in dataSourceList:
				rawDsName=configProperties.getProperty('jdbc.datasource.'+str(ds)+'.Name')
				dsName=setDSName(configProperties, rawDsName)
				#print dsName
				dbUser=configProperties.getProperty('jdbc.datasource.'+str(ds)+'.Username')
				dbPassword=configProperties.getProperty('jdbc.datasource.'+str(ds)+'.Password')
				JNDIName=configProperties.getProperty('jdbc.datasource.'+str(ds)+'.JNDI')
				dbConnectionURL=configProperties.getProperty('jdbc.datasource.'+str(ds)+'.URL')
				#dbTarget=configProperties.getProperty('wls.server.'+str(server)+'.ClusterName')
								
				InitialCapacity=configProperties.getProperty('jdbc.datasource.'+str(ds)+'.Capacity.Initial')
				MaximumCapacity=configProperties.getProperty('jdbc.datasource.'+str(ds)+'.Capacity.Max')
				CapacityIncrement=configProperties.getProperty('jdbc.datasource.'+str(ds)+'.Capacity.Increment')
				ConnectionCreationRetryFrequency=configProperties.getProperty('jdbc.datasource.'+str(ds)+'.ConnectionCreationRetryFrequency')

				DataSource_Tag_dict = createDataSource_Tag_dict(dsName, dbUser, dbPassword, JNDIName, dbConnectionURL, dbTarget, InitialCapacity, MaximumCapacity, CapacityIncrement, ConnectionCreationRetryFrequency)
				DataSource_Tag = doc.createElement('DataSource')
				createXMLChild(nodeTag, DataSource_Tag, DataSource_Tag_dict)


def addJMSElement(configProperties, server, serverName, jmsModuleTarget, nodeTag, std_ManagedServerName):
	jmsservers = configProperties.getProperty('wls.server.'+str(server)+'.jmsServers')
	jmsModules = configProperties.getProperty('wls.server.'+str(server)+'.jmsModules')
	jmsModuleSubDeployments = configProperties.getProperty('wls.server.'+str(server)+ '.SubDeployments')
	jmsserverName=''
	if not jmsservers is None and len(jmsservers)>0:
		jmsserverList = jmsservers.split(',')
		for jmsserver in jmsserverList:
			jmsserverName_Raw = configProperties.getProperty('jmsServer.' + str(jmsserver) + '.Name')
			jmsserverName = setJMSServerName(configProperties, jmsserverName_Raw)
			##Add JMS Server
			JMSServers_Tag_dict = createJMSServers_Tag_dict(jmsserverName)
			JMSServers_Tag = doc.createElement('JMSServers')
			createXMLChild(nodeTag, JMSServers_Tag, JMSServers_Tag_dict) 

	if not jmsModules is None and len(jmsModules)>0:
		jmsModuleList = jmsModules.split(',')
		for jmsModule in jmsModuleList:
			jmsModuleName_Raw = configProperties.getProperty('jmsModule.' + str(jmsModule) + '.Name')
			jmsModuleName = setJMSModuleName(configProperties, jmsModuleName_Raw)
			##Add JMS Module
			JMSModules_Tag_dict = createJMSModules_Tag_dict(jmsModuleName, jmsModuleTarget)
			JMSModules_Tag = doc.createElement('JMSModules')
			createXMLChild(nodeTag, JMSModules_Tag, JMSModules_Tag_dict)
			#
			#jmsModuleSubDeployments = configProperties.getProperty('jmsModule.' + str(jmsModule) + '.SubDeployments')
			if not jmsModuleSubDeployments is None and len(jmsModuleSubDeployments)>0:
				jmsModuleSubDeploymentList = jmsModuleSubDeployments.split(',')
				for jmsModuleSubDeployment in jmsModuleSubDeploymentList:
					jmsModuleSubDeploymentName_Raw = configProperties.getProperty('jmsModule.' + str(jmsModule) + '.SubDeployment.' + str(jmsModuleSubDeployment) + '.Name')
					jmsModuleSubDeploymentName=setJMSSDName(configProperties, jmsModuleSubDeploymentName_Raw)
					jmsModuleSubDeploymentTargetType = configProperties.getProperty('jmsModule.' + str(jmsModule) + '.SubDeployment.' + str(jmsModuleSubDeployment) + '.TargetType')					
					jmsModuleSubDeploymentTargets = configProperties.getProperty('jmsModule.' + str(jmsModule) + '.SubDeployment.' + str(jmsModuleSubDeployment) + '.Targets')
					jmsModuleSubDeploymentTargetName=''
					if not jmsModuleSubDeploymentTargetType is None and str(jmsModuleSubDeploymentTargetType) == 'JMSServer':
						jmsModuleSubDeploymentTargetName = configProperties.getProperty('jmsServer.' + str(jmsModuleSubDeploymentTargets) + '.Name')

					if not jmsModuleSubDeploymentTargetType is None and str(jmsModuleSubDeploymentTargetType) == 'Cluster':
						jmsModuleSubDeploymentTargetName = configProperties.getProperty('wls.cluster.'+str(jmsModuleSubDeploymentTargets)+'.name')
						
					if not jmsModuleSubDeploymentName is None or len(jmsModuleSubDeploymentName)>0:
						SubDeployment_Tag_dict = createSubDeployment_Tag_dict(jmsModuleSubDeploymentName, jmsModuleSubDeploymentTargetName)
						SubDeployment_Tag = doc.createElement('SubDeployment')
						createXMLChild(JMSModules_Tag, SubDeployment_Tag, SubDeployment_Tag_dict)

					jmsModuleSubDeploymentConnectionFactories = configProperties.getProperty('jmsModule.' + str(jmsModule) + '.SubDeployment.' + str(jmsModuleSubDeployment) + '.ConnectionFactories')
					if not jmsModuleSubDeploymentConnectionFactories is None and len(jmsModuleSubDeploymentConnectionFactories)>0:
						jmsModuleSubDeploymentConnectionFactoryList = jmsModuleSubDeploymentConnectionFactories.split(',')
						for jmsModuleSubDeploymentConnectionFactory in jmsModuleSubDeploymentConnectionFactoryList:
							jmsConnectionFactoryName_Raw = configProperties.getProperty('jmsModule.' + str(jmsModule) + '.SubDeployment.' + str(jmsModuleSubDeployment) + '.ConnectionFactory.' + str(jmsModuleSubDeploymentConnectionFactory) + '.Name')
							jmsConnectionFactoryName=setJMSCFName(configProperties, jmsConnectionFactoryName_Raw)
							jmsConnectionFactoryJNDI = configProperties.getProperty('jmsModule.' + str(jmsModule) + '.SubDeployment.' + str(jmsModuleSubDeployment) + '.ConnectionFactory.' + str(jmsModuleSubDeploymentConnectionFactory) + '.JNDI')
							#if not jmsConnectionFactoryName is None or len(jmsConnectionFactoryName)>0:
							##Add ConectionFactory
							ConnectionFactory_Tag_dict = createConnectionFactory_Tag_dict(jmsConnectionFactoryName, jmsConnectionFactoryJNDI, jmsModuleSubDeploymentName)
							ConnectionFactory_Tag = doc.createElement('ConnectionFactory')
							createXMLChild(JMSModules_Tag, ConnectionFactory_Tag, ConnectionFactory_Tag_dict)
				
					jmsModuleSubDeploymentTopics = configProperties.getProperty('jmsModule.' + str(jmsModule) + '.SubDeployment.' + str(jmsModuleSubDeployment) + '.Topics')
					if not jmsModuleSubDeploymentTopics is None and len(jmsModuleSubDeploymentTopics)>0:
						jmsModuleSubDeploymentTopicList = jmsModuleSubDeploymentTopics.split(',')
						for jmsModuleSubDeploymentTopic in jmsModuleSubDeploymentTopicList:
							jmsTopicName_Raw = configProperties.getProperty('jmsModule.' + str(jmsModule) + '.SubDeployment.' + str(jmsModuleSubDeployment) + '.Topic.' + str(jmsModuleSubDeploymentTopic) + '.Name')
							jmsTopicName=setJMSTopicName(configProperties, jmsTopicName_Raw)
							jmsTopicJNDI = configProperties.getProperty('jmsModule.' + str(jmsModule) + '.SubDeployment.' + str(jmsModuleSubDeployment) + '.Topic.' + str(jmsModuleSubDeploymentTopic) + '.JNDI')
							jmsTopicType = configProperties.getProperty('jmsModule.' + str(jmsModule) + '.SubDeployment.' + str(jmsModuleSubDeployment) + '.Topic.' + str(jmsModuleSubDeploymentTopic) + '.TopicType')
							jmsReDeliveryLimit = configProperties.getProperty('jmsModule.' + str(jmsModule) + '.SubDeployment.' + str(jmsModuleSubDeployment) + '.Topic.' + str(jmsModuleSubDeploymentTopic) + '.RedeliveryLimit')
							jmsReDeliveryDelay = configProperties.getProperty('jmsModule.' + str(jmsModule) + '.SubDeployment.' + str(jmsModuleSubDeployment) + '.Topic.' + str(jmsModuleSubDeploymentTopic) + '.RedeliveryDelay')
							jmsLoadBalancingPolicy = configProperties.getProperty('jmsModule.' + str(jmsModule) + '.SubDeployment.' + str(jmsModuleSubDeployment) + '.Topic.' + str(jmsModuleSubDeploymentTopic) + '.LoadBalancingPolicy')
							jmsMaximumMessageSize = configProperties.getProperty('jmsModule.' + str(jmsModule) + '.SubDeployment.' + str(jmsModuleSubDeployment) + '.Topic.' + str(jmsModuleSubDeploymentTopic) + '.MaximumMessageSize')
							##Add Topic destination
							Topic_Tag_dict = createTopic_Tag_dict(jmsTopicType, jmsTopicName, jmsTopicJNDI, jmsModuleSubDeploymentName, jmsLoadBalancingPolicy, jmsReDeliveryDelay, jmsReDeliveryLimit, jmsMaximumMessageSize)
							Topic_Tag = doc.createElement('Topic')
							createXMLChild(JMSModules_Tag, Topic_Tag, Topic_Tag_dict)

					jmsModuleSubDeploymentQueues = configProperties.getProperty('jmsModule.' + str(jmsModule) + '.SubDeployment.' + str(jmsModuleSubDeployment) + '.Queues')
					if not jmsModuleSubDeploymentQueues is None and len(jmsModuleSubDeploymentQueues)>0:
						jmsModuleSubDeploymentQueueList = jmsModuleSubDeploymentQueues.split(',')
						for jmsModuleSubDeploymentQueue in jmsModuleSubDeploymentQueueList:
							jmsQueueName_Raw = configProperties.getProperty('jmsModule.' + str(jmsModule) + '.SubDeployment.' + str(jmsModuleSubDeployment) + '.Queue.' + str(jmsModuleSubDeploymentQueue) + '.Name')
							#jmsQueueName = jmsQueueName_Raw+serverName+'_'+LANE+'_REPLACE_MACHINE_SUFFIX_REPLACE_MANAGED_SERVER_INDEX'
							jmsQueueName=setJMSQueueName(configProperties, jmsQueueName_Raw)
							jmsQueueJNDI = configProperties.getProperty('jmsModule.' + str(jmsModule) + '.SubDeployment.' + str(jmsModuleSubDeployment) + '.Queue.' + str(jmsModuleSubDeploymentQueue) + '.JNDI')
							jmsQueueType = configProperties.getProperty('jmsModule.' + str(jmsModule) + '.SubDeployment.' + str(jmsModuleSubDeployment) + '.Queue.' + str(jmsModuleSubDeploymentQueue) + '.QueueType')
							jmsExpirationPolicy = configProperties.getProperty('jmsModule.' + str(jmsModule) + '.SubDeployment.' + str(jmsModuleSubDeployment) + '.Queue.' + str(jmsModuleSubDeploymentQueue) + '.ExpirationPolicy')
							jmsTimeToLive = configProperties.getProperty('jmsModule.' + str(jmsModule) + '.SubDeployment.' + str(jmsModuleSubDeployment) + '.Queue.' + str(jmsModuleSubDeploymentQueue) + '.TimeToLive')
							jmsForwardDelay = configProperties.getProperty('jmsModule.' + str(jmsModule) + '.SubDeployment.' + str(jmsModuleSubDeployment) + '.Queue.' + str(jmsModuleSubDeploymentQueue) + '.ForwardDelay')
							jmsReDeliveryLimit = configProperties.getProperty('jmsModule.' + str(jmsModule) + '.SubDeployment.' + str(jmsModuleSubDeployment) + '.Queue.' + str(jmsModuleSubDeploymentQueue) + '.RedeliveryLimit')
							jmsReDeliveryDelay = configProperties.getProperty('jmsModule.' + str(jmsModule) + '.SubDeployment.' + str(jmsModuleSubDeployment) + '.Queue.' + str(jmsModuleSubDeploymentQueue) + '.RedeliveryDelay')
							jmsLoadBalancingPolicy = configProperties.getProperty('jmsModule.' + str(jmsModule) + '.SubDeployment.' + str(jmsModuleSubDeployment) + '.Queue.' + str(jmsModuleSubDeploymentQueue) + '.LoadBalancingPolicy')
							jmsMaximumMessageSize = configProperties.getProperty('jmsModule.' + str(jmsModule) + '.SubDeployment.' + str(jmsModuleSubDeployment) + '.Queue.' + str(jmsModuleSubDeploymentQueue) + '.MaximumMessageSize')
							jmsErrorDestination = configProperties.getProperty('jmsModule.' + str(jmsModule) + '.SubDeployment.' + str(jmsModuleSubDeployment) + '.Queue.' + str(jmsModuleSubDeploymentQueue) + '.ErrorDestination')
							##Add Queue destination
							#Queue_Tag_dict = createQueue_Tag_dict(jmsQueueType, jmsQueueName, jmsQueueJNDI, jmsModuleSubDeploymentName, jmsLoadBalancingPolicy, jmsReDeliveryDelay, jmsReDeliveryLimit)
							Queue_Tag_dict = createQueue_Tag_dict(jmsQueueType, jmsQueueName, jmsQueueJNDI, jmsModuleSubDeploymentName, jmsExpirationPolicy, jmsForwardDelay, jmsTimeToLive, jmsLoadBalancingPolicy, jmsReDeliveryDelay, jmsReDeliveryLimit, jmsMaximumMessageSize, jmsErrorDestination)
							Queue_Tag = doc.createElement('Queue')
							createXMLChild(JMSModules_Tag, Queue_Tag, Queue_Tag_dict)

def setServerName(configProperties, rawServerName):
	std_ManagedServerName=''
	#domain_name=configProperties.getProperty('wls.domain.name')
	std_ManagedServerName=rawServerName
		
	return  str(std_ManagedServerName)
  

def setClusterName(configProperties, rawClusterName):
	domain_name=configProperties.getProperty('wls.domain.name')
	#print 'rawClusterName='+rawClusterName
	clusterName=''
	clusterName=rawClusterName

	return clusterName
    
            
def setClusterChannelName(configProperties, rawClusterChannelName):
	domain_name=configProperties.getProperty('wls.domain.name')
	#print 'rawClusterChannelName='+rawClusterChannelName
	clusterChannelName=''
	clusterChannelName=rawClusterChannelName
			
	#print 'clusterChannelName='+clusterChannelName
	return clusterChannelName
	
def setDSName(configProperties, rawDSName):
	dsName=rawDSName
	return dsName
	
def setJMSServerName(configProperties, rawjmsserverName):
	jmsserverName=''
	domain_name=configProperties.getProperty('wls.domain.name')
	jmsserverName=rawjmsserverName

	return jmsserverName
    
    
def setJMSModuleName(configProperties, rawjmsModuleName):
	jmsModuleName=''
	domain_name=configProperties.getProperty('wls.domain.name')
	jmsModuleName=rawjmsModuleName

	return jmsModuleName

def setJMSSDName(configProperties, rawjmsSDName):
	#print rawjmsSDName
	jmsSDName=''
	domain_name=configProperties.getProperty('wls.domain.name')
	jmsSDName=rawjmsSDName

	return jmsSDName


def setJMSCFName(configProperties, rawjmsCFName):
	jmsCFName=''
	domain_name=configProperties.getProperty('wls.domain.name')
	jmsCFName=rawjmsCFName
		
	return jmsCFName


def setJMSTopicName(configProperties, rawjmsTopicName):
	jmsTopicName=''
	domain_name=configProperties.getProperty('wls.domain.name')
	jmsTopicName=rawjmsTopicName

	return jmsTopicName

def setJMSQueueName(configProperties, rawjmsQueueName):
	jmsQueueName=''
	domain_name=configProperties.getProperty('wls.domain.name')
	jmsQueueName=rawjmsQueueName

	return jmsQueueName