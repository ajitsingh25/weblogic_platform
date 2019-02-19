import os

try:
	commonModule
except NameError:
	execfile('ConfigNOW/common/common.py')


def createNetworkChannel(domainProperties, networkChannelName, networkChannelProtocol):
        ##AdminServer SSl Connect
        #connectAdminServerOverSSL(domainProperties)

        try:
                startEditSession()
                clustersList=cmo.getClusters()
                for each_cluster in clustersList:
                        clusterName=each_cluster.getName()
                        cd('/Clusters/'+clusterName)
                        servers = cmo.getServers()
                        for each_server in servers:
                                svrName=each_server.getName()
                                cd('/Clusters/'+clusterName+'/Servers/'+svrName)
                                machineName = cmo.getMachine().getName()
                                cd('SSL/'+svrName)
                                listenPort = cmo.getListenPort()
                                listenPortNC = int("10" + str(listenPort)[1:])
                                cd('/Clusters/'+clusterName+'/Servers/'+svrName)
                                cmo.createNetworkAccessPoint(networkChannelName)
                                cd('NetworkAccessPoints/'+networkChannelName)
                                cmo.setProtocol(networkChannelProtocol)
                                cmo.setListenAddress(machineName)
                                cmo.setListenPort(listenPortNC)
                                cmo.setEnabled(true)
                                cmo.setHttpEnabledForThisProtocol(false)
                                cmo.setTunnelingEnabled(false)
                                cmo.setOutboundEnabled(true)
                                cmo.setOutboundPrivateKeyEnabled(true)
                                cmo.setTwoWaySSLEnabled(true)
                                cmo.setClientCertificateEnforced(false)
                                cmo.setChannelIdentityCustomized(false)
                                cmo.setCustomPrivateKeyAlias(None)
                                cmo.setCustomPrivateKeyPassPhrase(None)
                                cmo.setChannelWeight(80)
                saveAndActivateChanges()
        except weblogic.descriptor.BeanAlreadyExistsException, bae:
                print "<Error> Caught BeanAlreadyExistsException exception in createNetworkChannelJVM, so skipping it !!"
                stopEdit('y')
        except Exception, e:
                print "<Error> Caught exception in createNetworkChannelJVM"
				
				
def createDomainNetworkChannel(domainProperties):
	channels=domainProperties.getProperty('cluster.network.channels')
	if not channels is None and len(channels)>0:
		channelsList = channels.split(',')
		for each_channel in channelsList:
			networkChannelName=domainProperties.getProperty('cluster.network.channel.'+str(each_channel)+'.name')
			networkChannelProtocol=domainProperties.getProperty('cluster.network.channel.'+str(each_channel)+'.protocol')
			createNetworkChannel(domainProperties, networkChannelName, networkChannelProtocol) 
