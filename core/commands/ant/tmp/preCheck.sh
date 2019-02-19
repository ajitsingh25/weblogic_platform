#!/bin/sh

pegaconfigBase=/x/web/gops
oracleBase=/x/gops/oracle
wlsUser=website
wlsGrp=website
osUMASK=0002

		
function checkRoot(){
	# Make sure the script is running as root.
	if [ "$UID" -ne "0" ]; then
		echo "[ERROR] You must be root to run $0. Try following"; echo "sudo su -";
		exit 9
	fi
}

function getOSUpdate() {
	# get up to date
	echo "[INFO] Get System Up to Date"
	#yum upgrade -y
	echo "[INFO] System Updated"
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
		checkRoot
		chown -R $wlsUser:$wlsGrp $oracleBase
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
		checkRoot
		chown -R $wlsUser:$wlsGrp $pegaconfigBase
		echo "[INFO] $pegaconfigBase Dir    	[OK]"
	fi
}

function checkGrp() {
	checkRoot
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
	checkRoot
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
#checkOracleBase
checkPegaconfigBase

