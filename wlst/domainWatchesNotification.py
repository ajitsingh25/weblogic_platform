from weblogic.descriptor import BeanAlreadyExistsException	
from java.util import Properties
import os

try:
	commonModule
except NameError:
	execfile('wlst/common.py')


def createMailSession(domainProperties):
    mailSessions=domainProperties.getProperty('wls.domain.mail.sessions')
    if not mailSessions is None and len(mailSessions) >0:
        mailSessionList=mailSessions.split(',')
        for mailSession in mailSessionList:
			mailSessionName=domainProperties.getProperty('wls.domain.mail.session.'+str(mailSession)+'.name')
			#mailSessionTarget=domainProperties.getProperty('wls.domain.mail.session.'+str(mailSession)+'.target')
			smtpHost=domainProperties.getProperty('wls.domain.mail.session.'+str(mailSession)+'.smtp.host')
			smtpPort=domainProperties.getProperty('wls.domain.mail.session.'+str(mailSession)+'.smtp.port')
			mailHost=domainProperties.getProperty('wls.domain.mail.session.'+str(mailSession)+'.host')
			mailJndi=domainProperties.getProperty('wls.domain.mail.session.'+str(mailSession)+'.jndi')
			cd('/')
			serversList = cmo.getServers()
			newTargetListNames=[]
			if len(serversList) >0:
				for each_server in serversList:
					svrName=each_server.getName()
					if svrName not in newTargetListNames:
						newTargetListNames.append(svrName)
			try:
				startEditSession()
				cd('/')
				mailSessionBean = cmo.createMailSession(mailSessionName)
				cd('/MailSessions/'+mailSessionName)
				targetsForDeployment=[]
				newTargetListTypes='Server'
				for value in newTargetListNames:
					nextName =str('com.bea:Name='+value+',Type='+newTargetListTypes)
					targetsForDeployment.append(ObjectName(nextName))
				set('Targets',jarray.array(targetsForDeployment, ObjectName))
				#set('Targets',jarray.array([ObjectName('com.bea:Name='+str(mailSessionTarget)+',Type=Server')], ObjectName))
				mailSessionBean.setJNDIName(mailJndi)

				properties = java.util.Properties()
				properties.put('mail.host',mailHost)
				properties.put('mail.smtp.host',smtpHost)
				properties.put('mail.smtp.port',smtpPort)
				mailSessionBean.setProperties(properties)
				saveAndActivateChanges()
			except weblogic.descriptor.BeanAlreadyExistsException, bae:
				print "<Error> Caught BeanAlreadyExistsException exception in createMailSession, so skipping it !!" + str(bae)
				stopEdit('y')
				pass
			except Exception, e:
				print "<Error> Caught exception in createMailSession" + str(e)
				discardChanges()
				sys.exit()
        
def createDiagnosticModule(domainProperties):
    modules = domainProperties.getProperty('wls.domain.diagnostic.modules')
    if not modules is None and len(modules) >0:
        moduleList = modules.split(',')
        for module in moduleList:
			moduleName = domainProperties.getProperty('wls.domain.diagnostic.module.'+str(module)+'.name')
			#moduleTarget = domainProperties.getProperty('wls.domain.diagnostic.module.'+str(module)+'.target')
			cd('/')
			serversList = cmo.getServers()
			newTargetListNames=[]
			if len(serversList) >0:
				for each_server in serversList:
					svrName=each_server.getName()
					if svrName not in newTargetListNames:
						newTargetListNames.append(svrName)
			try:
				startEditSession()
				cd('/')
				cmo.createWLDFSystemResource(moduleName)
				cd('/WLDFSystemResources/'+moduleName)
				targetsForDeployment=[]
				newTargetListTypes='Server'
				for value in newTargetListNames:
					nextName =str('com.bea:Name='+value+',Type='+newTargetListTypes)
					targetsForDeployment.append(ObjectName(nextName))
				set('Targets',jarray.array(targetsForDeployment, ObjectName))
				saveAndActivateChanges()
				return moduleName
			except weblogic.descriptor.BeanAlreadyExistsException, bae:
				return moduleName
				print "<Error> Caught BeanAlreadyExistsException exception in createDiagnosticModule, so skipping it !!" + str(bae)
				stopEdit('y')
				pass
			except Exception, e:
				print "<Error> Caught exception in createDiagnosticModule" + str(e)
				discardChanges()
				sys.exit()
				
            
