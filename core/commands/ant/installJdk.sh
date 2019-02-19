#!/bin/sh

##Installation script for setting up Java on Linux

#Script Execution Directory i.e Bin directory
SCRIPT_HOME="$(dirname $(readlink -f $0))"

WLS_BINARY_HOME=$1
UMASK=$2
JDK_VERSION=$3
ORACLE_BASE=$4
ORACLE_HOME=$5
USER=$6
#JAVA_DIST=$7
platformRootDir=$7
JAVA_INSTALL_HOME=$8
WL_VERSION=$9

WL_HOME=${ORACLE_HOME}/wlserver

JAVA_DIST=`cd $platformRootDir/../$WLS_BINARY_HOME;ls -lrt *.tar.gz | awk '{print $9}'`
#JAVA_INSTALL_HOME=${ORACLE_BASE}/product/$JDK_VERSION
JAVA_LINKNAME=jdk
JAVA_LINK_HOME=$JAVA_INSTALL_HOME/../$JAVA_LINKNAME

export PATH=$JAVA_HOME/bin:$PATH

#echo "$WLS_BINARY_HOME"
#echo $UMASK
#echo $JDK_VERSION
#echo $ORACLE_BASE
#echo $ORACLE_HOME
#echo $USER
#echo $JAVA_DIST


function install_jdk(){

        if [[ ! -f $platformRootDir/../$WLS_BINARY_HOME/$JAVA_DIST ]]; then
                        echo "[ERROR] Please specify the java distribution file (tar.gz)"
                        exit 1
        fi
        # Extract Java Distribution
        if [[ ! -d $JAVA_INSTALL_HOME ]]; then
                        mkdir -p $JAVA_INSTALL_HOME
                        cd $JAVA_INSTALL_HOME/..
                        echo "[INFO] Installing JDK ..."
                        tar -xzvf $platformRootDir/../${WLS_BINARY_HOME}/${JAVA_DIST} 1> /dev/null
                        return_code=$?
                        if [ "$return_code" != "0" ]; then
                                        echo "error while untar"
                                        exit $return_code
                        fi
                        echo "[INFO] JDK is extracted to $JAVA_INSTALL_HOME"
        else
                        echo "[INFO] JDK is already extracted to $JAVA_INSTALL_HOME, skiping jdk installation.."
                        break
        fi

        cd ${SCRIPT_HOME}


        if [ -L $JAVA_LINK_HOME ] ; then
                        if [ -e $JAVA_LINK_HOME ] ; then
                                        echo "[INFO] JDK Sym Link already created"
                        else
                                        echo "[WARNING] Link is broken. Fixing it .."
                                        echo "[INFO] Creating Link"
                                        cd $JAVA_INSTALL_HOME/..
                                        ln -sfn $JDK_VERSION $JAVA_LINKNAME
                                        cd $SCRIPT_HOME
                                        echo "[INFO] Broken Link is fixed now .."
                        fi
        elif [ -e $JAVA_LINK_HOME ] ; then
                        echo "[ERROR] $JAVA_LINK_HOME is Not a link. Aborting .."
                        echo "[ERROR] You can delete/mv $JAVA_LINK_HOME and retry the script."
                        exit 1
        else
                        echo "[WARNING] $JAVA_LINK_HOME Link is Missing. Fixing it .."
                        echo "[INFO] Creating Link"
                        cd $JAVA_INSTALL_HOME/..
                        ln -sfn $JDK_VERSION $JAVA_LINKNAME
                        cd $SCRIPT_HOME
                        echo "[INFO] $JAVA_LINK_HOME link created now..."
        fi

        if [ ! -f $JAVA_LINK_HOME/bin/java ]; then
                echo "[ERROR] Couldn't check the extracted directory. Please check the installation "
                exit 1
        fi

}



install_jdk

###END
