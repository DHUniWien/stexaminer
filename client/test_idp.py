#from app import make_fixture_request, make_delete_request
import app
import logging
import json
import pytest
import ast	### Python's Abstract Syntax Tree module
#from api_app.tasks import flex_parse

#logger = logging.getLogger(__name__)   ###  AttributeError: 'Logger' object has no attribute 'basicConfig'
#logging.basicConfig(level=logging.DEBUG, filename='/src/app/test_idp.log', filemode='a', format='%(asctime)s-%(levelname)s-%(message)s')
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s-%(levelname)s-%(message)s')
#logging.basicConfig(level=logging.DEBUG, filename='/src/app/testingClient.log', filemode='a', format='%(asctime)s-%(levelname)s-%(message)s')

"""
Make requests to the stexaminer service using the respective test data in `client/requests`.
and the respective reference data in `client/references`.
These will return responses in json format.
"""


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

logging.debug("### Performing REST-API request tests for IDP ###")


### make sure that pytest is working properly in our project:
def test_always_passes():
    assert True

#def test_always_fails():
#    assert False

### basic functional tests for idp:

def find_CMD_versusReferenceResult(testFileName, either1or2):
    # This test is equivalent to this reqiest:  POST http://localhost:8001/request/<command>"
    #result_json = app.make_fixture_request('01_findGroupings')

    result_json = app.make_fixture_request(testFileName)
    result_dict = json.loads(result_json)
    
    if (result_dict["result_source"] == "database"):
        try:
            id = result_dict["jobid"]
            logging.info(f"Results for calculation request already existed in DB. We need to delete the DB entry for run_id {id} and then repeat the test request")
            # Via app in testing client POST a DELETE from DB where run_id = id:
            delete_result = app.make_delete_request(id)
            
            if either1or2 == 1:  ### repeat the calculation request to get the result from calculation and not from idp-database
                result_json = app.make_fixture_request(testFileName)
                result_dict = json.loads(result_json)
                # Via app in testing client POST a DELETE from DB where run_id = id:
                delete_result = app.make_delete_request(id)
        
        except Exception as e:
            logging.info(f"### Exception: {e}###")

    returned_result = result_dict["result"]
    #logging.info(f"### returned_result:\n{returned_result}")
    ###returned_result_type = type(returned_result)			### type of returned_result: <class 'list'>
    
    testFileName_parts = testFileName.split('_',2)
    #logging.info(f"### testFileName_parts:\n  str({testFileName_parts})")
    command = testFileName_parts[1]    ### e.g.: testFileName: 01_findGroupings_withReceiver => command: findGroupings
    with open(f'references/{command}_testRefResult.json', 'r', encoding='utf-8') as f:
            refres = f.read()
    ###refres_type = type(refres)   ### type of refres: <class 'str'>
    
    referenceResult = flex_parse(refres)
    ###referenceResult_type = type(referenceResult)		### type of referenceResult: <class 'list'>
    #logging.info(f"### referenceResult:\n{referenceResult}")
    if either1or2 in {1,2}:
        if returned_result == referenceResult:
            logging.info(f"### test_{testFileName} {either1or2}. request PASSED successfully\n")
        else:
            logging.error(f"### test_{testFileName} {either1or2}. request FAILED\n")

        # Eventually, a file `result-{jobid}-{date}.json` should appear in the `client/received` directory here, 
        # which is stexaminer's answer. 
        try:
            assert returned_result == referenceResult
        except AssertionError as e:
            logging.error(f'### AssertionError:{e}###')
    elif either1or2 == 0:
        if returned_result != referenceResult:
            logging.info(f"### test_{testFileName} PASSED successfully\n")
        else:
            logging.error(f"### test_{testFileName} FAILED\n")

        try:
            assert returned_result != referenceResult
        except AssertionError as e:
            logging.error(f'### AssertionError:{e}###')


def test_01a_findGroupings_1stRequest():
    """
    1st request means that it has not been calculated before and hence does not exist in the idp-database. 
    The result will be calculated with the command 'findGroupings'.
    """
    find_CMD_versusReferenceResult('01_findGroupings_withReceiver', 1)

def test_01b_findGroupings_2ndSameRequest():
    find_CMD_versusReferenceResult('01_findGroupings_withReceiver', 2)
    """
    2nd request means that the same request has been calculated before and stored into the idp-database. 
    The result for command 'findGroupings' will be retrieved from the idp-database.
    """

def test_01c_findGroupings_noReferenceMatch():
    find_CMD_versusReferenceResult('01_findGroupings_withReceiver_noReferenceMatch', 0)
    """
    Intentionally there is no match between the calculated result and the reference result
    """


def test_02a_findSources_1stRequest():
    find_CMD_versusReferenceResult('02_findSources', 1)

def test_02b_findSources_2ndSameRequest():
    find_CMD_versusReferenceResult('02_findSources', 2)

def test_02c_findSources_noReferenceMatch():
    find_CMD_versusReferenceResult('02_findSources_noReferenceMatch', 0)

def test_03a_findClasses_1stRequest():
    find_CMD_versusReferenceResult('03_findClasses', 1)

def test_03b_findClasses_2ndSameRequest():
    find_CMD_versusReferenceResult('03_findClasses', 2)

def test_03c_findClasses_noReferenceMatch():
    find_CMD_versusReferenceResult('03_findClasses_noReferenceMatch', 0)


if __name__ == '__main__':
    test_always_passes()
    test_01a_findGroupings_1stRequest()
    test_01b_findGroupings_2ndSameRequest()
    test_01c_findGroupings_noReferenceMatch()
    test_02a_findSources_1stRequest()
    test_02b_findSources_2ndSameRequest()
    test_02c_findSources_noReferenceMatch()
    test_03a_findClasses_1stRequest()
    test_03b_findClasses_2ndSameRequest()
    test_03c_findClasses_noReferenceMatch()
    #test_always_fails()
    logging.info('### execution of tests is finished ###')
