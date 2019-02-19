
from org.apache.log4j import Logger, PropertyConfigurator

True=1
False=0

log=Logger.getLogger('validation')

def invalid_property_error_msg(propertyName, propertyValue):
    log.error('Property ' + str(propertyName) + ' with value of ' + str(propertyValue) + ' is invalid.')

def required_property_error_msg(propertyName):
    log.error('Required property ' + str(propertyName) + ' does not exist.')

def malformed_list_error_msg(propertyName):
    log.error('Property list ' + str(propertyName) + ' is malformed.')

def invalid_boolean_error_msg(propertyName):
    log.error('Boolean property ' + str(propertyName) + ' must have a value of true or false')

def invalid_number_error_msg(propertyName):
    log.error('Property ' + str(propertyName) + ' must have a numerical value')

def validateBoolean(config, propertyName):
    property=config.getProperty(propertyName)
    if property:
        if property.upper() != 'TRUE' and property.upper() != 'FALSE':
            invalid_boolean_error_msg(propertyName)
            return False
    	log.debug(propertyName + ' is valid')
    return True

def validateNumber(config, propertyName):
    property=config.getProperty(propertyName)
    if property:
        try:
            int(property)
        except ValueError:
            invalid_number_error_msg(propertyName)
            return False
        log.debug(propertyName + ' is valid')
    return True

def validateList(config, propertyName):
    property=config.getProperty(propertyName)
    if property:
        items=property.split(',')
        for item in items:
            if len(item)==0:
                malformed_list_error_msg(propertyName)
                return False
    return True
    
def listContainsValue(listProperty, value):
    if listProperty and value:
        list=listProperty.split(',')
        for item in list:
            if item==value:
                return True
    return False

def printHeader(text):
    line=getLine(text)
    log.debug(line)
    log.debug(text)
    log.debug(line)

def getLine(text):
    count=len(text)
    output = ''
    for i in xrange(0,count):
        output = output+'='
    return output