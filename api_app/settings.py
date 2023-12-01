''''
	Settings for idp-application. 
'''
#from django import forms
from django.conf import settings



''' idp run status codes. '''
STATUS_CODES = {
	'not_started': -1,
	'running': 1,
	'finished': 0,
	'failure': 2
}