

import validation_helper as helper

def run(cfg):
	valid=1
	
	helper.printHeader('[VALIDATING] nodemanager properties')
	
	if helper.validateBoolean(cfg,'nodemanager.secure.listener') is 0:
		valid=0		
	if helper.validateBoolean(cfg,'nodemanager.crashrecovery') is 0:
		valid=0		
	if helper.validateBoolean(cfg,'nodemanager.startscriptenabled') is 0:
		valid=0	
	if helper.validateBoolean(cfg,'nodemanager.domain.dir.sharing') is 0:
		valid=0
	if helper.validateNumber(cfg,'nodemanager.logcount') is 0:
		valid=0
	if helper.validateNumber(cfg,'nodemanager.loglimit') is 0:
		valid=0
	if helper.validateNumber(cfg,'nodemanager.listerner.port') is 0:
		valid=0
		
	return valid
		