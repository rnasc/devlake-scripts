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
connUrl = "http://10.124.70.137:443/api/plugins/{}/connections" 
scopesUrl = "http://10.124.70.137:443/api/plugins/{}/connections/{}/scopes"
scopeUrl = "http://10.124.70.137:443/api/plugins/{}/connections/{}/scopes/{}"
scopeConfigUrl = "http://10.124.70.137:443/api/plugins/{}/connections/{}/scope-configs"
remoteScopesUrl = "http://10.124.70.137:443/api/plugins/{}/connections/{}/remote-scopes"
projectsUrl = "http://10.124.70.137:443/api/projects"
projectUrl = "http://10.124.70.137:443/api/projects/{}"
blueprintsUrl = "http://10.124.70.137:443/api/blueprints"
blueprintUrl = "http://10.124.70.137:443/api/blueprints/{}"
sonarqubeRemoteSearchUrl = "http://10.124.70.137:443/api/plugins/sonarqube/connections/{}/search-remote-scopes"

#Azure Connection
azurePAT = "{INSERIR O PAT}"
azureOrgId = "telefonica-vivo-brasil"
azureConnectionType = "azuredevops_go"

#SonarQube Connection
sonarqubePAT = "{INSERIR O PAT}"
sonarqubeEndpoint = "http://sonar-devops.redecorp.br/api/"
sonarqubeConnectionType = "sonarqube" 

#Scope Config Details
scopeConfigDefaultName = "shared-config"
scopeConfigDefaultDeploymentPatternRegex = "^[Dd]eploy\\s"
scopeConfigDefaultProductionPatternRegex = "^.*[Pp]rod.*"

#Blueprint Details
blueprintNameSufix = "-Blueprint"
blueprintMode = "NORMAL"
blueprintEnable = True
blueprintCronConfig = "0 0 * * *"
blueprintIsManual = False
blueprintSkipOnFail = True
blueprintTimeAfter = "2023-12-11T00:00:00-03:00"

def createOrUpdateConnection(connectionType, projectRef):
    queryParams = { "pageSize": 800, "page": 1 }
    # Call the Get Connection API
    responseConnection = session.get(connUrl.format(str(connectionType)), params=queryParams, auth=basic)
    # Converts the response to json
    page = responseConnection.json()
    # Filter the connections that starts with the projectRef
    filtrado = list(filter(lambda x: x["name"].startswith(projectRef), page))
    # If it does not exists, creates the connection and return its id.
    if len(filtrado) == 0:
        # Creates the data to be sent to the API
        createConnectionData = { "name": projectRef, "token" : azurePAT, "proxy" : "", "rateLimitPerHour" : 0}
        # Call the Create Connection API
        resptest = session.post(connUrl.format(str(connectionType)), data = json.dumps(createConnectionData), auth = basic)
        print(resptest.json())
        # Returns the id of the created connection
        return resptest.json()["id"]
    else:
        # Returns the id of the exising connection
        return filtrado[0]["id"]

def createOrUpdateSonarQubeConnection(projectRef):
    queryParams = { "pageSize": 800, "page": 1 }
    # Call the Get Connection API
    responseConnection = session.get(connUrl.format("sonarqube"), params=queryParams, auth=basic)
    # Converts the response to json
    page = responseConnection.json()
    # Filter the connections that starts with the projectRef
    filtrado = list(filter(lambda x: x["name"].startswith(projectRef), page))
    # If it does not exists, creates the connection and return its id.
    if len(filtrado) == 0:
        # Creates the data to be sent to the API
        createConnectionData = { "name": projectRef, "token" : sonarqubePAT, "proxy" : "", "rateLimitPerHour" : 0, "endpoint" : sonarqubeEndpoint}
        # Call the Create Connection API
        resptest = session.post(connUrl.format("sonarqube"), data = json.dumps(createConnectionData), auth = basic)
        # Returns the id of the created connection
        return resptest.json()["id"]
    else:
        # Returns the id of the exising connection
        return filtrado[0]["id"]

