
from java.util import Vector, Collections
from java.lang import String

def run(config):
    """Display the config properties data linage"""
    print '\nData linage for this configuration is:'
    v = Vector(data_linage.keySet())
    Collections.sort(v)
    it = v.iterator()
    while (it.hasNext()):
        element = it.next();
        print '   [' + element + "]" 
        print '        Defined In     : '+ data_linage.get(element)
        print '\n'
    print '\n'