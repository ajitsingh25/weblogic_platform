import java.lang.Thread
#import common.distutils.config
execfile('wlst/common.py')
execfile('wlst/manageUserandGroups.py')
execfile('wlst/manageHydra.py')

def run(config):
	"""This is an example custom command, written in jython"""
	log.debug('-- in example.py')
#	getWLSMachineandandExecuteSecondary(config)
#	__createPegaConfigCommand(config)
#	createUsers(config)
#	__connectAdminServer(config)
	connectAdminServerOverSSL(config)
#	connect('gopsadmin','Gopsstg!','t3s://localhost:15102')
#	__setJobScheduler(config)
#	__deleteJobScheduler(config)
#	shutdown('adminserver_unify', 'Server', ignoreSessions='true', force='true', block='true')
#	disconnect()
	#   access properties like this -> config.getProperty('my.property')
	#redirect('NUL','false')
	#connect("gopsadmin", "Gopsstg!", "t3s://gcp2cpp177:11102")
	#redirect('NUL','true')


