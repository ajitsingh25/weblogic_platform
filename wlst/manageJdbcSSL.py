from weblogic.descriptor import BeanAlreadyExistsException
import os

try:
	commonModule
except NameError:
	execfile('ConfigNOW/common/common.py')

def undoChangesAndExitWithError():

	cfgManager = getConfigManager()

	try:
		cfgManager.getChanges()
		print "\n"
		print 'There are existing edit sessions'
		edit()    
		print "\n"
		print 'Undo any pending changes'
		undo('true','y')    
		print "\n"
		print 'Cancelling any existing edit sessions'
		cancelEdit('y')
		print "\n"
	except:
		print "\n"
		print 'There are no existing edit sessions'
		print "\n"
	disconnect()

	exit(exitcode=1)
	

def configureJDBCSSL(domainProperties):

	separator = os.sep
	adminServer_name=domainProperties.getProperty('wls.admin.name')
	hostname_raw=domainProperties.getProperty('wls.admin.Hostname')
	hostname=hostname_raw.split('.')[0].upper()
	domainServ=domainProperties.getProperty('wls.domain.serv')
	keystoreType=domainProperties.getProperty('wls.domain.serv.keystore.type')
	protected_pkg_root_loc=domainProperties.getProperty('wls.domain.serv.rootDir')
	protectedJksDir=domainProperties.getProperty('wls.domain.serv.protectedDir')
	keystoreDir=protected_pkg_root_loc+separator+hostname+separator+domainServ+separator+protectedJksDir

	msTrustJKSName=domainProperties.getProperty('wls.domain.serv.jks.ms.Trust.name')
	msTrustJKSPassword=domainProperties.getProperty('wls.domain.serv.jks.ms.Trust.password')
	msTrustJKS=keystoreDir+separator+msTrustJKSName
    	domainHome=domainProperties.getProperty('wls.domain.dir')+separator+str(domainName)
	
	dataSources=domainProperties.getProperty('jdbc.datasources')
	if not dataSources is None and len(dataSources)>0:
		dataSourceList = dataSources.split(',')
		for ds in dataSourceList:
			dsName=domainProperties.getProperty('jdbc.datasource.'+str(ds)+'.Name')
			dsUser=domainProperties.getProperty('jdbc.datasource.'+str(ds)+'.Username')
			dsSSLURL=domainProperties.getProperty('jdbc.datasource.'+str(ds)+'.ssl.URL')
			dsPath='/JDBCSystemResources/'+dsName+'/JDBCResource/'+dsName+'/JDBCDriverParams/'+dsName
    
			try:
				edit()
				startEdit()
				#startEditSession()
				
				print 'set user'
				cd(dsPath)
				cmo.setUrl(dsSSLURL)
				cd(dsPath+'/Properties/'+dsName+'/Properties/user')
				cmo.unSet('SysPropValue')
				cmo.unSet('EncryptedValue')
				cmo.setValue(dsUser)
				
				print 'set trustStore'
				cd(dsPath+'/Properties/'+dsName)
				cmo.createProperty('javax.net.ssl.trustStore')
				cd(dsPath+'/Properties/'+dsName+'/Properties/javax.net.ssl.trustStore')
				cmo.unSet('SysPropValue')
				cmo.unSet('EncryptedValue')
				cmo.setValue(msTrustJKS)
				
				print 'set trustStoreType'
				cd(dsPath+'/Properties/'+dsName)
				cmo.createProperty('javax.net.ssl.trustStoreType')
				cd(dsPath+'/Properties/'+dsName+'/Properties/javax.net.ssl.trustStoreType')
				cmo.unSet('SysPropValue')
				cmo.unSet('EncryptedValue')
				cmo.setValue('JKS')
				
				print 'set trustStorePassword'
				cd(dsPath+'/Properties/'+dsName)
				cmo.createProperty('javax.net.ssl.trustStorePassword')
				cd(dsPath+'/Properties/'+dsName+'/Properties/javax.net.ssl.trustStorePassword')
				cmo.unSet('Value')
				cmo.unSet('SysPropValue')
				cmo.setEncryptedValue(msTrustJKSPassword)
				cmo.setEncryptedValueEncrypted(encrypt(msTrustJKSPassword,domainHome))
				print 'done'
				
				saveAndActivateChanges()
			except weblogic.descriptor.BeanAlreadyExistsException, bae:
				print "<Error> Caught BeanAlreadyExistsException exception , so skipping it !!" + str(bae)
				stopEdit('y')
				pass
			except Exception, e:
				print "<Error> Caught exception in ssl " + str(e)
				undoChangesAndExitWithError()
				sys.exit()
		
def rollbackJDBCtoNonSSL():
	dataSources=domainProperties.getProperty('jdbc.datasources')
	if not dataSources is None and len(dataSources)>0:
		dataSourceList = dataSources.split(',')
		for ds in dataSourceList:
			dsName=domainProperties.getProperty('jdbc.datasource.'+str(ds)+'.Name')
			dsUser=domainProperties.getProperty('jdbc.datasource.'+str(ds)+'.Username')
			dsURL=domainProperties.getProperty('jdbc.datasource.'+str(ds)+'.URL')
			dsPath='/JDBCSystemResources/'+dsName+'/JDBCResource/'+dsName+'/JDBCDriverParams/'+dsName

			try:
				edit()
				startEdit()
				#startEditSession()
				print "destroy.."
				cd(dsPath+'/Properties/'+dsName)
				cmo.destroyProperty(getMBean(dsPath+'/Properties/'+dsName+'/Properties/javax.net.ssl.trustStorePassword'))
				cmo.destroyProperty(getMBean(dsPath+'/Properties/'+dsName+'/Properties/javax.net.ssl.trustStore'))
				cmo.destroyProperty(getMBean(dsPath+'/Properties/'+dsName+'/Properties/javax.net.ssl.trustStoreType'))
				print "destroyed.."
				print "set Non SSL Url..."
				cd(dsPath)
				cmo.setUrl(dsURL)
				print "done set Non SSL Url..."
				saveAndActivateChanges()
			except weblogic.descriptor.BeanAlreadyExistsException, bae:
				print "<Error> Caught BeanAlreadyExistsException exception , so skipping it !!" + str(bae)
				stopEdit('y')
				pass
			except Exception, e:
				print "<Error> Caught exception in exception " + str(e)
				undoChangesAndExitWithError()
				sys.exit()
				
				
