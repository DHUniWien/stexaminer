from . tasks import ClassBasedAddingTask, adding_task, MyCalcTask, calc_run_finished, calc_run_error
from idp3_async_api_djproj.celery import Celery
from celery.result import AsyncResult
from celery import signature
import logging


logging.basicConfig(level=logging.INFO, file='/home/idp/logs/executeCalc.log', filemode='a', format='%(asctime)s-%(levelname)s-%(message)s')
def run_add(a,b):
    """
    a toy function to quickly check the basic usage of the celery framework for asynchronuous task execution
    """
    print ("\n########## execute_calc.py/run_add ##############\n")
    print(a,b)
    res = adding_task.apply_async((a,b))   ### async call needs to have redis server started!!
    #res = adding_task.apply((a,b))         ### sync call for debugging purpose
    print(res.status) # e.g.'SUCCESS'
    #print(res.id) # e.g. '432890aa-4f02-437d-aaca-1999b70efe8d'
    #res = AsyncResult(res.id,app=adding_task)
    a_synced_res = res.get()
    print('#################################### the asynced result is:  ', a_synced_res)
    return a_synced_res


def run_calc(**kwargs): 
    ### kwargs filled in views.py: d=data, c=req_calcType, obj_id=calc_id, h=ret_host, p=ret_path
    ### So far return_path and return_host are not yet received from stemmaweb, but they are prepared here
    ### in idp for later possible usage
    
    run_id = kwargs['obj_id']
    return_path = kwargs['p']
    return_host = kwargs['h']

    res = MyCalcTask.apply_async(kwargs = kwargs,
        link = calc_run_finished.signature(kwargs = {'run_id': run_id, 'return_host': return_host , 'return_path': return_path}) ,
        link_error = calc_run_error.signature(kwargs = {'run_id': run_id, 'return_host': return_host , 'return_path': return_path}))
    
    ### use sync call instead of async call for debugging purpose:
    #res = MyCalcTask.apply(kwargs = kwargs,
    #   link = calc_run_finished.signature(kwargs = {'run_id': run_id, 'return_host': return_host , 'return_path': return_path}) ,
    #   link_error = calc_run_error.signature(kwargs = {'run_id': run_id, 'return_host': return_host , 'return_path': return_path}))   

    #print(res.status)       ### e.g.: FAILURE, SUCCESS, PENDING
    #logging.info('##################### the asynced status is:  ', str(res.status), '+++++++++++++++++\n')

    if ((res.status == "FAILURE") or (res.status == "SUCCESS")):
        a_synced_res = res.get()
    elif (res.status == "PENDING"):  ### is the same as status STATUS_CODES[running] in settings.py
        a_synced_res = None
    else:  ### prepared for not yet discovered/received status; possibly to be handled differently
        a_synced_res = None
    return a_synced_res