'''
	Some utility functions to help algorithm runs, etc.
'''
import os
import string
import random
import logging

from django.conf import settings
from django.template.defaultfilters import slugify
from django.shortcuts import get_object_or_404


def id_generator(size=8, chars=string.ascii_uppercase + string.digits):
	''' Semiunique ID generator -- copypaste code.

		Source:	http://stackoverflow.com/questions/2257441/python-random-string-generation-with-upper-case-letters-and-digits

		size:	length of the random string. Default 8.
		chars:	set of chars from which the string is created

		Returns random string.
	'''
	return ''.join(random.choice(chars) for x in range(size))

"""

def validate_json(json_data, algo_id):
	''' Validate that json contains all the needed parameters 

	returns 2-tuple (boolean, error message). If boolean is true, json
	is valid, otherwise the error message informs what is missing.
	'''

	if 'userid' not in json_data: return (False, "No userid given.")
	if 'content' not in json_data: return (False, "No data key present")
	if 'content.groupings' not in json_data: return (False, "No groupings present")
	if 'content.graph' not in json_data: return (False, "No stemmastring present")
	if 'content.command' not in json_data: return (False, "No algorithm present")
	
	if 'return_host' not in json_data: return (False, "No return_host present")
	if 'return_path' not in json_data: return (False, "No return_path present")

	

	params = json_data['parameters']
	for arg in algorithm.args.all().filter(external = True):
		if arg.key in params:
			value = params[arg.key]
			if not validate_parameter(value, arg.value):
				return (False, "Parameter %s = %s had wrong type. Expected %s." %\
					(arg.key, value, arg.value))
		else:
			return (False, "No parameter %s present" % (arg.key))

	return (True, "")


def validate_parameter(value, param_type):
	''' Validate, that value can be converted safely into param_type. '''
	if param_type == "positive_integer":
		if type(value) == int:
			return value > 0
		else:
			return False
	if param_type == "integer":
		return type(value) == int
	if param_type == "float":
		return type(value) == float
	if param_type == "boolean":
		if type(value) == bool:
			return True
		else:
			return False
	if param_type == "string":
		return type(str(value)) == str
	return False
"""
