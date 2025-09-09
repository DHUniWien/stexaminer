#!/usr/bin/env python
# -*- coding: utf-8 -*-

import time

import datetime
import os
import logging
import subprocess
from subprocess import run
from . import settings
import re
import json
import ast	### Python's Abstract Syntax Tree module
import logging
import requests
from requests.exceptions import SSLError, HTTPError
from . import utils
import shutil
from . models import Calc

from django.db import connection, connections

from celery import Celery, Task, shared_task
from  idp3_async_api_djproj.celery import celery_app
app = Celery('tasks')

logging.basicConfig(level=logging.DEBUG, filename='/home/idp/logs/task.log', format='%(asctime)s-%(levelname)s-%(message)s')


@shared_task	
def calc_run_error(*args, run_id=None, return_host=None, return_path=None):	
	''' Callback task in case the requested calculation fails.  
		note these in *args packed arguments, handed over but NOT visible in the 
		call execute_calc.py/run_calc()/MyCalcTask.apply_async(kwargs = kwargs, ....)
		- args[0]:  various celery task request infos
		- args[1]:  exception / error text, e.g.:
			Worker exited prematurely: signal 11 (SIGSEGV) Job: 0.
		- args[2]: empty or Traceback
	'''
	#print ('######################## idp calculation failed :-(( ################################')
	#logging.basicConfig(level=logging.DEBUG, filename='/home/idp/logs/errorBack.log', format='%(asctime)s-%(levelname)s-%(message)s')
	logging.info("\n celery task request infos = {args[0]}, \n exception/error text = {args[1]} \n\n")
	logging.error ('######################## idp calculation failed :-(( ################################')
	logging.info ('args[0]=', args[0], '+++++++++++++++++' )
	logging.info ('args[1]=', args[1], '+++++++++++++++++' )

	try:
		ci = Calc.objects.get(id=run_id)			### django-DB connection can be lost after errors during calc run
	except OperationalError:
		logging.warn ('\n ############ close and restore damaged DB connections #############\n')
		for conn in connections.all():
			conn.close_if_unusable_or_obsolete()			### close damaged DB connections

		#cursor = connection.cursor()	### Will result in: jango.db.utils.InterfaceError: connection already closed
		
		connection.cursor().execute('SELECT 1;')			### restore DB connections

		### get object again from DB:
		ci = Calc.objects.get(id=run_id)

	if ci.calc_status == settings.STATUS_CODES['running']:
		error_message = args[1]
		if error_message == "":
			error_message ="errorBack calc_run_error() did not receive the error msg in args[1]"
		print (f"########  errMsg =  {error_message} ###")   ### will be logged as WARNING by ForkPoolWorker
		ci.calc_status = settings.STATUS_CODES['failure']
		ci.error_msg = error_message   ### for later usage in /views.py/jobstatus()
	else:							   ### else: status 'failure' was already set earlier
		error_message = ci.error_msg

	ci.calc_end = datetime.datetime.now()
	ci.save()
	
	ret = {
		'jobid': run_id,
		'statuscode': ci.calc_status,
		'start_time': str(ci.calc_start),
		'end_time': str(ci.calc_end),
		'result': error_message
		}
	

	if ((return_host!=None) & (return_path!=None)):  ### for later usage, if these 2 parameters are provided with the request

		# Does the return host have a schema defined?
		targeturl = return_host + return_path

		EXPLICIT_SCHEMA = return_host.startswith('https://') or return_host.startswith('http://')
		if EXPLICIT_SCHEMA:
			r = requests.post(targeturl, json=ret)
		else:
			# We will have to try both
			try:
				r = requests.post('https://%s' % targeturl, json=ret)
			except SSLError:
				r = requests.post('http://%s' % targeturl, json=ret)

		try: 
			r.raise_for_status()
		except HTTPError as e:
			logging.warn("Attempt to return response to %s got an error: %s" % (targeturl, e.message))




