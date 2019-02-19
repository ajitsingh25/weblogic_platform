import os

try:
	commonModule
except NameError:
	execfile('ConfigNOW/common/common.py')

def configureNodeManagerSSL(domainProperties):
	separator = os.sep
	sslEnable=domainProperties.getProperty('wls.domain.ssl.enable')
	adminServer_name=domainProperties.getProperty('wls.admin.name')
	hostname_raw=domainProperties.getProperty('wls.admin.Hostname')
	hostname=hostname_raw.split('.')[0].upper()
	domainServ=domainProperties.getProperty('wls.domain.serv')
	keystoreType=domainProperties.getProperty('wls.domain.serv.keystore.type')
	protected_pkg_root_loc=domainProperties.getProperty('wls.domain.serv.rootDir')
	protectedJksDir=domainProperties.getProperty('wls.domain.serv.protectedDir')
	keystoreDir=protected_pkg_root_loc+separator+hostname+separator+domainServ+separator+protectedJksDir

	asIdentityJKSName=domainProperties.getProperty('wls.domain.serv.jks.as.Identity.name')
	asIdentityJKSPassword=domainProperties.getProperty('wls.domain.serv.jks.as.Identity.password')
	asprivateKeyAlias=domainProperties.getProperty('wls.domain.serv.jks.as.alias.name')
	asprivateKeyPhrase=domainProperties.getProperty('wls.domain.serv.jks.as.alias.password')
	asIdentityJKS=keystoreDir+separator+asIdentityJKSName

	nodeManagerHome=domainProperties.getProperty('nodemanager.home')
	nmPropertiesFile=nodeManagerHome+separator+'nodemanager.properties'
	
	if not asIdentityJKSName in open(nmPropertiesFile).read() and not sslEnable is None and sslEnable.lower() == 'true':
		f= open(nmPropertiesFile, 'a+')
		lines = open(nmPropertiesFile).readlines()
		if "###SSL Configuration\n" not in lines:
			f.write("\n")
			f.write("###SSL Configuration\n")
			f.write("KeyStores=%s\n"% keystoreType)
			f.write("CustomIdentityKeyStoreFileName=%s\n"% asIdentityJKS)
			f.write("CustomIdentityKeyStorePassPhrase=%s\n"% asIdentityJKSPassword)
			f.write("CustomIdentityAlias=%s\n"% asprivateKeyAlias)
			f.write("CustomIdentityPrivateKeyPassPhrase=%s\n"% asprivateKeyPhrase)
			f.flush()
			f.close()
		else:
			print 'Node Manager SSL is already Configured for this Host'
		
