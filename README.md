# stexaminer
IDP3 based Stemma coherence calculation service, as used in Stemmaweb

This project uses as it's core the idp3 knowledge base system developed in at KU Leuven:
https://dtai.cs.kuleuven.be/pages/software/idp/idp
https://dtai.cs.kuleuven.be/pages/software/idp/try
The IDP-scripts for stemmatological usage have also been developed there

The Digital Humanities Group at the University of Vienna built around this idp3 core a Django web app with a REST-API towards Stemmaweb, using Celery for task queueing and including a database which stores the requests and results.
The whole application is distributed on 4 interworking Docker containers.

## Running the service

Stexaminer is a Python 3 / Django web app, with external dependencies on an SQL server and Redis. 

To run the service , first create a `.env` file according to the pattern found in `.env.example` in this directory, setting appropriate values for at least `STEX_DBENGINE`, `STEX_DBNAME`, `STEX_DBUSER`, `STEX_DBPASS`, and `STEX_SECRET_KEY`. You can then start the service with the provided docker-compose file, or manually.

If you are using Docker, you can now run the command `docker compose up` in this directory. Three containers should start:

- A MySQL container, running on `mysql:3306` and not open to the outside
- A Redis container, running on `redis:6379` and not open to the outside
- A STEXAMINER server, running on `idp:8000` and mapped to localhost:8000

If you run the command `docker compose --profile testing up` instead, an additional container will start:

- A STEXAMINER testing client, running on `client:8001` and mapped to localhost:8001.

If you wish to run the service independently and not containerised, what passes for setup guidance can be found in the `Dockerfile` in this directory.

## Using the service

It should now be possible to make requests to the STEXAMINER server, similar to the [guidelines in the white paper](https://stemmaweb.net/?p=58).
Without using the stexaminer testing client (see above), you can send to stexaminer the following requests  (e.g. from folder ~/path-to-stexaminer/stexaminer/client), if you have installed the http tool:
    http --json POST http://127.0.0.1:8000/calc-items/ < requests/01_findGroupings.json
    http --json POST http://127.0.0.1:8000/calc-items/ < requests/02_findSources.json
    http --json POST http://127.0.0.1:8000/calc-items/ < requests/03_findClasses.json
Stexaminer will return the calculation result in json format

Usually the requests are sent from stemmaweb to texaminer.
    
If you are running the stexaminer testing client, you can make the following requests to test stexaminer's functionality:
    curl -X POST http://localhost:8001/request/01_findGroupings
    curl -X POST http://localhost:8001/request/02_findSources
    curl -X POST http://localhost:8001/request/03_findClasses

They will make requests to the stexaminer service using the respective test data in `client/requests`. 
These will return responses in json format.


Eventually, a file `result-{jobid}-{date}.json` should appear in the `client/received` directory here, which is stexaminer's answer. This can also be called up with the command

    curl http://localhost:8001/query/{jobid}
    
e.g.:
    curl http://localhost:8001/query/1        
will return something like:

{
  "command": "findSources",
  "end_time": "2024-02-14 15:38:40.136074+00:00",
  "jobid": 1,
  "result": "[[[[\"2\",\"3\",\"4\",\"5\",\"7\",\"A\",\"F\",\"G\",\"K\",\"T\",\"u03b1\",\"u03b3\",\"u03b4\"],[\"B\",\"D\",\"P\",\"S\"],[\"C\",\"E\",\"H\"],[\"Q\"]],[\"B\",\"C\",\"D\",\"E\",\"H\",\"Q\",\"u03b1\"]]]\n",
  "start_time": "2024-02-14 15:38:39.847044+00:00",
  "status": 0
}
    
    
    
You can query the result + status of a calculation request for a certain jobid also via the web-browser with:
   http://localhost:8000/jobstatus/{jobid}/

e.g.:
   http://localhost:8000/jobstatus/1/
will return something like:
   
{"jobid": 1, "status": 0, "command": "findSources", "start_time": "2024-02-14 13:21:50.580176+00:00", "result": "[[[[\"2\",\"3\",\"4\",\"5\",\"7\",\"A\",\"F\",\"G\",\"K\",\"T\",\"u03b1\",\"u03b3\",\"u03b4\"],[\"B\",\"D\",\"P\",\"S\"],[\"C\",\"E\",\"H\"],[\"Q\"]],[\"B\",\"C\",\"D\",\"E\",\"H\",\"Q\",\"u03b1\"]]]\n", "end_time": "2024-02-14 13:22:10.907579+00:00"}
