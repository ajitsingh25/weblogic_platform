#!/bin/sh

#Script Execution Directory i.e Bin directory
SCRIPT_PATH=$(readlink -f $0)
SCRIPT_HOME=$(dirname $SCRIPT_PATH)

WLS_BINARY_HOME=$1
platformRootDir=$2
OracleBase=$3
OracleHome=$4
#WLS_INSTALL_JAR_FILE=$5
JavaHome=$5
WLS_RSP_FILE=$6
oraInvFile=$7
oraInventory=$8
WL_VERSION=$9
USER=${10}

WL_HOME=$OracleHome/wlserver

umask 0002

BACKUP_SUFFIX="wp.bak"
FILE_EXT=(.sh .xml .properties)

export PATH=$JavaHome/bin:$PATH

function verifyOraInventory() {
        if [ ! -d $oraInventory ]; then
                # If the directory does not exist, create it
                mkdir -p $oraInventory
                echo "[INFO] Creating $oraInventory"
                #If there is an error in creating the direcotry, abort
                if [ $? -ne 0 ]
                        then
                                echo ""
                                echo "[ERROR] in creating $oraInventory"
                                echo ""
                                exit -1
                fi
				
#                chown -R $USER:$USER $oraInventory
        else
                echo "[INFO] $oraInventory already exists, moving forward..."
        fi
}

function installBinary() {
	WLS_INSTALL_JAR_FILE=`cd $platformRootDir/../$WLS_BINARY_HOME;ls -lrt *.jar | awk '{print $9}'`
	if [[ ! -d $OracleBase ]]; then
		echo "[INFO] creating $OracleBase directory"
                mkdir -p $OracleBase
	fi

	if [[ ! -d $WL_HOME ]]; then
        	echo "[INFO] Install Weblogic Binary"
		if [ -f $JavaHome/bin/java ]; then
			/sbin/rngd -r /dev/urandom -o /dev/random -t 1
        		$JavaHome/bin/java -d64 -Djava.io.tmpdir=/tmp -jar $platformRootDir/../$WLS_BINARY_HOME/$WLS_INSTALL_JAR_FILE -silent -novalidation -force -invPtrLoc $oraInvFile -responseFile $WLS_RSP_FILE
				
		else
			echo "[ERROR] $JavaHome not found. Aborting ...."
			exit
		fi
	else
        	echo "[INFO] WLS is already installed  to $OracleHome, skiping.."
        	break
	fi
}

function modifyFiles {
	## Modify files to reflect JDK symbolic links	
	EXTENTION=$1
	jdk_readlink=`readlink -f $JavaHome`
	CURRENT_JDK=`basename $jdk_readlink`
	JAVA_LINKNAME=`basename $JavaHome`
	COUNT=`find $OracleHome -type f -name "*${EXTENTION}" -exec grep -il "$CURRENT_JDK" {} \; | wc -l`
	for i in `find $OracleHome -type f -name "*${EXTENTION}" -exec grep -il "$CURRENT_JDK" {} \;`
	do
		echo $i
		sed -i.${BACKUP_SUFFIX} "s/${CURRENT_JDK}/${JAVA_LINKNAME}/g" $i
	done
	TOTAL=`expr $TOTAL + $COUNT`
	export sum=$TOTAL
}



verifyOraInventory
installBinary

#start modifying files
echo -e "Below WLS Files are going to be Updated to reflect JDK symlink.."
for ext in "${FILE_EXT[@]}"
do
	modifyFiles $ext
done
