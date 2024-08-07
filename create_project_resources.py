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

# def run():
#     try:
#         projects = getAzureProjects()
#         for project in projects:
#             ## Creates the Principal Connection ###
#             print("1. Working on '{}' Azure Project".format(project))
#             Creates or updates the connection. If it does not exist, creates it. Else, returns its id.
#             connectionId = createOrUpdateConnection(azureConnectionType, project.name)
#             Creates or updates the default Scope Config. If it does not exist, creates it. Else, returns its id.
#             scopeConfigId = createOrUpdateDefaultScopeConfig(connectionId, azureConnectionType)
#             Fetches the remote scopes (repositories) and link them to the connection.
#             scopes = getScopesAndLinkToConnection(connectionId, azureConnectionType, project.name)
#             Link the Default Scope Config to the Scopes.
#             linkDefaultScopeConfigToScopes(connectionId, scopeConfigId, azureConnectionType)
#             ## Creates the SonarQube Connection ###   
#             print("2. Working on SonarQube for '{}' Project".format(project))
#             Creates or updates the connection. If it does not exist, creates it. Else, returns its id.
#             sonarQubeConnectionId = createOrUpdateSonarQubeConnection(project.name)
#             print("Done! Project '{}' Found!".format(sonarQubeConnectionId))
#             Fetches the remote scopes (repositories) and link them to the connection.
#             sonarQubeScopes = getScopesAndLinkToSonarQubeConnection(sonarQubeConnectionId, project.name)
#             ## Creates the Devlake Project ###
#             print("3. Working on Devlake for '{}' Project".format(project))
#             Creates a Devlake Project with the projectRef name.
#             devLakeProject = createDevlakeProject(project.name)
#             ## Creates the Devlake Blueprint ###
#             print("4. Working on Devlake Blueprint for '{}' Project".format(project))
#             Creates a Devlake Blueprint for the projectRef name.
#             blueprintId = createDevlakeBlueprintForProject(project.name)
#             Updates Blueprint for Azure DevOps Connection
#             updateBlueprint(blueprintId, connectionId, azureConnectionType, scopes)
#             Updates Blueprint for SonarQube Connection
#             updateBlueprint(blueprintId, sonarQubeConnectionId, sonarqubeConnectionType, sonarQubeScopes)
#             print("All Done!")
#     except session.exceptions.HTTPError as httpErr: 
#             logging.error("Http Error: ", exc_info=httpErr)
#     except session.exceptions.ConnectionError as connErr:
#         logging.error("Error Connecting: ", exc_info=connErr)
#     except session.exceptions.Timeout as timeOutErr: 
#         logging.error("Timeout Error: ", exc_info=timeOutErr)
#     except session.exceptions.RequestException as reqErr:
#         logging.error("Something Else: ", exc_info=reqErr)
#     except Exception as err:
#         logging.error("Falha encontrada: {}.".format(err))
#         raise(err)

# def getProjectName(project):
#     return project.name

# def getAzureProjects():
#     try:
#         # Fill in with your personal access token and org URL
#         organization_url = "https://dev.azure.com/{}".format(azureOrgId)
#         # Create a connection to the org
#         credentials = BasicAuthentication("", azurePAT)
#         connection = Connection(base_url=organization_url, creds=credentials)
#         # Get a client (the "core" client provides access to projects, teams, etc)
#         core_client = connection.clients.get_core_client()
#         # Get the first page of projects
#         projectsList = core_client.get_projects()
#         # Sort projects by name
#         projectsList.sort(key=getProjectName)
#         for project in projectsList:
#             pprint.pprint(project.name)
#         return projectsList
#     except Exception as err:
#         logging.error("Falha encontrada: {}.".format(err))
#         raise(err)

# getAzureProjects()

