
import sys

from org.apache.log4j import Logger

def setup():
    sys.stdout = StdLogger('stdout')

class StdLogger:
    def __init__(self, name):
        self.logger=Logger.getLogger(name)
        
    def write(self, s):
        print_log=1
        
        if s=='\n':
            print_log=0
        if 'Error: cd() failed' in s:
            print_log=0
        if 'No element' in s:
            print_log=0            
        if 'Error: runCmd() failed.' in s:
            print_log=0
        if 'No nested element' in s:
            print_log=0            
                        
        if print_log>=1:
            self.logger.info(s)