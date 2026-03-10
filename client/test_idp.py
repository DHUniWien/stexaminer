#from app import make_fixture_request, make_delete_request
import logging
import json
import pytest
import ast	### Python's Abstract Syntax Tree module
#import app
from idp_pytest_client import app

#logger = logging.getLogger(__name__)   ###  AttributeError: 'Logger' object has no attribute 'basicConfig'
#logging.basicConfig(level=logging.DEBUG, filename='/src/app/test_idp.log', filemode='a', format='%(asctime)s-%(levelname)s-%(message)s')
logging.basicConfig(level=logging.INFO, format='%(asctime)s-%(levelname)s-%(message)s')
#logging.basicConfig(level=logging.DEBUG, filename='/src/app/testingClient.log', filemode='a', format='%(asctime)s-%(levelname)s-%(message)s')

"""
Send requests to the stexaminer service using as source the respective test data in `client/requests`.
The stexaminer service returns responses in json format.

1st request means that it has not been calculated before and hence does not exist in the idp-database. 
    The result will be calculated with the given command (one of: findGroupings, findSources, findClasses)

2nd request means that the same request has been calculated before and was stored into the idp-database. 
    The result for the given command will be retrieved from the idp-database.   

Then compare the received result with the respective reference data in `client/references`.

testFileNames ending with '_noReferenceMatch' are *intended* not to produce the same result as the related reference data
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


### basic functional tests for idp:


@pytest.mark.parametrize(
    "testFileName, FirstOr2ndRequest_orNoMatch",
    [   ("01_findGroupings_withReceiver", 1),
        ("01_findGroupings_withReceiver", 2),
        ("01_findGroupings_withReceiver_noReferenceMatch", 0),
        ("02_findSources", 1),
        ("02_findSources", 2),
        ("02_findSources_noReferenceMatch", 0),
        ("03_findClasses", 1),
        ("03_findClasses", 2),
        ("03_findClasses_noReferenceMatch", 0),
    ],
    ids=["findGroupings_1st-request", "findGroupings_2nd-request", "findGroupings_NoMatchIntended", \
        "findSources_1st-request", "findSources_2nd-request", "findSources_NoMatchIntended", \
        "findClasses_1st-request", "findClasses_2nd-request", "findClasses_NoMatchIntended"]
)
def test_CompareCalculatedVersusReferenceResult(app, testFileName, FirstOr2ndRequest_orNoMatch):
    # These tests are equivalent to such reqiests:  POST http://localhost:8001/request/<command>"

    result_dict = app.make_fixture_request(testFileName)

    
    if (result_dict["result_source"] == "database"):
        try:
            id = result_dict["jobid"]
            if FirstOr2ndRequest_orNoMatch == 1:  ### repeat the calculation request to get the result from calculation and not from idp-database
                # Via app in testing client POST a DELETE from DB where run_id = id:
                delete_result = app.make_delete_request(id)
                #logging.info(f"delete_result: {delete_result}")
                logging.info(f"Results for calculation request already existed in DB. \n \
                                We deleted the DB entry for run_id {id} and now we repeat the calculation request")
                result_dict = app.make_fixture_request(testFileName)
            elif FirstOr2ndRequest_orNoMatch == 2:
                logging.info(f"Results for calculation request for run_id {id} were retrieved from the database")

        except Exception as e:
            logging.error(f"### Exception: {e}###")

    # Eventually, a file `result-{jobid}-{date}.json` should appear in the `client/received` directory here, 
    #     which is stexaminer's answer.

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


    if FirstOr2ndRequest_orNoMatch in {1, 2}:
        assert returned_result == referenceResult
    elif FirstOr2ndRequest_orNoMatch == 0:
        assert returned_result != referenceResult
