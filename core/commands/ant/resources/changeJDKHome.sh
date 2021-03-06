#!/bin/sh

#Script Execution Directory i.e Bin directory
SCRIPT_PATH=$(readlink -f $0)
SCRIPT_HOME=$(dirname $SCRIPT_PATH)

mserverHome=/x/web/gops/oracle/config/mserver
aserverHome=/x/web/gops/oracle/config/aserver
domainName=kana
JavaHome=/x/web/gops/oracle/product/jdk

umask 0002

BACKUP_SUFFIX="wp.bak"
FILE_EXT=(.sh .xml .properties)

export PATH=$JavaHome/bin:$PATH

function modifyFiles {
	## Modify files to reflect JDK symbolic links	
	EXTENTION=$1
	jdk_readlink=`readlink -f $JavaHome`
	CURRENT_JDK=`basename $jdk_readlink`
	JAVA_LINKNAME=`basename $JavaHome`
	if [ ! -z $mserverHome  -a -d $mserverHome ]; then
		for i in `find $mserverHome/$domainName -type f -name "*${EXTENTION}" -exec grep -il "$CURRENT_JDK" {} \;`
		do
			echo $i
			sed -i.${BACKUP_SUFFIX} "s/${CURRENT_JDK}/${JAVA_LINKNAME}/g" $i
		done
	fi

        if [ -d $aserverHome ]; then
                for i in `find $aserverHome/$domainName -type f -name "*${EXTENTION}" -exec grep -il "$CURRENT_JDK" {} \;`
                do
                        echo $i
                        sed -i.${BACKUP_SUFFIX} "s/${CURRENT_JDK}/${JAVA_LINKNAME}/g" $i
                done
        fi


}


#start modifying files
echo -e "Below WLS Files are going to be Updated to reflect JDK symlink.."
for ext in "${FILE_EXT[@]}"
do
	modifyFiles $ext
done

