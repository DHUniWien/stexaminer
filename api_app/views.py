import subprocess
from . import settings
from django.views import View
from django.http import Http404
from django.http import HttpResponse
from django.http import HttpResponseRedirect
from django.http import HttpResponseNotFound
from django.http import HttpResponseBadRequest
from django.http import JsonResponse
import json
from rest_framework.decorators import api_view
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from datetime import datetime
from . models import Calc, Results
from . execute_calc import run_add, run_calc
import re
import codecs
import logging

logging.basicConfig(level=logging.DEBUG, file='/home/idp/logs/View.log', filemode='a', format='%(asctime)s-%(levelname)s-%(message)s')
logging.info('Starting logging into this View.log\n')
with open('/home/idp/logs/view.log', 'a') as f:
		f.write("\n Start write-appending into this view file\n")

@method_decorator(csrf_exempt, name='dispatch')
class CalcRequest(View):
    def post(self, request):
        logging.info('CalcRequest View called \n')
        req = json.loads(request.body.decode("utf-8"))
        ret_path = req.get('return_path')   ### for the testing client: ret_path = "/result" 
        ret_host = req.get('return_host')   ### for the testing client: ret_host = 'client:8001'  ## or 'http://client:8001'  
        idp_content = req.get('content')
        req_calcType = None
        req_calcType = idp_content.get('command')      #### one of these: findGroupings / findClasses / findSources
        if not ((req_calcType == "findGroupings") or (req_calcType == "findClasses") or (req_calcType == "findSources")):
            if req_calcType == None:
                error_msg = "Please provide one of these commands / calculation types: findGroupings / findClasses / findSources"
            else:
                error_msg = "Command '" + req_calcType + "' is not possible. \n \
                             Please provide one of these commands / calculation types: findGroupings / findClasses / findSources"
            return JsonResponse({"error": error_msg}, status=201)
      
        groups = idp_content.get('groupings') 
        # groups example:
        #  [[['A', 'C', 'D', 'F', 'H', 'P', 'S', 'T'], ['E', 'K', 'Q']],
        #   [['A', 'F', 'H', 'K', 'P', 'S'], ['C', 'D', 'E', 'Q', 'T']],
        #   [['A', 'C', 'E', 'F', 'H', 'K', 'T'], ['D', 'P', 'Q', 'S']]]
        
        stem_string = idp_content.get('graph') 
        # stemma-string example:
        #'digraph stemma {   2 [ class=hypothetical ];   3 [ class=hypothetical ];   4 [ class=hypothetical ];   
        #    5 [ class=hypothetical ];   7 [ class=hypothetical ];   B [ class=hypothetical ];   G [ class=hypothetical ];
        #   "α" [ class=hypothetical ];   "γ" [ class=hypothetical ];   "δ" [ class=hypothetical ];   A [ class=extant ];
        #    C [ class=extant ];   D [ class=extant ];   E [ class=extant ];   F [ class=extant ];   H [ class=extant ];
        #    K [ class=extant ];   P [ class=extant ];   Q [ class=extant ];   S [ class=extant ];   T [ class=extant ];
        #    2 -> B;   2 -> C;   3 -> F;   3 -> H;   4 -> 5;   4 -> D;   5 -> 7;   5 -> K;   5 -> Q;   7 -> E;   7 -> G;
        #    B -> P;   B -> S;   "α" -> A;   "α" -> T;   "α" -> "δ";   "γ" -> 3;   "γ" -> 4;   "δ" -> 2;   "δ" -> "γ"; }'
        
        calc_data = {
            'input_data': idp_content,    ### raw
            'calculation_type': req_calcType,
            'calc_start': datetime.now(),
            'calc_end': datetime.now(),
            'calc_status': settings.STATUS_CODES['not_started'],
            'error_msg': "",
            'warning_msg': "",
            'finished': False,
            'result_path': ""
        }

        calc_instance = Calc.objects.create(**calc_data)     ### store calc_data in DB
        ci = Calc.objects.get(id=calc_instance.id)
        ci.calc_start = datetime.now()
        ci.calc_status = settings.STATUS_CODES['running']

        # dedicated elements saving schema:  obj.save(update_fields=['field_1', 'field_2']) 
        ci.save(update_fields=['calc_status', 'calc_start'])

        result = None
        result = run_calc(d=idp_content, c=req_calcType, obj_id=calc_instance.id, h=ret_host, p=ret_path) 

        ### commented out because this is probably better done in tasks.py/MyCalcTask:
        #ci.calc_end = datetime.now()
        #ci.calc_status = settings.STATUS_CODES['finished']
        #ci.finished = True
        #ci.save(update_fields=['calc_status', 'calc_end', 'finished'])


        ### result example for algorithm/req_calcType = "findGroupings":
        ### 'result: [[[["2","3","4","A","B","C","D","F","H","P","S","T","u03b1","u03b3","u03b4"],["5","7","E","G","K","Q"]],true],
        ###          [[["A","F","H","K","P","S"],["C","D","E","Q","T"]],false],
        ###          [[["A","C","E","F","H","K","T"],["D","P","Q","S"]],false]]\n'   

        if (result == None):
            return JsonResponse({"Feedback ":"The calculation is ongoing, please try again later"}, status=201)
        else:
            result = result.rstrip('\n') ### remove trailing newline
            result = result.split(":", 1) ### split at ':' after 'result';       1: do no further splits
            
            res_trees = json.loads(result[1])
            tree_count = len(res_trees)

            c = 0
            while c < tree_count:                    ### don't want to just check: "while tree_count"  would store res_data in reverse order into DB later

                res_data = {
                    'calc_id': calc_instance,        ### foreign key towards the Calc table; cannot be just an int.
                    'algorithm': req_calcType,
                    'stemmastring': stem_string,
                    'grouping': groups[c],           ### input grouping
                    'result': res_trees[c]           ### result grouping 
                }
                result_record = Results.objects.create(**res_data)   ### store res_data in DB; create new record
                c += 1
            

            return JsonResponse({"Your result ":str(result)}, status=201)



