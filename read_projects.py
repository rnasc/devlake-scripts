
import json

def readProjects():
    # Opening JSON file
    f = open('../extracoes/projetos_azure_devops.json', encoding='UTF-8')
    
    # returns JSON object as a dictionary
    data = json.load(f)
    
    # Iterating through the json list
    for i in data:
        print(i['name'])
    
    # Closing file
    f.close()

readProjects()