#!/bin/sh

domainName=@@DOMAIN_NAME@@
aserverDomainHome=@@AS_DOMAIN_HOME@@
mserverDomainHome=@@MS_DOMAIN_HOME@@
sharedDir=@@SHARED_DIR@@
oracleHome=@@ORACLE_HOME@@
wlsName=@@WLS_NAME@@
wlsVersion=@@WLS_VERSION@@
JAVA_HOME=@@JAVA_HOME@@
today=$(date +"%m-%d-%y-%H:%M:%S")


WL_HOME=$oracleHome/$wlsName

NODEMGR_HOME=$oracleHome/oracle_common/common/nodemanager
export NODEMGR_HOME

if [ $wlsVersion = "wls12130" ]; then
	DOMAIN_HOME=$aserverDomainHome/$domainName
	JAVA_HOME="${JAVA_HOME}"
	export JAVA_HOME
else
	DOMAIN_HOME=$mserverDomainHome/$domainName
	#  Set JAVA_HOME for node manager
	. ${DOMAIN_HOME}/bin/setNMJavaHome.sh
fi

JAVA_OPTIONS="${JAVA_OPTIONS} -Dweblogic.RootDirectory=${DOMAIN_HOME} "
export JAVA_OPTIONS


${WL_HOME}/server/bin/stopNodeManager.sh
