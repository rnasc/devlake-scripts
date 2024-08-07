import requests
import logging

from requests.adapters import HTTPAdapter
from requests.auth import HTTPBasicAuth
from urllib3.util.retry import Retry

session = requests.Session()
retry = Retry(connect=3, backoff_factor=0.5)
adapter = HTTPAdapter(max_retries=retry)
session.mount('http://', adapter)
session.mount('https://', adapter)

basic = HTTPBasicAuth('admin', 'admin')

#URLs
pipelinesUrl = "http://10.124.70.137:443/api/pipelines"
pipelineUrl = "http://10.124.70.137:443/api/pipelines/{}"

def deleteAllPipelines():
    # Creates the query parameter
    queryParamsPartial = { "pageSize": 10000, "page": 1 }
    # Call the Get Scopes API to get the scopes (repositories) already linked to the connection
    pipelineResp = session.get(pipelinesUrl, params=queryParamsPartial, auth=basic)
    pipelines = pipelineResp.json()["pipelines"]

    if(len(pipelines) > 0):
        print("Found {} pipelines.".format(len(pipelines)))
        for pipeline in pipelines:
            resp = session.delete(pipelineUrl.format(pipeline["id"]), auth=basic)
            if(resp.status_code == 200):
                print("Pipeline {} delete successfully.".format(pipeline["id"]))
            else:
                print("Error deleting pipeline: {}".format(resp.text))

def run():
    try:
        deleteAllPipelines()
    except session.exceptions.HTTPError as httpErr: 
            logging.error("Http Error: ", exc_info=httpErr)
    except session.exceptions.ConnectionError as connErr:
        logging.error("Error Connecting: ", exc_info=connErr)
    except session.exceptions.Timeout as timeOutErr: 
        logging.error("Timeout Error: ", exc_info=timeOutErr)
    except session.exceptions.RequestException as reqErr:
        logging.error("Something Else: ", exc_info=reqErr)
    except Exception as err:
        logging.error("Falha encontrada: {}.".format(err))
        raise(err)

run()