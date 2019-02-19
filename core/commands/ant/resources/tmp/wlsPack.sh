#!/bin/sh

PLATFORM_HOME="/x/mytemp/asingh/wls_paas/platform"
DOMAIN_NAME="petkana"
DOMAIN_HOME="/x/web/gops/oracle/config/aserver"
ORACLE_HOME="/x/web/gops/oracle/product/wl12213"

TEMPLATE_HOME=$PLATFORM_HOME/custom/resources/templates

pack_domain() {
    if [ -f $TEMPLATE_HOME/${DOMAIN_NAME}.jar ]; then
        echo 'REMOVING OLD TEMPLATE'
        rm -f $TEMPLATE_HOME/${DOMAIN_NAME}.jar
    fi
    echo 'PACKING DOMAIN'
    ${ORACLE_HOME}/oracle_common/common/bin/pack.sh -managed=true -domain=$DOMAIN_HOME/$DOMAIN_NAME -template=$TEMPLATE_HOME/${DOMAIN_NAME}.jar -template_name=${DOMAIN_NAME}
}
pack_domain
