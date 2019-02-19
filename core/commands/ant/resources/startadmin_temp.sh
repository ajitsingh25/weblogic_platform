#!/bin/ksh
today=$(date +"%m-%d-%y-%H:%M:%S")

domainName=@@DOMAIN_NAME@@
domainHome=@@DOMAIN_HOME@@
adminserverName=@@ADMINSERVER_NAME@@
sharedDir=@@SHARED_DIR@@

DIRECTORY=$sharedDir/$domainName/logs/$adminserverName
if [ ! -d "$DIRECTORY" ]; then
	mkdir -p ${DIRECTORY}
fi

adminlog=${DIRECTORY}/${adminserverName}_${today}.log
echo -e "[INFO] $adminserverName startup log: $adminlog "
nohup $domainHome/$domainName/bin/startWebLogic.sh >> $adminlog &


