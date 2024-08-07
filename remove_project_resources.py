import requests
import json

from requests.adapters import HTTPAdapter
from requests.auth import HTTPBasicAuth
from urllib3.util.retry import Retry

session = requests.Session()
retry = Retry(connect=3, backoff_factor=0.5)
adapter = HTTPAdapter(max_retries=retry)
session.mount('http://', adapter)
session.mount('https://', adapter)

basic = HTTPBasicAuth('admin', 'admin')

def run(connectionType, projectRef):
    #define a conexão de busca da connection voltadas ao azuredevops_go e faz a busca das connections disponíveis no devlake
    # responseConnection = session.get("http://10.124.70.137:443/api/plugins/"+ str(connectionType) +"/connections", auth=basic)
    # page = responseConnection.json()

    # #filtra as connections que possuem a sigla projectRef
    # filtrado = list(filter(lambda x: x["name"].startswith(projectRef), page))
    
    # print("Quantidade de Connections encontrados: " + str(len(filtrado)))
    # print("Id da Connection: " + str(filtrado[0]["id"]))

    # connectionId = filtrado[0]["id"]

    # url2 = "http://10.124.70.137:443/api/plugins/" + str(connectionType) + "/connections/" + str(connectionId) + "/scopes"
    
    # queryParams2 = {
    #     "blueprints": "false",
    #     "pageSize": 800,
    #     "page": 1
    # }
    
    # resp2 = session.get(url2, params=queryParams2, auth=basic)
    # results2 = resp2.json()["scopes"]

    # print("Quantidade de Scopes Encontrados: " + str(len(results2))) 

    # queryParams3 = {
    #     "delete_data_only": "false"
    # }
    
    # for r in results2:
    #     try:
    #         url3 = "http://10.124.70.137:443/api/plugins/" + str(connectionType) + "/connections/" + str(connectionId) + "/scopes/" + str(r["scope"]["id"])
    #         print(url3)
    #         resp3 = session.delete(url3, params=queryParams3, auth=basic)
    #         print(resp3)
    #         results3 = resp3.json()
    #         print(json.dumps(results3))
    #     except Exception as e:
    #         print("Falha de conexão. Prosseguindo com o próximo item...")


    responseConnection = session.get("http://10.124.70.137:443/api/plugins/sonarqube/connections", auth=basic)
    page = responseConnection.json()

    #filtra as connections que possuem a sigla projectRef
    filtrado = list(filter(lambda x: x["name"].startswith(projectRef), page))
    
    print("Quantidade de Connections encontrados: " + str(len(filtrado)))
    print("Id da Connection: " + str(filtrado[0]["id"]))

    connectionId = filtrado[0]["id"]

    url3 = "http://10.124.70.137:443/api/plugins/sonarqube/connections/" + str(connectionId) + "/scopes"
    
    queryParams2 = {
        "blueprints": "false",
        "pageSize": 800,
        "page": 1
    }
    
    resp3 = session.get(url3, params=queryParams2, auth=basic)
    results3 = resp3.json()["scopes"]

    print("Quantidade de Scopes Encontrados: " + str(len(results3))) 

    queryParams4 = {
        "delete_data_only": "false"
    }
    
    for r in results3:
        print(r)
        url4 = "http://10.124.70.137:443/api/plugins/sonarqube/connections/" + str(connectionId) + "/scopes/" + str(r["scope"]["projectKey"])
        print(url4)
        resp4 = session.delete(url4, params=queryParams4, auth=basic)
        print(resp4)
        results4 = resp4.json()
        print(json.dumps(results4))

run("sonarqube", "DevOps")