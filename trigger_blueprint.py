import requests
import logging
import json
import pprint

from azure.devops.connection import Connection
from msrest.authentication import BasicAuthentication
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
blueprintsUrl = "http://10.124.70.137:443/api/blueprints"
blueprintUrl = "http://10.124.70.137:443/api/blueprints/{}"
blueprintTriggerUrl = "http://10.124.70.137:443/api/blueprints/{}/trigger"

def triggerBlueprint(projectRefs):
    for projectRef in projectRefs:
        # Creates the query parameter
        queryParamsPartial = { "label": "{}".format(str(projectRef)), "pageSize": 500, "page": 1 }
        # Call the Get Scopes API to get the scopes (repositories) already linked to the connection
        blueprintResp = session.get(blueprintsUrl, params=queryParamsPartial, auth=basic)
        blueprints = blueprintResp.json()["blueprints"]

        if(len(blueprints) > 0):
            blueprint = blueprints[0]
            data = {
                    "skipCollectors": False,
                    "fullSync": False
                    }
            resp = session.post(blueprintTriggerUrl.format(blueprint["id"]), json=data, auth=basic)
            if(resp.status_code == 200):
                print("Blueprint triggered successfully.")
            else:
                print("Error triggering blueprint: {}".format(resp.text))

def run(projectRefs):
    try:
        ### Creates the Principal Connection ###
        triggerBlueprint(projectRefs)
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

run(
     [
        "ECVV - ECOSISTEMA VIVO"
     ])