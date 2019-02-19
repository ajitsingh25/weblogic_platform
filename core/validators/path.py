
from java.io import File

def run(config):
    result = True
    enum = config.keys()
    # The list of properties that we currently identify as the ones that need a path value against it.
    pathprops=["wls.oracle.home","obpm.home","wls.domain.dir","wls.domain.javahome",".log.rotationDir",".httplog.rotationDir","wls.template."]
    wrongprops=[]
    while enum.hasMoreElements():
        key = enum.nextElement()
        for pathprop in pathprops:
        	if key.find(pathprop)>-1 and len(config.getProperty(key))>1 and config.getProperty(key).find("/")==-1:
				
        		wrongprops.append(key)
        		        		
    if len(wrongprops)>0:
    	log.error("")
       	log.error("The following properties expects a path as its value.Please provide a valid path for this property. If you are on Windows operating system please consider changing your path seperating character from \\ to /")
       	for wrongprop in wrongprops:
       		print "	"+wrongprop+"\n"
       	return False
        		   
    return result
