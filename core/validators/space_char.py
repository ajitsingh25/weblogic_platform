
import validation_helper as helper

def run(config):
    if validateSpaceCharacter(config):
        return False
    return True

def validateSpaceCharacter(domainProperties):

    error = 0

    if not domainProperties is None:
        enum = domainProperties.keys()
        while enum.hasMoreElements():
            key = enum.nextElement()
            value = domainProperties.getProperty(key)
            if not value is None and len(value)>0:
                if value.endswith(' '):
                    error = 1
                    log.error('Property ' + str(key) + ' contains the space character at the end of line.')

    return error
