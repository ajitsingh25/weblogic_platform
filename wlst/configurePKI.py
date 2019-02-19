import os

try:
	commonModule
except NameError:
	execfile('ConfigNOW/common/common.py')

def domainSSLConfiguration(domainProperties):
	separator = os.sep
	adminServer_name=domainProperties.getProperty('wls.admin.name')
	hostname_raw=domainProperties.getProperty('wls.admin.Hostname')
	hostname=hostname_raw.split('.')[0].upper()
	domainServ=domainProperties.getProperty('wls.domain.serv')
	keystoreType=domainProperties.getProperty('wls.domain.serv.keystore.type')
	protected_pkg_root_loc=domainProperties.getProperty('wls.domain.serv.rootDir')
	protectedJksDir=domainProperties.getProperty('wls.domain.serv.protectedDir')
	#print(separator, hostname, domainServ, protected_pkg_root_loc, protectedJksDir)
	keystoreDir=protected_pkg_root_loc+separator+hostname+separator+domainServ+separator+protectedJksDir
	
	PROTECTED_READER=keystoreDir+"/../protectedreader"
	PROTECTED_PROPS_FILE=keystoreDir+"/"+domainServ+"/_protected.cfg"
	PLAIN_TEXT_KEYS_TO_BE_DECRYPTED_VALUE="encrypted_keystore_passphrase,encrypted_weblogic_keystore_passphrase"
	BASE64_KEYS_TO_BE_DECRYPTED_VALUE="encrypted_auth_key"
	servAuthcode=domainProperties.getProperty('base.domain.serv.authCode.password')
	os.environ["AUTHCODE"] = servAuthcode
	
	msTrustJKSName=domainProperties.getProperty('wls.domain.serv.jks.ms.Trust.name')
	msTrustJKSPassword=domainProperties.getProperty('wls.domain.serv.jks.ms.Trust.password')
	msIdentityJKSName=domainProperties.getProperty('wls.domain.serv.jks.ms.Identity.name')
	msIdentityJKSPassword=domainProperties.getProperty('wls.domain.serv.jks.ms.Identity.password')
	msprivateKeyAlias=domainProperties.getProperty('wls.domain.serv.jks.ms.alias.name')
	msprivateKeyPhrase=domainProperties.getProperty('wls.domain.serv.jks.ms.alias.password')

	asTrustJKSName=domainProperties.getProperty('wls.domain.serv.jks.as.Trust.name')
	asTrustJKSPassword=domainProperties.getProperty('wls.domain.serv.jks.as.Trust.password')
	asIdentityJKSName=domainProperties.getProperty('wls.domain.serv.jks.as.Identity.name')
	asIdentityJKSPassword=domainProperties.getProperty('wls.domain.serv.jks.as.Identity.password')
	asprivateKeyAlias=domainProperties.getProperty('wls.domain.serv.jks.as.alias.name')
	asprivateKeyPhrase=domainProperties.getProperty('wls.domain.serv.jks.as.alias.password')

	msIdentityJKS=keystoreDir+separator+msIdentityJKSName
	msTrustJKS=keystoreDir+separator+msTrustJKSName
	asIdentityJKS=keystoreDir+separator+asIdentityJKSName
	asTrustJKS=keystoreDir+separator+asTrustJKSName
	
	RETURN_VALUE_CMD = PROTECTED_READER+" "+domainServ+" "+PROTECTED_PROPS_FILE+" "+PLAIN_TEXT_KEYS_TO_BE_DECRYPTED_VALUE+" "+BASE64_KEYS_TO_BE_DECRYPTED_VALUE
	RETURN_VALUE_OUT = os.popen(RETURN_VALUE_CMD).read()

	AS_PASSPHRASE_CMD = "return_value=\""+RETURN_VALUE_OUT+"\" ; echo $return_value | sed \"s/^.*encrypted_weblogic_keystore_passphrase=//;s/^[[:space:]]*//;s/[[:space:]].*$//\""
	MS_PASSPHRASE_CMD = "return_value=\""+RETURN_VALUE_OUT+"\" ; echo $return_value | sed \"s/^.*encrypted_keystore_passphrase=//;s/^[[:space:]]*//;s/[[:space:]].*$//\""
	
	#AS_PASSPHRASE_OUT = os.popen(AS_PASSPHRASE_CMD).read()
	#MS_PASSPHRASE_OUT = os.popen(MS_PASSPHRASE_CMD).read()
	
	if os.path.exists(PROTECTED_PROPS_FILE):
		AS_PASSPHRASE_OUT = os.popen(AS_PASSPHRASE_CMD).read()
		MS_PASSPHRASE_OUT = os.popen(MS_PASSPHRASE_CMD).read()
		msTrustJKSPassword=MS_PASSPHRASE_OUT
		msIdentityJKSPassword=MS_PASSPHRASE_OUT
		msprivateKeyPhrase=MS_PASSPHRASE_OUT
		asTrustJKSPassword=AS_PASSPHRASE_OUT
		asIdentityJKSPassword=AS_PASSPHRASE_OUT
		asprivateKeyPhrase=AS_PASSPHRASE_OUT
		
	
    	try:
		startEditSession()
        	serversList=cmo.getServers()
        	for each_server in serversList:
            		svrName=each_server.getName()
            		if svrName.find(adminServer_name) == -1:
				print "Configuring SSL for "+str(svrName)
                		cd('/Servers/' + svrName)
                		cmo.setKeyStores(keystoreType)
                		#Set Keystore
                		cmo.setCustomIdentityKeyStoreFileName(msIdentityJKS)
                		cmo.setCustomIdentityKeyStoreType('JKS')
                		set('CustomIdentityKeyStorePassPhrase', msIdentityJKSPassword)
                		#Set Trustore
                		cmo.setCustomTrustKeyStoreFileName(msTrustJKS)
                		cmo.setCustomTrustKeyStoreType('JKS')
                		set('CustomTrustKeyStorePassPhrase', msTrustJKSPassword)
                		##SSL....
                		cd('/Servers/' + svrName + '/SSL/' + svrName)
                		cmo.setServerPrivateKeyAlias(msprivateKeyAlias)
                		set('ServerPrivateKeyPassPhrase', msprivateKeyPhrase)
			if svrName.find(adminServer_name) != -1:
				print "Doing AdminServer Changes...."
                                cd('/Servers/' + svrName)
                                cmo.setKeyStores('CustomIdentityAndCustomTrust')
                                #Set Keystore
                                cmo.setCustomIdentityKeyStoreFileName(asIdentityJKS)
                                cmo.setCustomIdentityKeyStoreType('JKS')
                                set('CustomIdentityKeyStorePassPhrase', asIdentityJKSPassword)
                                #Set Trustore
                                cmo.setCustomTrustKeyStoreFileName(asTrustJKS)
                                cmo.setCustomTrustKeyStoreType('JKS')
                                set('CustomTrustKeyStorePassPhrase', asTrustJKSPassword)
                                ##SSL
                                cd('/Servers/' + svrName + '/SSL/' + svrName)
                                cmo.setServerPrivateKeyAlias(asprivateKeyAlias)
                                set('ServerPrivateKeyPassPhrase', asprivateKeyPhrase)
		saveAndActivateChanges()
		print "Done SSl COnfig..."
	except Exception, e:
        	print 'Error in configurring SSL for...\n'
        	print e
        	dumpStack()
        	discardChanges()	

#	__startAdminServerwithScript(domainProperties)
