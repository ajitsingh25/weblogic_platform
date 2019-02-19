#!/bin/sh


PLATFORM_HOME="/x/mytemp/asingh/wls_paas/platform"
DOMAIN_NAME="petkana"
ORACLE_HOME="/x/web/gops/oracle/product/wl12213"
MSERVER_DOMAIN_HOME="/x/web/gops/oracle/config/mserver"

TEMPLATE_HOME=$PLATFORM_HOME/custom/resources/secondary
unpack_domain() {
    if [ -d $MSERVER_DOMAIN_HOME/$DOMAIN_NAME ]; then
        echo 'REMOVING $MSERVER_DOMAIN_HOME/$DOMAIN_NAME '
        rm -rf $MSERVER_DOMAIN_HOME/$DOMAIN_NAME
    fi
    ${ORACLE_HOME}/oracle_common/common/bin/unpack.sh -domain=$MSERVER_DOMAIN_HOME/$DOMAIN_NAME -template=$TEMPLATE_HOME/${DOMAIN_NAME}.jar
}
unpack_domain
