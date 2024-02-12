from django.db import models
from . import settings

class Calc(models.Model):		### package models; class Model
	""" 		
	calc_start	: When run was started. Basically the time when this instance
				  was created.
		
	calc_end	: When run ended. This can mean either that the run failed or it ended normally.

	finished	: Is the run finished already?. For quick checking. (False, True)
		
	calculation_type: findGroupings, findClasses, findSources ; also referred to as "algorithm"
		
	input_data	: received input data via REST-API

	result_path : path to resulting file of the run (in json format?)

	#request_id = models.AutoField(unique=True)			### intended to generate a unique id, but creates this: 
	###								### AssertionError: Model api_app.requested can't have more than one AutoField. 

	By default, Django gives each model the following field:
	id = models.AutoField(primary_key=True, **options)
	This is an auto-incrementing primary key.
	==> use this one instead of the above request_id		
	
	"""	
	input_data = models.CharField(max_length=4096)		### raw or prepared?
	calculation_type = models.CharField(max_length=20) 	
	calc_start = models.DateTimeField(auto_now_add = True )	### request time
	calc_end = models.DateTimeField(auto_now_add = False)
	calc_status = models.IntegerField(default = settings.STATUS_CODES['not_started'])
	error_msg = models.CharField(max_length = 2048, blank = True, default = '')
	warning_msg = models.CharField(max_length = 2048, blank = True, default = '')
	finished = models.BooleanField (default = False)
	result_path = models.CharField(max_length = 4096, blank = True, default = '')

	def __str__(self):
		return self.name

	### https://stackoverflow.com/questions/2771676/django-datetime-issues-default-datetime-now
	

class Results(models.Model):
	"""
	Result table:
	Store one record per grouping rather than one record per request/calc

	e.g. for the calculated result:
	[[[[\"2\",\"3\",\"4\",\"A\",\"B\",\"C\",\"D\",\"F\",\"H\",\"P\",\"S\",\"T\",\"u03b1\",\"u03b3\",\"u03b4\"],[\"5\",\"7\",\"E\",\"G\",\"K\",\"Q\"]],true],
	[[[\"A\",\"F\",\"H\",\"K\",\"P\",\"S\"],[\"C\",\"D\",\"E\",\"Q\",\"T\"]],false],
	[[[\"A\",\"C\",\"E\",\"F\",\"H\",\"K\",\"T\"],[\"D\",\"P\",\"Q\",\"S\"]],false]]\n"}


	...  save the 1st record together with the stemma string in the record:
	[<STEMMASTRING>, [[\"2\",\"3\",\"4\",\"A\",\"B\",\"C\",\"D\",\"F\",\"H\",\"P\",\"S\",\"T\",\"u03b1\",\"u03b3\",\"u03b4\"],[\"5\",\"7\",\"E\",\"G\",\"K\",\"Q\"]],true]

	... then the 2nd record is:
	[<STEMMASTRING>, [[\"A\",\"F\",\"H\",\"K\",\"P\",\"S\"],[\"C\",\"D\",\"E\",\"Q\",\"T\"]],false]

	... and the next one is:
	[<STEMMASTRING>,  [[\"A\",\"C\",\"E\",\"F\",\"H\",\"K\",\"T\"],[\"D\",\"P\",\"Q\",\"S\"]],false]

	
	Example for a stemma-string:
	"digraph stemma {   2 [ class=hypothetical ];   3 [ class=hypothetical ];   4 [ class=hypothetical ];   
	5 [ class=hypothetical ];   7 [ class=hypothetical ];   B [ class=hypothetical ];   K [ class=hypothetical ];   
	\"α\" [ class=hypothetical ];   \"γ\" [ class=hypothetical ];   \"δ\" [ class=hypothetical ];   A [ class=extant ];
	  C [ class=extant ];   D [ class=extant ];   E [ class=extant ];   F [ class=extant ];   G [ class=extant ];
	  H [ class=extant ];   P [ class=extant ];   Q [ class=extant ];   S [ class=extant ];   T [ class=extant ];   
	  2 -> B;   2 -> C;   3 -> F;   3 -> H;   4 -> 5;   4 -> D;   5 -> 7;   5 -> K;   5 -> Q;   7 -> E;   7 -> G;   
	  B -> P;   B -> S;   \"α\" -> A;   \"α\" -> T;   \"α\" -> \"δ\";   \"γ\" -> 3;   \"γ\" -> 4;   \"δ\" -> 2;  
	   \"δ\" -> \"γ\"; }"

	"""
	calc_id = models.ForeignKey(Calc, on_delete=models.CASCADE)
	algorithm = models.CharField(max_length=20)
	stemmastring = models.CharField(max_length=2048)
	grouping = models.CharField(max_length=2048)
	result = models.CharField(max_length=4096) ### 2b checked: TEXT-field ?!

	def __str__(self):
		return self.name