from django.db import models
from . import settings

# Create your models here.

class Calc(models.Model):		### package models; class Model
	""" 		
	calc_start	: When run was started. Basically the time when this instance
				  was created.
		
	calc_end	: When run ended. This can mean either that run was stopped
				  by user or it ended normally
		
	finished	: Is the run finished already. For quick checking.
		
	calculation_type: findGroupings, findClasses, findSources
		
	input_data	: received Input data via REST-API

	result_path : path to resulting file of the run (in json format?)

	#request_id = models.AutoField(unique=True)			### intended to generate a unique id, but creates this: 
	###								### AssertionError: Model api_app.requested can't have more than one AutoField. 

	By default, Django gives each model the following field:
	id = models.AutoField(primary_key=True, **options)
	This is an auto-incrementing primary key.
	==> use this one instead of the above request_id		
	
	"""	
	input_data = models.CharField(max_length=4096)		
	calculation_type = models.CharField(max_length=20) 	
	calc_start = models.DateTimeField(auto_now_add = False )	### request time
	calc_end = models.DateTimeField(auto_now_add = False)
	calc_status = models.IntegerField(default = settings.STATUS_CODES['not_started'])
	error_msg = models.CharField(max_length = 2048, blank = True, default = '')
	warning_msg = models.CharField(max_length = 2048, blank = True, default = '')
	finished = models.BooleanField (default = False)
	result_path = models.CharField(max_length = 4096, blank = True, default = '')

	### https://stackoverflow.com/questions/2771676/django-datetime-issues-default-datetime-now
	

