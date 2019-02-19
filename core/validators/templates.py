

from java.io import File
import validation_helper as helper

def run(domainProperties):
    return helper.validateList(domainProperties, 'wls.templates')