def createOrUpdateDefaultScopeConfig(connectionId, connectionType):
    # Creates de query param
    queryParams = { "search": scopeConfigDefaultName, "pageSize": 100, "page": 1 }
    # Call the Get Scope Config API
    resp1 = session.get(scopeConfigUrl.format(str(connectionType), str(connectionId)), params=queryParams, auth=basic)
    # Converts the response to JSON
    results1 = resp1.json()
    # If results1 is empty, creates the default scope config
    if not results1:
        # Creates the data to be sent to the API
        createScopeConfigData = {
                                    "entities": [ "CODE", "CODEREVIEW", "CROSS", "CICD" ],
                                    "name": scopeConfigDefaultName,
                                    "deploymentPattern": scopeConfigDefaultDeploymentPatternRegex,
                                    "productionPattern": scopeConfigDefaultProductionPatternRegex,
                                    "refdiff": { "tagsLimit": 10, "tagsPattern": "/v\\d+\\.\\d+(\\.\\d+(-rc)*\\d*)*$/" }
                                }
        # Call the Create Scope Config API
        respCreateScopeConfigData = session.post(scopeConfigUrl.format(str(connectionType), 
                                                    str(connectionId)), 
                                                    data = json.dumps(createScopeConfigData), 
                                                    auth = basic)
        # Returns the id of the created scope config
        return respCreateScopeConfigData.json()["id"]
    else:
        # Returns the id of the existing scope config
        return results1[0]["id"]

def getScopesAndLinkToConnection(connectionId, connectionType, projectRef):
    # Creates the query parameter
    queryParams = { "groupId": "{}/{}".format(azureOrgId, str(projectRef)), "pageSize": 800, "page": 1 }
    # Call the Get Remote Scopes API to get the remote scopes (repositories)
    respFull = session.get(remoteScopesUrl.format(str(connectionType), str(connectionId)), params=queryParams, auth=basic)
    # Converts the response to JSON and get the 'children' content
    resultsFull = respFull.json()["children"]
    # Call the Get Scopes API to get the scopes (repositories) already linked to the connection
    respPartial = session.get(scopesUrl.format(str(connectionType), str(connectionId)), params=queryParams, auth=basic)
    # Converts the response to JSON and get the 'scopes' content
    resultsPartial = respPartial.json()["scopes"]
    # Creates a list to store the remote scopes that will be returned.
    scopes = []
    # For each remote scope...
    for r in resultsFull:
        scopeId = ""
        # Check if the remote scope is already linked to the connection
        filtrado = list(filter(lambda x: x["scope"]["id"].startswith(r["id"]), resultsPartial))
        # If it is not linked, creates the remote scope
        if len(filtrado) == 0:
            testdata = {
                            "data": [
                                {
                                    "OrganizationId" : azureOrgId,
                                    "ProjectId": r["data"]["ProjectId"],
                                    "id": r["data"]["id"],
                                    "name": r["data"]["name"],
                                    "remoteUrl": r["data"]["remoteUrl"],
                                }
                            ]
                        }
            resptest = session.put(scopesUrl.format(str(connectionType),str(connectionId)), data = json.dumps(testdata), auth = basic)
            if(resptest.status_code == 200):
                scopeId = resptest.json()[0]["id"]
                print("{}-{}".format(resptest, scopeId))
            else:
                print("Falha na criação do Data Scope: {}".format(resptest.json()))
            
        else:
            scopeId = filtrado[0]["scope"]["id"]
        
        scopeF = list(filter(lambda x: x["scopeId"] == scopeId, scopes))
        if len(scopeF) == 0:
            scope = {'scopeId': scopeId}
            scopes.append(scope)
    return scopes

def getScopesAndLinkToSonarQubeConnection(connectionId, projectRef):
    # Creates the query parameter
    queryParams = { "search": "{}".format(str(projectRef)), "pageSize": 500, "page": 1 }
    # Call the Get Remote Scopes API to get the remote scopes (repositories)
    respFull = session.get(sonarqubeRemoteSearchUrl.format(str(connectionId)), params=queryParams, auth=basic)
    # Converts the response to JSON and get the 'children' content
    resultsFull = respFull.json()["children"]
    queryParamsPartial = { "searchTerm": "{}".format(str(projectRef)), "pageSize": 500, "page": 1 }
    # Call the Get Scopes API to get the scopes (repositories) already linked to the connection
    respPartial = session.get(scopesUrl.format(str("sonarqube"), str(connectionId)), params=queryParamsPartial, auth=basic)
    # Converts the response to JSON and get the 'scopes' content
    resultsPartial = respPartial.json()["scopes"]
    # Creates a list to store the remote scopes that will be returned.
    scopes = []
    # For each remote scope...
    for r in resultsFull:
        scopeId = ""
        # Check if the remote scope is already linked to the connection
        filtrado = list(filter(lambda x: x["scope"]["projectKey"].startswith(r["id"]), resultsPartial))
        # If it is not linked, creates the remote scope
        if len(filtrado) == 0:
            testdata = {
                            "data": [
                                {
                                    "projectKey": r["data"]["projectKey"],
                                    "name": r["data"]["name"],
                                    "qualifier": r["data"]["qualifier"],
                                    "visibility": r["data"]["visibility"],
                                    "lastAnalysisDate": r["data"]["lastAnalysisDate"],
                                    "revision": r["data"]["revision"]
                                }
                            ]
                        }
            resptest = session.put(scopesUrl.format(str("sonarqube"),str(connectionId)), data = json.dumps(testdata), auth = basic)
            scopeId = resptest.json()[0]["projectKey"]
            print("{}-{}".format(resptest, scopeId))
        else:
            scopeId = filtrado[0]["scope"]["projectKey"]

        scopeF = list(filter(lambda x: x["scopeId"] == scopeId, scopes))
        if len(scopeF) == 0:
            scope = {'scopeId': scopeId}
            scopes.append(scope)
    return scopes