def createNotification(domainProperties, moduleName):
    notifications = domainProperties.getProperty('wls.domain.diagnostic.module.module1.notifications')
    if not notifications is None and len(notifications) >0:
        notificationList = notifications.split(',')
        for notification in notificationList:
			notificationName = domainProperties.getProperty('wls.domain.diagnostic.module.module1.notifications.'+str(notification)+'.name')
			notificationEnable = domainProperties.getProperty('wls.domain.diagnostic.module.module1.notifications.'+str(notification)+'.enable')
			notificationMailSession = domainProperties.getProperty('wls.domain.diagnostic.module.module1.notifications.'+str(notification)+'.mailsession')
			notificationRecipients = domainProperties.getProperty('wls.domain.diagnostic.module.module1.notifications.'+str(notification)+'.recipients')
			recipientStrList = []
			if not notificationRecipients is None and len(notificationRecipients) > 0:
				notificationRecipientsList = notificationRecipients.split(',')
				for recipient in notificationRecipientsList:
					recipientStrList.append(String(recipient))

			try:
				startEditSession()        
				notificationHome='/WLDFSystemResources/'+str(moduleName)+'/WLDFResource/'+str(moduleName)+'/WatchNotification/'+str(moduleName)
				cd(notificationHome)
				cmo.createSMTPNotification(notificationName)
				cd(notificationHome+'/SMTPNotifications/'+notificationName)
				cmo.setEnabled(java.lang.Boolean(notificationEnable))
				cmo.setTimeout(30)
				cmo.setMailSessionJNDIName(notificationMailSession)
				set('Recipients',jarray.array(recipientStrList, String))

				cmo.setSubject(None)
				cmo.setBody(None)
				saveAndActivateChanges()
				return notificationName
			except weblogic.descriptor.BeanAlreadyExistsException, bae:
				return notificationName
				print "<Error> Caught BeanAlreadyExistsException exception in createNotification, so skipping it !!" + str(bae)
				stopEdit('y')
				pass
			except Exception, e:
				print "<Error> Caught exception in createNotification" + str(e)
				discardChanges()
				sys.exit()
            
def createDomainWatch(domainProperties, moduleName, notificationName):
	watches = domainProperties.getProperty('wls.domain.diagnostic.module.module1.watches')
	if not watches is None and len(watches) >0:
		watchList = watches.split(',')
		for watch in watchList:
			domainName = domainProperties.getProperty('wls.domain.name')
			watchName = domainProperties.getProperty('wls.domain.diagnostic.module.module1.watches.'+str(watch)+'.name')
			watchEnable = domainProperties.getProperty('wls.domain.diagnostic.module.module1.watches.'+str(watch)+'.enable')
			watchRuleType = domainProperties.getProperty('wls.domain.diagnostic.module.module1.watches.'+str(watch)+'.ruletype')
			watch_sampling_rate = domainProperties.getProperty('wls.domain.diagnostic.module.module1.watches.'+str(watch)+'.sampling_rate')
			watch_sample_period = domainProperties.getProperty('wls.domain.diagnostic.module.module1.watches.'+str(watch)+'.sample_period')
			watch_threshold = domainProperties.getProperty('wls.domain.diagnostic.module.module1.watches.'+str(watch)+'.threshold')
			watch_EL=domainProperties.getProperty('wls.domain.diagnostic.module.module1.watches.'+str(watch)+'.EL')
			#watch_EL='wls:ServerHighStuckThreads(\"'+watch_sampling_rate+' seconds\",\"'+watch_sample_period+' minutes\",'+watch_threshold+')'
			watchHome='/WLDFSystemResources/'+str(moduleName)+'/WLDFResource/'+str(moduleName)+'/WatchNotification/'+str(moduleName)
			try:
				startEditSession()
				cd(watchHome)
				cmo.createWatch(watchName)

				cd(watchHome+'/Watches/'+watchName)
				cmo.setEnabled(java.lang.Boolean(watchEnable))
				cmo.setExpressionLanguage('EL')
				cmo.setRuleType(watchRuleType)
				cmo.setRuleExpression(watch_EL)
				cmo.setAlarmType('AutomaticReset')
				cmo.setAlarmResetPeriod(60000)
				set('Notifications',jarray.array([ObjectName('com.bea:Name='+notificationName+',Type=weblogic.diagnostics.descriptor.WLDFSMTPNotificationBean,Parent=['+domainName+']/WLDFSystemResources['+moduleName+'],Path=WLDFResource['+moduleName+']/WatchNotification['+moduleName+']/SMTPNotifications['+notificationName+']')], ObjectName))

				cd(watchHome+'/Watches/'+watchName+'/Schedule/'+watchName)
				cmo.setMinute('*')
				cmo.setSecond('*')
				cmo.setMinute('*/1')
				saveAndActivateChanges()
			except weblogic.descriptor.BeanAlreadyExistsException, bae:
				print "<Error> Caught BeanAlreadyExistsException exception in createDomainWatch, so skipping it !!" + str(bae)
				stopEdit('y')
			except Exception, e:
				print "<Error> Caught exception in createDomainWatch" + str(e)
				discardChanges()
				sys.exit()

def configureDomainWatchNotification(domainProperties):
    domainMonitoringEnable=domainProperties.getProperty('wls.domain.monitoring.enable')
    if not domainMonitoringEnable is None and str(domainMonitoringEnable).lower() == 'true':
        createMailSession(domainProperties)
        moduleName = createDiagnosticModule(domainProperties)
        notificationName = createNotification(domainProperties, moduleName)
        createDomainWatch(domainProperties, moduleName, notificationName)
        