@api_view(['GET'])
def jobstatus(request, run_id):	
	if request.method == 'GET':
		try:
			algo_run = Calc.objects.get(id = run_id)
		except:		
			error_message = "There was no calculation with id " + str(run_id)
			response = HttpResponse(error_message)
			response.status_code = 400
			return response

		# Build basic response 
		msg = {
			'jobid': algo_run.id,
			'status': algo_run.calc_status,
			'command': algo_run.calculation_type,
			'start_time': str(algo_run.calc_start)
			}

		if algo_run.calc_status == settings.STATUS_CODES['running']:
			msg['result'] = "The calculation is ongoing, please try again later"
			return HttpResponse(json.dumps(msg))

		if algo_run.calc_status == settings.STATUS_CODES['finished']:
			# read result from file:
			with open(algo_run.result_path, mode='r') as f:
				result = json.load(f)
			# add response fields:
			msg['result'] = result
			msg['end_time'] = str(algo_run.calc_end)

			### 2bclarified: Shall we include a warning content in the answer, if it exists?
			###   could set/unset it via parameter "hide_warnings = True/False"
			### The warnings usually come from the external idp app and give e.g. infos like this:
			# Warning: Derived sort Manuscript for variable x. At findClasses.idp:22:19
			# Warning: Verifying and/or autocompleting structure SClass
			# Warning: Sort Variant in structure SClass has an empty interpretation.
			# Warning: Sort Manuscript in structure SClass has an empty interpretation.

			#if algo_run.warning_msg != None:
			#	msg['warning_msg'] = algo_run.warning_msg

			return HttpResponse(json.dumps(msg))

		if algo_run.calc_status == settings.STATUS_CODES['failure']:
			# add response fields:
			msg['result'] = algo_run.error_msg  ### 2bclarified: Shall the result field contain the error info according 
												### to the white paper for stemweb?; we could also use an error field
			msg['end_time'] = str(algo_run.calc_end)
			return HttpResponse(json.dumps(msg))


@method_decorator(csrf_exempt, name='dispatch')
class AddRequest(View):
    def post(self, request):
        ### related request example:
        ### curl -X POST -H "Content-Type: application/json" http://127.0.0.1:8000/add-items/ -d "{\"x\":\"4\",\"y\":\"8\"}"

        #data = json.loads(request.body.decode("utf-8"))
        body_unicode = request.body.decode('utf-8')
        body_data = json.loads(body_unicode)
        x = body_data['x']
        y = body_data['y']
        #result = run_add(x,y)
        result = run_add(int(x),int(y))
        return JsonResponse({"result": result}, status=201)

