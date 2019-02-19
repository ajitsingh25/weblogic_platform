
try:
	from weblogic.management.security.authentication import UserEditorMBean
except ImportError:
	UserEditorMBean = None


#=======================================================================================
# Load required modules
#=======================================================================================

try:
    commonModule
except NameError:
    execfile('wlst/common.py')

def createUser(username, password, description, authenticator):
    log.info("Creating a user : " + str(username) + ". Authenticator is " + str(authenticator))
    atnr=cmo.getSecurityConfiguration().getDefaultRealm().lookupAuthenticationProvider(str(authenticator))
    atnr.createUser(username,password,description)
    print "Created user successfully"
    
def addUserToGroup(username,groupname,authenticator):
    log.info("Adding a user : " + str(username) + " to group " + groupname + ". Authenticator is " + str(authenticator))
    atnr=cmo.getSecurityConfiguration().getDefaultRealm().lookupAuthenticationProvider(str(authenticator))
    atnr.addMemberToGroup(groupname,username)
    log.info("Done adding a user")

def createGroup(groupname, description, authenticator):
    log.info("Creating a group : " + str(groupname) + " with a description of " + str(description) + ". Authenticator is " + str(authenticator))
    atnr=cmo.getSecurityConfiguration().getDefaultRealm().lookupAuthenticationProvider(str(authenticator))
    if int(atnr.groupExists(groupname)) == 0:
    	atnr.createGroup(groupname,description)
    	log.info("Created group successfully")

def removeUser(username, authenticator):
    log.info("Removing user : " + str(username) + ". Authenticator is " + str(authenticator))
    atnr=cmo.getSecurityConfiguration().getDefaultRealm().lookupAuthenticationProvider(str(authenticator))
    if int(atnr.userExists(username)) == 1:
    	atnr.removeUser(username)
    	log.info("Removed user successfully")

#==============================================================================
# createUsers
#
# Creates all additional users configured in properties file.
#==============================================================================
def createUsers(resourcesProperties):
	allUsers = resourcesProperties.getProperty('security.users')
	if not allUsers is None and len(allUsers) > 0:
		#connectAdminServerOverSSL(resourcesProperties)
		userList = allUsers.split(',')
		for newUser in userList:
			userPrefix = 'security.user.' + newUser + '.'
			userName = resourcesProperties.getProperty(userPrefix + 'username')
			userPassword = resourcesProperties.getProperty(userPrefix + 'password')
			userDescription = resourcesProperties.getProperty(userPrefix + 'description')
			authenticator = resourcesProperties.getProperty(userPrefix + 'authenticator')
			groupName=resourcesProperties.getProperty(userPrefix + 'groupname')
			if not authenticator is None:
				createUser(userName, userPassword, userDescription, authenticator)
				addUserToGroup(userName,groupName,authenticator)
			else:
				createUser(userName, userPassword, userDescription, 'DefaultAuthenticator')
				addUserToGroup(userName,groupName,'DefaultAuthenticator')
		#disconnect()
		#print "Disconnected to admin server"