run("ACRM - ACCOUNT_RECEIVABLE MGMT")
run("ADBB - AEM B2B")
run("ADCP - CAMUNDA")
run("ADCP - FLUTTER")
run("ADCP - JAVA")
run("ADCP - WEB")
run("AMDP - API Management Digital Plataform")
run("APPV - Framework-Brasil")
run("AXWY - API MANAGEMENT - AXWAY")
run("AXWY - ApiManagementCloud")
run("AXWY - ApiManagementOnPremise")
run("AZR4 - 4P AZURE")
run("BINV - BLUEPLANET INVENTORY")
run("BLMN - BILLING MGMT")
run("BSVN - BPM SAVVION")
run("CLMN - COLLECTION MGMT")
run("CMMR - COMMERCE")
run("CMOC - COMMERCIAL_OFFER CATALOG")
run("CNDF - Condor Financial Transaction Management")
run("CODE - PLATFORM CODE")
run("CODE - PLATFORM CODE DEVELOP")
run("CPDV - CHANNELS PDV")
run("CSCM - CUSTOMER COMMUNICATION")
run("CSCR - CUSTOMER CREDIT e RISK")
run("CSFR - CUSTOMER FRAUD")
run("CSIN - CUSTOMER INFORMATION")
run("CSIT - CUSTOMER INTERACTION")
run("CSJN - CUSTOMER JOURNEY")
run("CSLM - CUSTOMER LIMIT")
run("CSLY - CUSTOMER LOYALTY")
run("CSOM - CUSTOMER ORDER MGMT")
run("CSOR - CUSTOMER ORDER ROUTING")
run("CSSP - CUSTOMER SUPPORT")
run("DINT - DATA INTEGRATION")
run("DIP - DIGITAL INTEGRATION PLATFORM")
run("DTFN - DATAFIN")
run("DevOps")
run("ECMC - Ecomm Cloud B2C")
run("ECVV - ECOSISTEMA VIVO")
run("ELCN - Elastic Connectors")
run("EMDP - Event Management Digital Platform")
run("ESAW - ESIM ACTIVATION WEB")
run("FNIX - Fenix")
run("GEAD - GEOGRAPHIC ADDRESS")
run("GFNO - GF UNIFICADO")
run("GLDV - GITLAB DEVOPS")
run("GNSS - Contact Center")
run("GSIM - GERENCIAMENTO DE SIMCARD")
run("HBPO - Dauto")
run("HBPO - HUB PGTO")
run("HRCL - HÉRCULES")
run("HYBD - SCC B2B")
run("IAC - IPMD - IPaaS")
run("IAC - KB2B - Telco B2B")
run("IAC - KCLI - Clientes")
run("IAC - KCOR - Corporativo")
run("IAC - KCPO - Telco B2C Pós")
run("IAC - KCPR - Telco B2C Pré")
run("IAC - KCSG - Canal Guiado")
run("IAC - KCSS - Customer Self Service")
run("IAC - KFIS - Fiscal")
run("IAC - KOBS - Observabilidade")
run("IAC - KPAR - Parceiros")
run("IAC - KPDV - Loja")
run("IAC - KPGT - Pagamentos")
run("IAC - KQAT - Qualidade")
run("IAC - KREC - Receita")
run("IAC - KSDX - Sandbox")
run("IAC - KVAR - Varejo")
run("IAC - Landing Zone")
run("IAC - SRUS - SIRIUS")
run("IAC - Segurança")
run("IAC - TEAM SQUAD AUTOMAÇÕES")
run("IAC-ADCP - Arquitetura Digital Cloud Platform")
run("IAC-B2C")
run("IAC-DIP - DIGITAL INTEGRATION PLATFORM")
run("IAC-FDCP - Financial Digital Cloud Platform")
run("IAC-OSS - Operation Support System")
run("IAC-SEC - Security")
run("IFRM - INVOICE FORMAT_RENDER MGMT")
run("IPM - Indicadores de Performance e Métricas")
run("IPMD - IPaaS AMDOCS")
run("JIRA - Jira e Confluence")
run("LCMN - LOCATION MANAGEMENT")
run("LMNG - LOCATION MANAGEMENT")
run("MIGR-4Field")
run("MIGR-Abr")
run("MIGR-Analytics_Sc")
run("MIGR-Api-Management")
run("MIGR-Api-Microservices")
run("MIGR-Apoio")
run("MIGR-Aprendendoautomcao")
run("MIGR-Architecture-Docs")
run("MIGR-Arquitetura-Corporativa")
run("MIGR-Arquitetura-Do-Futuro")
run("MIGR-Arquitetura-Solucoes-Inovacoes")
run("MIGR-Atendimentoura8486")
run("MIGR-Atis")
run("MIGR-Atlys")
run("MIGR-Backstage")
run("MIGR-Bcm")
run("MIGR-Bff")
run("MIGR-Bigid")
run("MIGR-Bpm")
run("MIGR-Bss_Automacoes")
run("MIGR-Callidus")
run("MIGR-Cam")
run("MIGR-Canais")
run("MIGR-Canonical-Model")
run("MIGR-Catalogo")
run("MIGR-Cdrone")
run("MIGR-Cenarios-Qa-Automacao")
run("MIGR-Changemanagement")
run("MIGR-Coe")
run("MIGR-Coedev")
run("MIGR-Col")
run("MIGR-Com")
run("MIGR-Common-Domain")
run("MIGR-CommonDomain")
run("MIGR-Conector-Legado")
run("MIGR-Connector")
run("MIGR-Conta-Online")
run("MIGR-Conta-Online-Fixa")
run("MIGR-Conta-Online-Historico")
run("MIGR-Contact-Center")
run("MIGR-Conv86")
run("MIGR-Cpe-Inventory")
run("MIGR-Crc")
run("MIGR-Crmb2B")
run("MIGR-Crmb2B-Everis")
run("MIGR-Crmb2B-Indra-Departamentais")
run("MIGR-Css")
run("MIGR-Cyber")
run("MIGR-Data-Preparation")
run("MIGR-Deployautomation")
run("MIGR-Desenvolvimento-Colaborativo")
run("MIGR-DevOps")
run("MIGR-Diagnose-Service-Problem")
run("MIGR-Diagnoseserviceproblem")
run("MIGR-Dial-My-App")
run("MIGR-Document-Manager")
run("MIGR-Ecommerce-B2B")
run("MIGR-Edutech")
run("MIGR-Engenharia")
run("MIGR-Enterprise-Domain")
run("MIGR-Enterprisedomain")
run("MIGR-Esboss")
run("MIGR-Eta_Direct")
run("MIGR-Eventsplatform")
run("MIGR-FERRAMENTAS-AUTOMACAO-AIOPS")
run("MIGR-FERRAMENTAS-AUTOMACAO-SAN")
run("MIGR-Fb-App-Vivo")
run("MIGR-Febrabans_Legados")
run("MIGR-Fms")
run("MIGR-Foundation-Azure")
run("MIGR-Framework-Brasil")
run("MIGR-Framework-Brasil-Challenges")
run("MIGR-Framework-Mobile")
run("MIGR-Framework-Qa-Automacao")
run("MIGR-Fsw11")
run("MIGR-Ftm")
run("MIGR-Gedoc")
run("MIGR-Genesys")
run("MIGR-Genesys_Wde")
run("MIGR-Geniaus")
run("MIGR-Gestor-Bloqueios")
run("MIGR-Giscover-Fibra")
run("MIGR-Gonext-Wles")
run("MIGR-Governance-App")
run("MIGR-Gps")
run("MIGR-Gps2")
run("MIGR-Gpsnext")
run("MIGR-Gsim")
run("MIGR-Gsimoss")
run("MIGR-Gsimossl")
run("MIGR-Gvox")
run("MIGR-Gvp")
run("MIGR-Hostsbuildpack")
run("MIGR-Hpfms")
run("MIGR-Hpfms-Fraude-Service")
run("MIGR-Hub_Faturas")
run("MIGR-IIKPIs")
run("MIGR-Idm")
run("MIGR-Ifaces-Int")
run("MIGR-Import_Prod")
run("MIGR-Indicare")
run("MIGR-Infra-Integracao")
run("MIGR-Integration-Domain")
run("MIGR-Interfacescac")
run("MIGR-Intermediate")
run("MIGR-Inventario-Sistema")
run("MIGR-Jaimail2")
run("MIGR-Jee")
run("MIGR-Kafka")
run("MIGR-Kenan")
run("MIGR-Lib-Extended")
run("MIGR-Lm")
run("MIGR-Location-Management")
run("MIGR-Locationmanagement")
run("MIGR-Logtracker")
run("MIGR-Lojaonline")
run("MIGR-Lojaonline-B2B")
run("MIGR-Mainframe")
run("MIGR-Manobra-Gpon")
run("MIGR-Manobra-Unica")
run("MIGR-Manobra-Unificada")
run("MIGR-Meu-Vivo-Design-System")
run("MIGR-Meuvivo-B2C-Ecare")
run("MIGR-Meuvivoempresas")
run("MIGR-Mib-Plataforma-Tv")
run("MIGR-Microservicos4P")
run("MIGR-Microservicosmeuvivo")
run("MIGR-Migracao")
run("MIGR-Moft")
run("MIGR-Monitor-Oss")
run("MIGR-Ms")
run("MIGR-Mvno")
run("MIGR-Netcool-Vivo")
run("MIGR-Network-Reallocation")
run("MIGR-Networkreallocation")
run("MIGR-Ngin")
run("MIGR-Ngin_Gestao")
run("MIGR-Nof")
run("MIGR-Novo_Siu")
run("MIGR-Novoportalgf")
run("MIGR-Npac")
run("MIGR-Nsia")
run("MIGR-Number-Inventory")
run("MIGR-Numberinventory")
run("MIGR-Nyx")
run("MIGR-Oam")
run("MIGR-Odp")
run("MIGR-Ods")
run("MIGR-Open-Hack-Azure")
run("MIGR-Oss")
run("MIGR-Oss-Commons")
run("MIGR-Oss-Fixa")
run("MIGR-Oss-Inventory")
run("MIGR-Ossopenapis")
run("MIGR-Oud")
run("MIGR-Ovd")
run("MIGR-Pagina-Investigacao")
run("MIGR-Plataforma-Digital")
run("MIGR-Plataforma_Nds")
run("MIGR-Platon")
run("MIGR-Portabilidade")
run("MIGR-Portal")
run("MIGR-Portal-Arquitetura")
run("MIGR-Portal-Federado")
run("MIGR-Portal-Integra")
run("MIGR-Portal-Lgpd")
run("MIGR-Portal-Swa")
run("MIGR-Portalautomacao")
run("MIGR-Portalbbtx")
run("MIGR-Portalvivo")
run("MIGR-Portalvivofixa")
run("MIGR-Portanum")
run("MIGR-Power-Curve")
run("MIGR-Processum1")
run("MIGR-Processum2")
run("MIGR-Processum3")
run("MIGR-Pruma")
run("MIGR-QuickStart")
run("MIGR-RPA-Tributario")
run("MIGR-Radius")
run("MIGR-Resource-Inventory-Api")
run("MIGR-Resource-Test")
run("MIGR-ResourceInventory")
run("MIGR-Resourceactivation")
run("MIGR-Resourceorder")
run("MIGR-Resourceschemas")
run("MIGR-Ressarcimento-Sas")
run("MIGR-Rm")
run("MIGR-Robomigracaotecnologia")
run("MIGR-Rom-Camunda")
run("MIGR-Roteamento-Genesys")
run("MIGR-Router")
run("MIGR-Rpa-Blue-Prism")
run("MIGR-Rpa-Interno")
run("MIGR-Rrm")
run("MIGR-S2Partner")
run("MIGR-SUSTENTACAO-INTEGRACAO")
run("MIGR-Sagre")
run("MIGR-Salesforce")
run("MIGR-Sap")
run("MIGR-Sap_Fiori")
run("MIGR-Sap_Portal")
run("MIGR-Sas")
run("MIGR-Savvion-Bao")
run("MIGR-Savvion-Billing")
run("MIGR-Savvion-Corporate")
run("MIGR-Savvion-Wom")
run("MIGR-Sbm")
run("MIGR-Scct")
run("MIGR-Science")
run("MIGR-Scm")
run("MIGR-Scpw")
run("MIGR-Scqla")
run("MIGR-Security-Scans")
run("MIGR-Serasa-Premium")
run("MIGR-Service-Test-Management")
run("MIGR-Serviceproblemmanagement")
run("MIGR-Servicetestmanagement")
run("MIGR-Sgci")
run("MIGR-Sgoe")
run("MIGR-Sics")
run("MIGR-Siebel")
run("MIGR-Sigan")
run("MIGR-Sigan-2")
run("MIGR-Sigitm")
run("MIGR-Sigitmoss")
run("MIGR-Sigres")
run("MIGR-Sigres-2")
run("MIGR-Sigres-Dm")
run("MIGR-Sigres-Massiva")
run("MIGR-Sigres-Portal")
run("MIGR-Sigres-Viewer")
run("MIGR-Sigres2")
run("MIGR-Sirius")
run("MIGR-Siscom")
run("MIGR-Sisnum")
run("MIGR-Smap")
run("MIGR-Smartcenter")
run("MIGR-Smartoffers")
run("MIGR-Smartvendas")
run("MIGR-Smsantana")
run("MIGR-Smtx")
run("MIGR-Sonic")
run("MIGR-Squads")
run("MIGR-Sre")
run("MIGR-Staff")
run("MIGR-Star")
run("MIGR-Staross")
run("MIGR-Talc")
run("MIGR-Tbs")
run("MIGR-Technical-Architecture")
run("MIGR-Telefonica")
run("MIGR-Terus")
run("MIGR-Teshuva")
run("MIGR-Test-Schemas")
run("MIGR-Testesvirtuais")
run("MIGR-Testschemas")
run("MIGR-Tmforum-Apis")
run("MIGR-Topologyinventory")
run("MIGR-Traffic-Simulator")
run("MIGR-Troubleticket")
run("MIGR-Twofa")
run("MIGR-Ura-App-Services")
run("MIGR-Ura-Fixa")
run("MIGR-Ura_Atendimento")
run("MIGR-Vantive-Prisma")
run("MIGR-Vidav")
run("MIGR-Visualizador_Nfe_Feb")
run("MIGR-Vivo-Accounts")
run("MIGR-Vivo-Apis-Core")
run("MIGR-Vivo-Mais")
run("MIGR-Vivo-Mis-Tech")
run("MIGR-Vivo360")
run("MIGR-Vivonet")
run("MIGR-Vivonext")
run("MIGR-Vle")
run("MIGR-Vts")
run("MIGR-Wfm")
run("MIGR-Wisetool")
run("MIGR-Workforcemanagement")
run("MIGR-agi")
run("MIGR-autorec")
run("MIGR-axon")
run("MIGR-b2c-dev-legados")
run("MIGR-bpel")
run("MIGR-brm")
run("MIGR-canaispresencias")
run("MIGR-crystal")
run("MIGR-css-atendimento")
run("MIGR-css-batch")
run("MIGR-dasi-datalab")
run("MIGR-data-barn")
run("MIGR-databarn")
run("MIGR-enova")
run("MIGR-framework-sms")
run("MIGR-gonext")
run("MIGR-ods_adh")
run("MIGR-osb")
run("MIGR-ossdevopslabs")
run("MIGR-pix-manager")
run("MIGR-rpa-atendimento")
run("MIGR-rpa-b2b")
run("MIGR-rpa-componentes")
run("MIGR-rpa-controlm")
run("MIGR-rpa-dotnet")
run("MIGR-rpa-engenharia")
run("MIGR-rpa-governanca")
run("MIGR-rpa-ms")
run("MIGR-rpa-nice")
run("MIGR-rpa-rh")
run("MIGR-sat")
run("MIGR-servicos-virtuais")
run("MIGR-sgp")
run("MIGR-sici")
run("MIGR-soa")
run("MIGR-spic-nspic")
run("MIGR-vivocorp")
run("MKNB - MARKETPLACE ENABLER")
run("MVEJ-MVE")
run("MVPA - Setup App Aks")
run("NGIN - NGIN")
run("NGIN - Sustentacao")
run("NQAS - New Quality Assurance")
run("NXBA - NEXT BEST ACTION")
run("NXBO - NEXT BEST OFFERING")
run("OOAP - OSS OPEN API")
run("OPDI - OPERATION DOMAIN INVENTORY")
run("ORSS - ORACLE SOA SUITE")
run("OSS-Sustentacao")
run("OSSD - OSS DEVOPS")
run("PCO3 - Processum 3.0")
run("PSCR - PORTAL SISTEMAS CORPORATIVOS")
run("PYPM - PAYMENT_POS MGMT")
run("PrevTech - Prevencao a fraude")
run("RBQA - ROBOSQA")
run("RBVM - Risk Based Vulnerability Management Segurança Digital")
run("RSPS - RESOURCE PORTABILITY SYSTEM")
run("RSRI - RESOURCE INVENTORY - RI")
run("SCA - SISTEMA DE CONTROLE DE ACESSO")
run("SDU - SISTEMA DE DIAGNOSTICO UNIFICADO")
run("SFMN - SALES FORCE MGMT")
run("SGTM - SIGITM")
run("SLCM - SALES COMMISSION")
run("SLLD - SALES LEAD")
run("SMBS - Smart Bis")
run("SMRC - SMART CGW")
run("SMRH - Smart History")
run("SMRM - Smart-Messages")
run("SMRO - Smart Offers")
run("SMRR - Smart Reports")
run("SMRS - Smart SIM")
run("SRAP - SERVICE APPOINTMENT")
run("SRAV - SERVICE AVAILABILITYY")
run("SRQL - SERVICE QUALIFICATION")
run("SRUS - SIRIUS")
run("SRVY - SERVICE AVAILABILITY")
run("STDS - SITE DE COMPRAS")
run("TEAM - ADPE - Arquitetura Digital e Projetos Especiais")
run("TEAM - AGITECH-Agile Tech")
run("TEAM - ARQ – Gestão Integrada de Demanda")
run("TEAM - ARQ-EstratégiaTech")
run("TEAM - ARQDS - Arq. Dados")
run("TEAM - ARQTC - Arq. Técnica")
run("TEAM - Arq. Cloud")
run("TEAM - Arq. Integração e Solução")
run("TEAM - Arq. Negocio e Aplicacional")
run("TEAM - Azure DevOps Projeto - Segurança Terra")
run("TEAM - CloudFirst")
run("TEAM - Cloud_Engineer")
run("TEAM - Controle das iniciativas de Processos TI (Lean Office)")
run("TEAM - DAET")
run("TEAM - DAET-Analytics e APPs")
run("TEAM - DAET-Comtech")
run("TEAM - DAET-Governança Estratégica")
run("TEAM - DAET-Portfolio de Iniciativas")
run("TEAM - DevEx")
run("TEAM - Engenharia de Software")
run("TEAM - Engenharia de Software Integração - Débitos Técnicos")
run("TEAM - Engenharia de Software de Integração - Squad Enabler")
run("TEAM - GACOP-Governança Arquitetura Corporativa")
run("TEAM - GOVAT-Governança Ativos de Arquitetura")
run("TEAM - Gestão de Demanda Cross")
run("TEAM - LABS")
run("TEAM - LO-Lean Office")
run("TEAM - Melhorias ERT")
run("TEAM - OKRs")
run("TEAM - PEX-Platform-Experience")
run("TEAM - PGDAET-Planejamento e Gestão")
run("TEAM - POC")
run("TEAM - QA")
run("TEAM - RepositorioTI")
run("TEAM - SecurityChampions")
run("TEAM - SegurançaTerra")
run("TEAM - VivoObserva")
run("TEAM - Ways of Working")
run("TEAM - Web Engine")
run("TLCO - TELCO B2C")
run("TPAZ - TECH PRODUCTS AZURE CLOUD")
run("TRTL - Troubleshooting Tools")
run("VTX - Condor_Voucher_Transaction_System")
run("VVFG - VIVO EMPRESTIMO FGTS")
run("VVMS - VIVO MAIS")
run("VVMT - VIVO MAESTRO")
run("VVMY - VIVO MONEY")
run("VVPI - Vivo PAY")
run("VVPP - VIVO PIX PARCELADO")
run("WBCM - WebComponents")
run("WFM - WORKFORCE MANAGEMENT")
run("WFMS - WORKFORCE MANAGEMENT SYSTEM")
