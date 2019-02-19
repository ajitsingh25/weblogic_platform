#!/bin/sh

if [ -f setenv.sh ]; then
        rm setenv.sh
fi
./wlscli.sh install_jdk stage kana
./wlscli.sh install_weblogic stage kana
./wlscli.sh patch_apply stage kana
./wlscli.sh create_domain stage kana
./wlscli.sh setup_cron stage kana
#./wlscli.sh secondary stage kana
#/wlscli.sh configure_secondary_hosts state kana