def linkDefaultScopeConfigToScopes(connectionId, scopeConfigId, connectionType):
    # Creates the query parameters
    queryParams2 = { "blueprints": "false", "pageSize": 800, "page": 1 }
    # Call the Get Scopes API to get the scopes (repositories) linked to the connection
    resp2 = session.get(scopesUrl.format(str(connectionType),str(connectionId)), params=queryParams2, auth=basic)
    # Converts the response to JSON and get the 'scopes' content
    results2 = resp2.json()["scopes"]
    # For each item in the response...
    for r in results2:
        # Tries to link the default scope config to the scope
        try:
            # If the scope already has a scope config, prints a message and continues
            if(not (("scopeConfigId" in r["scope"]) and (r["scope"]["scopeConfigId"] != 0))):
                # Else, links the default scope config to the scope.
                testdata = {
                        "scope": 
                        {
                            "connectionId": r["scope"]["connectionId"],
                            "OrganizationId": r["scope"]["OrganizationId"],
                            "ProjectId": r["scope"]["ProjectId"],
                            "id": r["scope"]["id"],
                            "name": r["scope"]["name"],
                            "url": r["scope"]["url"],
                            "remoteUrl": r["scope"]["remoteUrl"],
                            "IsFork": r["scope"]["IsFork"],
                        },
                        "scopeConfigId": scopeConfigId
                }
                # Call the Scope API patching the scope with the scope config of the default id.
                resp3 = session.patch(scopeUrl.format(str(connectionType), str(connectionId), str(r["scope"]["id"])), data = json.dumps(testdata), auth=basic)
                print("Status Execução: {} - {}".format(resp3.status_code, resp3.json()))
        except Exception as e:
            print("Falha encontrada: {}. Prosseguindo com o próximo item...".format(e))

def createDevlakeProject(projectRef):
    queryParams = { "pageSize": 800, "page": 1 }
    # Call the Get Project API
    response = session.get(projectUrl.format(str(projectRef)), params=queryParams, auth=basic)
    # If it does not exists, creates the connection and return its id.
    if(response.status_code == 404):
        # Creates the data to be sent to the API
        createProjectData = {"name": projectRef, "description": "", "metrics": [{"pluginName": "dora", "pluginOption": "", "enable": True}]}
        # Call the Create Connection API
        resp = session.post(projectsUrl, data = json.dumps(createProjectData), auth = basic, headers = {'Content-type': 'application/json'})
        print("Projeto criado: " + resp.json()["name"])
        return resp.json()["name"]
    else:
        return response.json()["name"]

def createDevlakeBlueprintForProject(projectRef):
    # Creates de query param
    queryParams = { "pageSize": 800, "page": 1 }
    # Call the Get Blueprint API
    response = session.get(blueprintsUrl, params=queryParams, auth=basic)
    # Converts the response to json
    page = response.json()["blueprints"]
    # Filter the connections that starts with the projectRef
    filtrado = list(filter(lambda x: x["name"].startswith(projectRef), page))
    # If it does not exists, creates the connection and return its id.
    if not filtrado:
        # Creates the data to be sent to the API
        createBlueprintData = {
                                "name":"{}{}".format(projectRef, blueprintNameSufix),
                                "projectName": "{}".format(projectRef),
                                "mode": blueprintMode,
                                "enable": blueprintEnable,
                                "cronConfig": blueprintCronConfig,
                                "isManual": blueprintIsManual,
                                "skipOnFail": blueprintSkipOnFail,
                                "timeAfter": blueprintTimeAfter,
                                "labels": [ projectRef ],
                                "connections":[ ]
                            }
        # Call the Create Connection API
        resp = session.post(blueprintsUrl, data = json.dumps(createBlueprintData), auth = basic, headers = {'Content-type': 'application/json'})
        # print(resp.json())
        print("Blueprint criado: {}".format(resp.json()["id"]))
        return resp.json()["id"]
    else:
        return filtrado[0]["id"]

