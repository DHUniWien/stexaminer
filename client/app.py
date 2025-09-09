from flask import Flask, request
from datetime import date
import json
import requests as req
import logging

#logger.basicConfig(level=logging.DEBUG, filename='/src/app/testingClient.log', filemode='a', format='%(asctime)s-%(levelname)s-%(message)s')
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s-%(levelname)s-%(message)s')

app = Flask(__name__)
"""
A testing client app with RESTful API to send requests to the idp app and to receive the answers.
Code re-used (& slightly adapted) from the Stemweb testing client app
"""

#IDP_BASE = 'http://idp:8000'   ### for container
IDP_BASE = 'http://localhost:8000'   ### for host-computer

# Check that we are up
@app.get('/')
def index():
    return '<h1>Hello World!</h1>'


# return path; prepared for possible later usage, when stemmaweb will use & send return_host + return_path
@app.post('/result')
#@app.route("/result", methods=["POST", "GET"])
def receive_result():
    '''Just write the result we get to a file'''
    res = request.get_json()  # will return 400 if it isn't JSON
    runid = res['jobid']
    try:
        with open('received/result-%d-%s.json' % (runid, date.today()), 'w') as f:
            f.write(json.dumps(res, ensure_ascii=False))
    except IOError as e:
        app.logger.debug('File write error: %s ', e)
        return('File write error: %s' % e, 500)
    return('', 200)

def store_result(res):
    '''Write the result we get to a file'''
    if res.status_code == 200:
        r = res.json()
        runid = r['jobid']
    else:
        r = json.loads(res.text)  ### type(r) = <class 'dict'>   ,  type(res) = <class 'requests.models.Response'>
        runid = r['jobid']

    try:
        pathed_file = "received/result-" + str(runid) + "-" +str(date.today())
        app.logger.debug(pathed_file)
        #with open('received/result-%d-%s.json' % (runid, date.today()), 'w') as f:
        with open(pathed_file, 'w') as f:
            f.write(json.dumps(r, ensure_ascii=False))
            app.logger.info('Received result is stored into file received/result-%d-%s.json' % (runid, date.today()) )
    except IOError as e:
        app.logger.debug('File write error during saving the result: %s ',  e)
    return pathed_file


@app.get('/query/<jobid>')
def query_job(jobid):
    '''Query a given job ID to see if it finished'''
    r = req.get('%s/jobstatus/%s/' % (IDP_BASE,jobid))
    return _r2flask(r)


# Make one of the test requests
@app.post('/request/<fixid>')
def make_fixture_request(fixid):
    '''Send the content of the appropriate request to the idp server'''
    fixfile = 'test-requests/%s.json' % fixid
    app.logger.debug('Got fixture file %s' % fixfile)

    with open(fixfile, encoding='utf-8') as f:
        fixdata = json.load(f)
    app.logger.debug('Loaded the fixture data')
    r = req.post('%s/%s/' % (IDP_BASE, 'calc-items'), json=fixdata)
    app.logger.debug("Made the request")
    #result_path = store_result(r)
    #return result_path
    return _r2flask(r)

@app.post('/delete_request/<run_id>')
def make_delete_request(run_id):
    ''' request to delete all records in IDP-database for the given run_id'''
    r = req.post('%s/delete_from_database/%s/' % (IDP_BASE,run_id))
    app.logger.debug(f"Sent the delete request for database record with run_id {run_id}")
    return _r2flask(r)


def _r2flask(r):
    '''Return a Flask response object from a Requests one'''
    app.logger.debug("Got requests response object with status %d" % r.status_code)
    if r.status_code == 200:
        ### return r.json() ##### created json decoding errors during some pytests
        return (r.text)
    else:
        #return r.text, r.status_code           ### r.status_code not needed by / not useful for test_idp
        return ((r.text).replace('\\"', ''))

# send delete_from_database request
@app.post('/delete_from_database/<jobid>')
def delete_result(jobid):
    r = req.get('%s/database/%s/' % (IDP_BASE,jobid))
    return _r2flask(r)



if __name__ == '__main__':
    app.run()



