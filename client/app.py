from flask import Flask, request
from datetime import date
import json
import requests as req

app = Flask(__name__)
"""
A testing client app with RESTful API to send requests to the idp app and to receive the answers.
Code re-used (& slightly adapted) from the Stemweb app  
"""

IDP_BASE = 'http://idp:8000'

# Check that we are up
@app.get('/')
def index():
    return '<h1>Hello World!</h1>'


# Implement the return path
#@app.post('/result')
@app.route("/result", methods=["POST", "GET"])
def receive_result():
    '''Just write the result we get to a file'''
    res = request.get_json()  # will return 400 if it isn't JSON
    runid = res['jobid']
    try:
        with open('received/result-%d-%s.json' % (runid, date.today()), 'w') as f:
            f.write(json.dumps(res, ensure_ascii=False))
    except IOError as e:
        return('File write error: %s' % e.message, 500)
    return('', 200)


@app.get('/query/<jobid>')
def query_job(jobid):
    '''Query a given job ID to see if it finished'''
    r = req.get('%s/jobstatus/%s/' % (IDP_BASE,jobid))
    return _r2flask(r)


# Make one of the test requests
@app.post('/request/<fixid>')
def make_fixture_request(fixid):
    '''Send the content of the appropriate request to the idp server'''
    fixfile = 'requests/%s.json' % fixid
    app.logger.debug('Got fixture file %s' % fixfile)

    with open(fixfile, encoding='utf-8') as f:
        fixdata = json.load(f)
    app.logger.debug('Loaded the fixture data')
    r = req.post('%s/%s/' % (IDP_BASE, 'calc-items'), json=fixdata)
    app.logger.debug("Made the request")
    return _r2flask(r)


def _r2flask(r):
    '''Return a Flask response object from a Requests one'''
    app.logger.debug("Got requests response object with status %d" % r.status_code)
    if r.status_code == 200:
        return r.json()
    else:
        return r.text, r.status_code


if __name__ == '__main__':
    app.run()
    #app.run(ssl_context='adhoc') ### adhoc: use on-the-fly certificates, which are useful to quickly serve an 
                                  ### application over HTTPS without having to mess with certificates.
                                  ### need to install pyopenssl as additional dependency in your virtual environment:


