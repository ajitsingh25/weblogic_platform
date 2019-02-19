def updateArgValues(currentArgsList, newArgsList):
    for y in newArgsList:
        if y.find('=') != -1:
            key_y=y.split('=')[0]
            for x in currentArgsList:
                if x.find('='):
                    key_x=x.split('=')[0]
                    if key_x == key_y:
                        print y+' '+x
                        kx,vx = x.split('=')
                        ky,vy = y.split('=')
                        if kx == ky and vx != vy:
                            #aList.remove(x)
                            index1=currentArgsList.index(x)
                            currentArgsList[index1] = y
    
def updateMemArgsValue(currentArgsList, newArgsList):
    for y in newArgsList:
        if y.find('-Xms')!=-1 or y.find('-Xmx')!= -1:
            key_y=y[0:4]
            value_y=y[4:]
            print 'key and values are :' +str(key_y)+' '+str(value_y)
            for x in currentArgsList:
                if x.find('-Xms')!= -1 or x.find('-Xmx')!= -1:
                    key_x=x[0:4]
                    value_x=x[4:]
                    print 'x and y are :' + str(x)+' '+str(y)
                    print 'key_y == key_x : ' +str(key_y)+' '+str(key_x) + ' '+str(value_y)+' '+str(value_x)
                    if key_y == key_x and value_x != value_y:
                        print "updating args"
                        index2=currentArgsList.index(x)
                        currentArgsList[index2] = y
                    

def updateSvrArg(domainProperties):       
    currentArgsList=[]
    vmArgumentsUpdateFlag=domainProperties.getProperty('base.wls.server.vmarguments.update')
    sslEnable=domainProperties.getProperty('wls.domain.ssl.enable')
    vmArguments=domainProperties.getProperty('base.wls.server.vmarguments')
    newArgsList=vmArguments.split()
    
    vmSSLArguments=domainProperties.getProperty('base.wls.server.ssl.vmarguments')
    SSLArgumentsList = vmSSLArguments.split()
    
    serversList = cmo.getServers()
    if len(serversList) >0:
        for each_server in serversList:
            svrName=each_server.getName()
            cd('/Servers/'+svrName+'/ServerStart/'+svrName)
            svrArguments=cmo.getArguments()
            currentArgsList = svrArguments.split()
            if not vmArgumentsUpdateFlag is None and vmArgumentsUpdateFlag.lower() == 'true':
                updateArgValues(currentArgsList, newArgsList)
                updateMemArgsValue(currentArgsList, newArgsList)
                for each_arg in newArgsList:
                    if each_arg not in currentArgsList:
                        currentArgsList.append(each_arg)
            if not sslEnable is None and sslEnable.lower() == 'true':
                for each_arg in SSLArgumentsList:
                    if each_arg not in currentArgsList:
                        currentArgsList.append(each_arg)
            converted_currentArgsList = ' '.join(map(str, currentArgsList))
            cmo.setArguments(converted_currentArgsList)