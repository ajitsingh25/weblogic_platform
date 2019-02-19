
from java.util import Vector, Collections
from java.lang import String

def run(config):
    """Display the config as a fully resolved set of properties"""
    print '\nConfiguration properties are:'
    v = Vector(config.keySet())
    Collections.sort(v)
    it = v.iterator()
    while (it.hasNext()):
       element = it.next();
       if (String(element.lower()).endsWith('.password')):
           printValue = '****'
       else:
           printValue = config.get(element)

       print '   ' + element + "=" + printValue
    print '\n'