
import sys

def getPassword(domainProperties, propertyName, msg):
	error=0
	
	password=domainProperties.getProperty(propertyName)
	prompt=domainProperties.getProperty('password.prompt')
	
	if password is None or len(password)==0:
		if prompt:
			if  not password:
				dont_match=1
				while dont_match:
					print 'Please enter ' + msg + ': '
					password1=raw_input()
					print 'Confirm ' + msg + ': ' 
					password2=raw_input()
					if password1==password2:
						dont_match=0
					else:
						print 'PASSWORDS DO NOT MATCH'
				domainProperties.setProperty(propertyName,password1)    
		else:
			log.error('Please verify ' + propertyName + ' property exists in configuration.')
			error=1
	else:
		log.debug(propertyName + ' property is valid.')
        
	if error:
		sys.exit()
        