@shared_task
def calc_run_finished(*args, run_id=None, return_host=None, return_path=None):
	''' Callback task in case idp calculation finishes succesfully. '''

	try:
		logging.info ('reported errors or warnings:', args[1], '+++++++++++++++++' )
	except IndexError:   ### i.e. args[1] does not exist, because no errors occured
		#logging.info (f'######## No errors occured during calulation of run_id {run_id} ##########')
		pass

	if ((return_host!=None) & (return_path!=None)):  ### for later usage, if these 2 parameters are provided with the request

		try:
			ci = Calc.objects.get(id=run_id)			### django-DB connection can be lost after errors during calc run
		except OperationalError:
			logging.warn ('##### close and restore damaged DB connections #####')
			for conn in connections.all():
				conn.close_if_unusable_or_obsolete()			### close damaged DB connections

			#cursor = connection.cursor()	### Will result in: jango.db.utils.InterfaceError: connection already closed
			
			connection.cursor().execute('SELECT 1;')			### restore DB connections

			### get object again from DB:
			ci = Calc.objects.get(id=run_id)

		### already set at the end of MyCalcTask.run()
		#ci.calc_status = settings.STATUS_CODES['finished']
		#ci.calc_end = datetime.datetime.now()
		#ci.finished = True
		#ci.save(update_fields=['calc_status', 'calc_end', 'finished'])
	
		with open(ci.result_path, "r") as fp:
				#result = fp.read()
				calc_result = json.load(fp)

		ret = {
			'jobid': run_id,
			'statuscode': ci.calc_status,
			'start_time': str(ci.calc_start),
			'end_time': str(ci.calc_end),
			'result': calc_result
			}
		
		# Does the return host have a schema defined?
		targeturl = return_host + return_path
		EXPLICIT_SCHEMA = return_host.startswith('https://') or return_host.startswith('http://')
		if EXPLICIT_SCHEMA:
			r = requests.post(targeturl, json=ret)
		else:
			# We will have to try both
			try:
				r = requests.post('https://%s' % targeturl, json=ret)
			except SSLError:
				r = requests.post('http://%s' % targeturl, json=ret)

		try: 
			r.raise_for_status()
		except HTTPError:
			logging.warn("Attempt to return response to %s got an error: %d %s" % (targeturl, r.status_code, r.text))


def flex_parse(data):
    """
    Attempts to convert a string into a Python object using either JSON or ast.literal_eval.
    If the input is already a Python object, it is returned unchanged.
    """
    if not isinstance(data, str):
        # already a Python object
        return data

    # first try to convert a JSON data structure into a dictionary
    try:
        return json.loads(data)
    except json.JSONDecodeError:
        pass

    # then try to safely convert string-based data into Python object(s)
    try:
        return ast.literal_eval(data)
    except (ValueError, SyntaxError):
        pass

    # if parsing fails, return the original string
    return data


def remove_temp_files(directory_name):
	for file_name in os.listdir(directory_name):
		pathed_file = directory_name + file_name
		if ".idp" in file_name:			### *.idp script files
			os.remove(pathed_file)
		elif (file_name == "json.lua"):
			os.remove(pathed_file)	


