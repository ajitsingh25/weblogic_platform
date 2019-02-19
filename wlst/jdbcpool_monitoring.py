

def create_html_dir(listx, alertHTML):
	#alertHTML=monitoringHome+'alert_email.html'
	f = open(alertHTML,'wt')
	[f.write("<tr><td>%s</td><td>%s</td><td>%s</td><td>%d</td><td>%d</td><td>%d</td><td>%s</td></tr>" % (ed['DomainName'] ,ed['ServerName'] , ed['DSName'] , ed['ActiveConnectionsCurrentCount'] ,ed['ActiveConnectionsHighCount'] , ed['maxCapacity'], ed['State'] )) for ed in listx]
	f.close()

def checkPool(config):
	dixJDBC = {}
	monitoringHome=config.getProperty('ConfigNOW.home')+'/core/commands/ant/resources/monitoring/'
	alertHTML=monitoringHome+'alert_email.html'
	poolThreshold=80
	allJDBCResources = cmo.getJDBCSystemResources()
	if (len(allJDBCResources) > 0):
		for jdbcResource in allJDBCResources:
			dsname1 = jdbcResource.getName()
			dsResource = jdbcResource.getJDBCResource()
			dsMaxCap = dsResource.getJDBCConnectionPoolParams().getMaxCapacity()
			if dsname1 not in  dixJDBC:
				dixJDBC[dsname1] = {}
				dixJDBC[dsname1]['maxCapacity']= dsMaxCap
			
	servers=domainRuntimeService.getServerRuntimes()
	if (len(servers) > 0):
		for each_server in servers:
			svrName=each_server.getName()
			serverState=each_server.getState()
			if serverState == 'RUNNING':
				jdbcServiceRuntime = each_server.getJDBCServiceRuntime()
				dataSourcesRT = each_server.getJDBCServiceRuntime().getJDBCDataSourceRuntimeMBeans()
				if (len(dataSourcesRT) > 0):
					for dataSource in dataSourcesRT:
						dsname2=dataSource.getName()
						dixJDBC[dsname2]['DomainName']= config.getProperty('ConfigNOW.configuration')
						dixJDBC[dsname2]['ServerName']= svrName
						dixJDBC[dsname2]['DSName']= dsname2
						dixJDBC[dsname2]['ActiveConnectionsCurrentCount']= dataSource.getActiveConnectionsCurrentCount()
						dixJDBC[dsname2]['ActiveConnectionsHighCount']= dataSource.getActiveConnectionsHighCount()
						dixJDBC[dsname2]['State']= dataSource.getState()
					
	listx = [{ 'DomainName':v['DomainName'],'ServerName':v['ServerName'],'DSName':v['DSName'],'ActiveConnectionsHighCount':v['ActiveConnectionsHighCount'],'maxCapacity' : v['maxCapacity'], 'ActiveConnectionsCurrentCount':v['ActiveConnectionsCurrentCount'], 'State':v['State']} for v in dixJDBC.itervalues() if 'ActiveConnectionsCurrentCount' in v and v['ActiveConnectionsCurrentCount'] >= 0 and round((round(v['ActiveConnectionsCurrentCount'], 1)/round(v['maxCapacity'], 1))*100, 0) >= round(poolThreshold, 1)]
	if len(listx) > 0:
		create_html_dir(listx, alertHTML)
		