def updateBlueprint(blueprintId, connectionId, connectionType, scopes):
    queryParams = { "pageSize": 800, "page": 1 }
    response = session.get(blueprintUrl.format(str(blueprintId)), params=queryParams, auth=basic)
    blueprint = response.json()

    if(len(scopes) > 0):
        for scope in scopes:
            connection = list(filter(lambda x: x["connectionId"] == connectionId, blueprint["connections"]))
            if len(connection) == 0:
                blueprint["connections"].append({
                    "pluginName": connectionType,
                    "connectionId": connectionId,
                    "scopes": [ scope ]
                })
            else:
                scopeRead = list(filter(lambda x: x["scopeId"].startswith(scope["scopeId"]), connection[0]["scopes"]))

                if len(scopeRead) == 0:
                    connection[0]["scopes"].append(scope)
                else:
                    print("Scope {} já existe! Prosseguindo...".format(scope["scopeId"]))
                    continue
            
            dataConn = {
                "name": blueprint["name"],
                "projectName": blueprint["projectName"],
                "mode": blueprint["mode"],
                "plan": blueprint["plan"],
                "enable": blueprint["enable"],
                "cronConfig": blueprint["cronConfig"],
                "isManual": blueprint["isManual"],
                "beforePlan": blueprint["beforePlan"],
                "afterPlan": blueprint["afterPlan"],
                "labels": blueprint["labels"],
                "connections": blueprint["connections"],
                "skipOnFail": blueprint["skipOnFail"],
                "fullSync": blueprint["fullSync"],
                "skipCollectors": blueprint["skipCollectors"],
                "id": blueprint["id"],
            }
            # Patches blueprint with both azure connections and scopes
            resp = session.patch(blueprintUrl.format(str(blueprintId)), data = json.dumps(dataConn), auth=basic, headers = {'Content-type': 'application/json'})
            if(resp.status_code == 200):
                queryParams = { "pageSize": 800, "page": 1 }
                response = session.get(blueprintUrl.format(resp.json()["id"]), params=queryParams, auth=basic)
                blueprint = response.json()
                if(resp.status_code != 200):
                    print("Scope: {}".format(scope["scopeId"]))
                print("Status Execução: {}-{}.{}".format(resp.status_code, scope["scopeId"], resp))
            else:
                print("Falha ao realizar busca do Blueprint".format(resp.json()))

def run(projectRef):
    try:
        ### Creates the Principal Connection ###
        print("1. Working on Azure Project")
        # Creates or updates the connection. If it does not exist, creates it. Else, returns its id.
        connectionId = createOrUpdateConnection(azureConnectionType, projectRef)
        print("Done! Project '{}' Found!".format(connectionId))
        # Creates or updates the default Scope Config. If it does not exist, creates it. Else, returns its id.
        scopeConfigId = createOrUpdateDefaultScopeConfig(connectionId, azureConnectionType)
        # Fetches the remote scopes (repositories) and link them to the connection.
        scopes = getScopesAndLinkToConnection(connectionId, azureConnectionType, projectRef)
        # Link the Default Scope Config to the Scopes.
        linkDefaultScopeConfigToScopes(connectionId, scopeConfigId, azureConnectionType)

        ### Creates the SonarQube Connection ###   
        print("2. Working on SonarQube Project")
        # Creates or updates the connection. If it does not exist, creates it. Else, returns its id.
        sonarQubeConnectionId = createOrUpdateSonarQubeConnection(projectRef)
        print("Done! Project '{}' Found!".format(sonarQubeConnectionId))
        # Fetches the remote scopes (repositories) and link them to the connection.
        sonarQubeScopes = getScopesAndLinkToSonarQubeConnection(sonarQubeConnectionId, projectRef)

        ### Creates the Devlake Project ###
        print("3. Working on Devlake Project")
        # Creates a Devlake Project with the projectRef name.
        devLakeProject = createDevlakeProject(projectRef)
        print("Done! Devlake Project '{}' Found!".format(devLakeProject))

        ### Creates the Devlake Blueprint ###
        print("4. Working on Devlake Blueprint")
        # Creates a Devlake Blueprint for the projectRef name.
        blueprintId = createDevlakeBlueprintForProject(projectRef)
        # Updates Blueprint for Azure DevOps Connection
        updateBlueprint(blueprintId, connectionId, azureConnectionType, scopes)
        # Updates Blueprint for SonarQube Connection
        updateBlueprint(blueprintId, sonarQubeConnectionId, sonarqubeConnectionType, sonarQubeScopes)
        print("Done! Devlake Blueprint '{}' Found!".format(devLakeProject))
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