#!/bin/sh

#PLATFORM_HOME="/x/mytemp/asingh/wls_paas/platform"
PLATFORM_HOME="/x/mytemp/asingh/wls_paas/platform"
SCRIPT_HOME=$PLATFORM_HOME/custom/resources/monitoring
crontab -l > mycron
for i in `ls -lrt $SCRIPT_HOME/*.sh |awk '{print $9}'`
do
	if [ `grep "$i" mycron| wc -l` == 0 ]; then
		echo "Configuring cron for $i"
		echo "*/5 * * * *  $i > /dev/null 2>&1"  >> mycron
	else
		echo "$i is already configured in crontab"		
	fi
done
crontab mycron