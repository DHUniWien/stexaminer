from . tasks import ClassBasedAddingTask, adding_task, MyCalcTask, calc_run_finished, calc_run_error
from idp3_async_api_djproj.celery import Celery
from celery.result import AsyncResult
from celery import signature
import logging
from time import sleep
from . settings import WAIT_FOR_IDPRESULT


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

    #logging.info('###### the immediate asynced status is: %s %s', res.status, '#####')

    if res.status in ("FAILURE","SUCCESS"):
        logging.info('###### celery task %s for idp-run %s is finished', res.id, run_id)
        a_synced_res = res.get()
    elif (res.status == "PENDING"):  ### means the same as status STATUS_CODES[running] in settings.py
        sleep(WAIT_FOR_IDPRESULT)    ### Wait for the task to possibly finish after this (short) time
        if res.ready():
            logging.info('###### celery task %s for idp-run %s is finished', res.id, run_id)
            a_synced_res = res.get() ### fetch the result & status, etc,  again
        else:
            a_synced_res = None      ### the task is still ongoing
    else:  ### prepared for not yet discovered/received status
        logging.info('##### The not yet discovered status of the idp-run %s is: ', res.status)
        a_synced_res = None          ### possibly to be handled differently
    return a_synced_res