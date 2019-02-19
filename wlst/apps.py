##
## apps.py
##
## This script contains functions for application deployments.

from java.io import File 
import thread
import time

#=======================================================================================
# Load required modules
#=======================================================================================

try:
	commonModule
except NameError:
	execfile('ConfigNOW/common/common.py')

#=======================================================================================
# Global variables
#=======================================================================================

appsModule = '1.0.1'

log.debug('Loading module [apps.py] version [' + appsModule + ']')

#=======================================================================================
# Deploy applications
#=======================================================================================

def deployApps(componentProperties):
	"""Deploys applications"""

	applications = componentProperties.getProperty('applications')

	if applications is None:
		log.info('No applications to deploy')
	else:
		apps = applications.split(',')
		for app in apps:
			__deployApp('application.' + app, componentProperties)

#=======================================================================================
# Undeploy applications
#=======================================================================================

def undeployApps(componentProperties):
	"""Deploys applications"""

	applications = componentProperties.getProperty('applications')

	if applications is None:
		log.info('No applications to undeploy')
	else:
		apps = applications.split(',')
		for app in apps:
			__undeployApp('application.' + app, componentProperties=componentProperties)

#=======================================================================================
# Deploy an application
#=======================================================================================

def __deployApp(appPrefix, componentProperties):
	"""Deploys an application"""
	appName = componentProperties.getProperty(appPrefix + '.name')
	appPath = componentProperties.getProperty(appPrefix + '.path')
	targets = componentProperties.getProperty(appPrefix + '.targets')
	isRemote = componentProperties.getProperty(appPrefix +'.isRemote')
	
	if appPath is None or len(appPath)==0:
		appPath = componentProperties.getProperty('applications.default.deploy.path')
	appFile = appPath + File.separator + componentProperties.getProperty(appPrefix + '.file')
	deployTargetList=[]
	if not targets is None and len(targets)>0:
		targetList = targets.split(',')
		for target in targetList:
			targetType = componentProperties.getProperty(appPrefix + '.target.TargetType')
			#print targetType
			if targetType == 'Server':
				#targetName = componentProperties.getProperty('wls.server.'+str(target) + '.name')
				serversList=cmo.getServers()
				if not serversList is None and len(serversList):
					for each_server in serversList:
						svrName=each_server.getName()
						if svrName.find(target) != -1:
							#print svrName
							if svrName not in deployTargetList:
								deployTargetList.append(svrName)

			if targetType == 'Cluster':
				#targetName = componentProperties.getProperty('wls.server.'+str(target) + '.name')
				clusterList=cmo.getClusters()
				if not clusterList is None and len(clusterList):
					for each_cluster in clusterList:
						ctrName=each_cluster.getName()
						if ctrName.find(target) != -1:
							#print ctrName
							if ctrName not in deployTargetList:
								deployTargetList.append(ctrName)
							
	#print deployTargetList
	deployTargets = ','.join(map(str, deployTargetList))
	#print deployTargets
	try:
		if isRemote is not None and isRemote.upper()=='TRUE':
			log.info('Deploying application Remotely: ' + appName)
			progress = deploy(appName, appFile, deployTargets, stageMode='stage',upload='true',remote='true')
		else:
			log.info('Deploying Application : '+appName)
			progress = deploy(appName, appFile, deployTargets)
			#log.info('Deploying application: ' + appName)

			progress.printStatus()
			log.debug(str(appName) + ' has been deployed. Check state ' + str(appName) + '?=' + str(progress.getState()))
			log.debug(str(appName) + ' has been deployed. Check if ' + str(appName) + ' is completed?=' + str(progress.isCompleted()))
			log.debug(str(appName) + ' has been deployed. Check if ' + str(appName) + ' is running?=' + str(progress.isRunning()))
			log.debug(str(appName) + ' has been deployed. Check if ' + str(appName) + ' is failed?=' + str(progress.isFailed()))
			log.debug(str(appName) + ' has been deployed. Check message ' + str(appName) + '?=' + str(progress.getMessage()))
	except Exception, error:
		raise ScriptError, 'Unable to deploy application [' + appName + ']: ' + str(error)
#=======================================================================================
# Undeploy an application
#=======================================================================================

def __undeployApp(appPrefix, componentProperties):
	"""Undeploys an application"""
	domain = componentProperties.getProperty('wls.admin.Hostname')
	hostname = domain.split('.')[0]
	appName = componentProperties.getProperty(appPrefix + '.name')
	targets_raw = componentProperties.getProperty(appPrefix + '.targets')
	targets = hostname+'_'+targets_raw
	undeployTimeout = componentProperties.getProperty('applications.default.undeploy.timeout')
	
	try:
		__stopApp(appName)
		
		log.info('Undeploying application: ' + appName)
		
		progress = undeploy(appName, targets, timeout=undeployTimeout)
		log.debug(str(appName) + ' has been undeployed. Check state ' + str(appName) + '?=' + str(progress.getState()))
		log.debug(str(appName) + ' has been undeployed. Check if ' + str(appName) + ' is completed?=' + str(progress.isCompleted()))
		log.debug(str(appName) + ' has been undeployed. Check if ' + str(appName) + ' is running?=' + str(progress.isRunning()))
		log.debug(str(appName) + ' has been undeployed. Check if ' + str(appName) + ' is failed?=' + str(progress.isFailed()))
		log.debug(str(appName) + ' has been undeployed. Check message ' + str(appName) + '?=' + str(progress.getMessage()))
		if progress.isFailed():
			if str(progress.getMessage()).find('Deployer:149001') == -1:
				raise ScriptError, 'Unable to undeploy application [' + appName + ']: ' + str(progress.getMessage())
	except Exception, error:
		raise ScriptError, 'Unable to undeploy application [' + appName + ']: ' + str(error)

#=======================================================================================
# Stop an application
#=======================================================================================

def __stopApp(appName):
	"""Stops an application"""

	log.info('Stopping application: ' + appName)

	try:
		progress = stopApplication(appName)
		log.debug('Is running? ' + str(progress.isRunning()))
	except Exception, error:
		raise ScriptError, 'Unable to stop application [' + appName + ']: ' + str(error)

