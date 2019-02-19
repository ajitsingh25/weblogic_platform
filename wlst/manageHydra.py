# Connecting to WL server
execfile('wlst/common.py')

# Setting Hydra job schduler table to CLW_CLUSTER
def __setJobScheduler(configProperties):
	hydraTimer=configProperties.getProperty('hydra.Timer')
	hydraTargets=configProperties.getProperty('hydra.Target.Name')
	hydraDS=configProperties.getProperty('hydra.ds.Name')
		
	print "* Parameter [hydraTimer = " + hydraTimer + "]"

	try:
        	if not hydraTargets is None and len(hydraTargets)>0:
                	hydraTargetList = hydraTargets.split(',')
                	for target in hydraTargetList:
				startEditSession()
				print "setting schduler table..."+str(target)			
				cd('/')
			   	cd('/Clusters/%s' % (target))
			   	cmo.setJobSchedulerTableName(hydraTimer)
			   	cmo.setDataSourceForJobScheduler(getMBean('/JDBCSystemResources/GemsDS'))
			   	cmo.setDataSourceForAutomaticMigration(getMBean('/JDBCSystemResources/GemsDS'))
				saveAndActivateChanges()
				startEditSession()
			   	cd ('/Clusters/%s' % (target))
			   	cd ('/Machines')
			   	mach = cmo.getMachines()
			   	for tm in mach:
					machineName = tm.getName()
					cd ('/Clusters/%s' % (target))
					set('CandidateMachinesForMigratableServers',jarray.array([ObjectName('com.bea:Name=%s,Type=UnixMachine' % (machineName))], ObjectName))
				cd('/')
				saveAndActivateChanges()
				print "Done .. "+str(target)
	except Exception, e:
		print ":: ERROR ==> Caught exception while setting job scheduler table name >>"+str(e)
		stopEdit('y')


# Deleting Hydra job schduler table to CLW_CLUSTER  
def __deleteJobScheduler(configProperties):
	hydraTargets=configProperties.getProperty('hydra.Target.Name')

	try:
		startEditSession()
        	if not hydraTargets is None and len(hydraTargets)>0:
                	hydraTargetList = hydraTargets.split(',')
                	for target in hydraTargetList:
                        	print "deleting schduler table..."+str(target)
				cd('/')
				cd('/Clusters/%s' % (target))
				cmo.unSet('DataSourceForJobScheduler')
				cd('/')
		saveAndActivateChanges()
	except Exception, e:
		print ":: ERROR ==> Caught exception while deleting GemsDS DB target to clfw_cluster >>"+str(e)
		stopEdit('y')
