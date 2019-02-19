@echo off

set JAVA_HOME=c:\x\gops\oracle\product\jdk
@REM set JAVA_HOME=C:\x\Java\jdk1.7.0_151
set PATH=C:\WINDOWS\system32;C:\WINDOWS;%JAVA_HOME%\bin

set wlscli_cp=core/engine/lib/ant-contrib-1.0b1.jar;core/engine/lib/xmltask.jar;core/engine/lib/log4j-1.2.17.jar;core/engine/lib/commons-logging-1.2.jar;core/engine/lib/jsch-0.1.51.jar;core/engine/lib/ant.jar;core/engine/lib/ant-launcher.jar;core/engine/lib/ant-apache-log4j.jar;core/engine/lib/commons-codec-1.4.jar;core/engine/lib/commons-exec-1.1.jar;core/engine/lib/ant-nodeps.jar;core/engine/lib/catalina-ant.jar;core/engine/lib/tomcat-coyote.jar;core/engine/lib/tomcat-util.jar;core/engine/lib/tomcat-juli.jar;.;

setlocal

title wlscli

if %JAVA_HOME%.==. (
    @echo java not found. Please ensure that you have java installed and JAVA_HOME and PATH environment variables refers to correct JAVA installation directory.
    goto run_wlst

) 

:set_env
IF EXIST setenv.cmd CALL setenv.cmd

echo %classpath% | find "weblogic.jar" > nul

if errorlevel 1 goto run_jython

:run_wlst
@echo running wlst
java  -Xms1024m -Xmx1024m -classpath "%wlscli_cp%;%classpath%" -Duser.timezone='UTC' -Djava.security.egd=file:/dev/./urandom -Dpython.os=nt %ARGS% weblogic.WLST -skipWLSModuleScanning  core/engine/main.py %*
if errorlevel 3 goto set_env
goto :EOF

:run_jython
@echo running jython
%JAVA_HOME%\bin\java -version
%JAVA_HOME%\bin\java  -Xms1024m -Xmx1024m -classpath "./jython21.jar;%wlscli_cp%;%classpath%" -Duser.timezone='UTC' -Dpython.home=. org.python.util.jython core/engine/main.py %*
if errorlevel 2 goto set_env

endlocal