class MyCalcTask(Task):
	def __init__(self, **kwargs):
		self.data = kwargs.pop('d', None)
		self.calctype = kwargs.pop('c', None)
		self.run_id = kwargs.pop('obj_id', None)
		logging.basicConfig(level=logging.DEBUG, file='/home/idp/logs/MyCalcTask.log', filemode='a', format='%(asctime)s-%(levelname)s-%(message)s')

	def run(self, **kwargs):
		self.__init__(**kwargs)
		self.uniq_id = utils.id_generator()					### e.g.: 'EPTUKTXQ'
		infilename = str(self.run_id) + "_indata.json" 
		results_dir = os.path.dirname("/home/idp/results")
		script_dir = "/home/idp/idp_scripts/" 
		unique_dir =  datetime.datetime.now().strftime("%Y%m%d-%H%M%S") + "-" + self.uniq_id	### e.g.: '20230116-171934-EPTUKTXQ'
		working_dir = os.path.join(results_dir, unique_dir, "")   ### the last path component is empty, hence a directory separator ('/') will 
																   ### be put at the end along with the concatenated value												
		os.mkdir(working_dir)
		os.chdir(working_dir)

		infilepath = os.path.join(working_dir, infilename)

		### copy idp scripts and lua file to working dir for temporary usage
		# fetch all files
		for file_name in os.listdir(script_dir):
			# construct full file path
			source = script_dir + file_name
			destination = working_dir + file_name
			# copy only files
			if os.path.isfile(source):
				shutil.copy(source, destination)

		dict_data = self.data
		with open(infilepath, "w") as fp:
			json.dump(dict_data, fp) 

		ctype = self.calctype

		"""
		### On Python 3.7 or higher, if we pass in capture_output=True to subprocess.run(), the CompletedProcess object returned by run() will 
		### contain the stdout (standard output) and stderr (standard error) output of the subprocess.
		#res = subprocess.run(command, capture_output=True, text=True, shell = True)  ### security caveat when using shell=True ?
		"""

		catcmd = 'cat '
		cmd2 = ' | idp -e "exec('
		cmd3 = ')" main.idp'
		command = catcmd + infilepath + cmd2 + ctype + cmd3

		# next 2 lines with waitcmd = TESTCASE: simulate long running calc and wait some time 
		# comment them out, if you are not running this TESTCASE
		#waitcmd = 'sleep 20; '
		#command = waitcmd + catcmd + infilepath + cmd2 + ctype + cmd3
		### End of TESTCASE		

		### Here we call the idp app as an external command line application:		
		res = subprocess.run(command, capture_output=True, text=True, shell = True)
		
		### Because subprocess.run() waits for the command to finish running before returning, we'll receive the entire contents 
		### of stdout and stderr as a whole only after the command has completed. If we need to stream output as it appears in real time,
		###  we can use subprocess.Popen instead.
		#return	(res.returncode, result, self.run_id)

		#logging.info('\n###### res.stdout of subprocess.run(): ===%s===#################\n', res.stdout )
		#logging.info('\n###### res.stderr of subprocess.run(): ===%s===#################\n', res.stderr )

		ci = Calc.objects.get(id=self.run_id)
		ci.calc_end = datetime.datetime.now()
		ci.finished = True
		match_err, match_warn = None, None
		match_err = re.search("[Ee]rror:", res.stderr)
		match_warn = re.search("[Ww]arning:", res.stderr)
		
		### Uncomment the next 2 lines for testcase: intended error here
		#match_err = True
		#res.stderr = " I am a testcase error\n including a warning line"
		### End of testcase: intended error here

		if res.returncode != 0:
			logging.error("Subprocess failed with return code %d: %s", res.returncode, res.stderr)
			raise Exception(f"Subprocess failed with code {res.returncode}: {res.stderr}")

		if match_err != None:
			answer = f"error: {res.stderr}"			
			ci.calc_status = settings.STATUS_CODES['failure']
			ci.error_msg = res.stderr
			ci.save(update_fields=['calc_status', 'error_msg', 'calc_end', 'finished'])
			logging.error(answer)
			#remove_temp_files(working_dir)  ### better keep them for a while for debugging
			raise Exception (answer)    ### sets the status of the MyCalcTask()-result [see execute_calc.py] to "FAILURE"

		if res.stdout.strip() == "" and res.stderr.strip() == "":
			logging.warning(f"Subprocess for run-id {self.run_id} succeeded but gave no output; that is suspicious.")

		if ((res.stderr == "") or match_warn or (res.stdout != "")):
			answer = res.stdout
			#print (f"original Task result type is: type({answer})")
			logging.info(f"original Task result for run_id {self.run_id}: {answer}")
			#print("original Task result for %s: %s", self.run_id, answer)
			parsed_answer = flex_parse(answer)
			logging.info(f"parsed Task result for run_id {self.run_id}: {parsed_answer}")
			#print("parsed Task result for %s: %s", self.run_id, parsed_answer)
			ci.calc_status = settings.STATUS_CODES['finished']	
			res_file = str(self.run_id) + "_result.json"	
			ci.result_path = os.path.join (working_dir, res_file)   ### maybe, later not needed, since results are stored in DB
			ci.save(update_fields=['calc_status', 'result_path', 'calc_end', 'finished'])
			if match_warn:
				ci.warning_msg = res.stderr	### 2bchecked: are warnings separated from errors?
				ci.save(update_fields=['warning_msg'])
				logging.warning(res.stderr)
			with open(ci.result_path, "w") as fp:
				###json.dump(res.stdout, fp)
				json.dump(parsed_answer, fp)

			### remove temporary script files; 
			### keep unique working_dir with in_data.json + result.json file; may be removed later as well since results are stored in database
			#remove_temp_files(working_dir)
			### ToCheck: remove input files?

			return(parsed_answer)
	

		
MyCalcTask = celery_app.register_task(MyCalcTask())



class ClassBasedAddingTask(Task):
	def __init__(self, *args, **kwargs):
		pass
		

	def run(self, *args, **kwargs):
		result = 0
		# Iterating over the Python args tuple
		for x in args:
			result += x

		time.sleep(result)
		print('############ ClassBasedAddingTasks result: ', result, '  #############################')
		return	result

ClassBasedAddingTask = celery_app.register_task(ClassBasedAddingTask())

#def adding_task(*args):
#@app.task
@shared_task
def adding_task(x,y):
		result = 0
		#for k in args:			
		#	result += int(k)
		# Iterating over the Python args tuple

		result = x + y
		#time.sleep(result)
		print('############ adding_tasks result: ', result, '  #############################')
		return	result

