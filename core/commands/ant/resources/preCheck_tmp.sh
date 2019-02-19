#!/bin/sh

PLATFORM_HOME=@@CONFIG_HOME@@
pegaconfigBase=@@PEGACONFIG_BASE@@
oracleBase=@@ORACLE_BASE@@
wlsUser=@@USER@@
wlsGrp=@@GROUP@@
osUMASK=@@UMASK@@

		
function checkRoot(){
	# Make sure the script is running as root.
	if [ "$UID" -ne "0" ]; then
		echo "[ERROR] Pre-requiste steps has not done on this host."
		echo "[ERROR] Run $0 wirh root to comple pre-requiste. Try following"; echo "sudo su -";
		exit 9
	fi
}

function getOSUpdate() {
	checkRoot
	# get up to date
	echo "[INFO] Get System Up to Date"
	#yum upgrade -y
	echo "[INFO] System Updated"
}

function checkPlatformBase() {
	if [ ! -d $PLATFORM_HOME ]; then
		checkRoot
		echo "[INFO] Creating $PLATFORM_HOME Dir"
		umask $osUMASK
		mkdir -p $PLATFORM_HOME
		chown -R $wlsUser:$wlsGrp $oracleBase
		echo "[INFO] $PLATFORM_HOME Dir    		[OK]"
	else
		#checkRoot
		#chown -R $wlsUser:$wlsGrp $oracleBase
		echo "[INFO] $PLATFORM_HOME Dir    		[OK]"
	fi
}


function checkOracleBase() {
	if [ ! -d $oracleBase ]; then
		checkRoot
		echo "[INFO] Creating $oracleBase Dir"
		umask $osUMASK
		mkdir -p $oracleBase
		chown -R $wlsUser:$wlsGrp $oracleBase
		echo "[INFO] $oracleBase Dir    		[OK]"
	else
		#checkRoot
		#chown -R $wlsUser:$wlsGrp $oracleBase
		echo "[INFO] $oracleBase Dir    		[OK]"
	fi
}

function checkPegaconfigBase() {
	if [ ! -d $pegaconfigBase ]; then
		checkRoot
		echo "[INFO] Creating $pegaconfigBase Dir"
		umask $osUMASK
		mkdir -p $pegaconfigBase
		chown -R $wlsUser:$wlsGrp $pegaconfigBase
		echo "[INFO] $pegaconfigBase Dir    	[OK]"
	else
		#checkRoot
		#chown -R $wlsUser:$wlsGrp $pegaconfigBase
		echo "[INFO] $pegaconfigBase Dir    	[OK]"
	fi
}

function checkGrp() {
	#checkRoot
	if [ $(getent group $wlsGrp) ]; then
		echo "[INFO] $wlsGrp group    			[OK]"
	else
		checkRoot
		echo "[INFO] $wlsGrp group not found, creating."
		groupadd $wlsGrp
		echo "[INFO] $wlsGrp group    			[OK]"
	fi
}
		
function checkUsr() {
	#checkRoot
	if [ `getent passwd $wlsUser | wc -l` -eq 1 ]; then
		echo "[INFO] $wlsUser user    			[OK]"
	else
		checkRoot
		echo "[INFO] $wlsUser user not found, creating."
		useradd $wlsUser
		echo $wlsUser:$wlsUser | chpasswd
		echo "[INFO] $wlsUser user    			[OK]"
		checkGrp
		if getent group $wlsGrp | grep &>/dev/null "\b${username}\b"; then
			usermod -g $wlsUser $wlsGrp
		fi
		echo "[INFO] $wlsUser assigned to group $wlsGrp"
	fi
}	

checkUsr
checkPlatformBase
checkOracleBase
if [ ! -z $pegaconfigBase ];then
	checkPegaconfigBase
fi

