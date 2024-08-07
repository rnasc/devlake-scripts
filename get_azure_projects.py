from azure.devops.connection import Connection
from msrest.authentication import BasicAuthentication
from dotenv import load_dotenv

import pprint
import os

load_dotenv()
pat = os.environ['VIVO_PAT']

# Fill in with your personal access token and org URL
# personal_access_token = "{INSERIR O PAT}"
personal_access_token = pat 
organization_url = 'https://dev.azure.com/telefonica-vivo-brasil'

# Create a connection to the org
credentials = BasicAuthentication('', personal_access_token)
connection = Connection(base_url=organization_url, creds=credentials)

# Get a client (the "core" client provides access to projects, teams, etc)
core_client = connection.clients.get_core_client()

def myFunc(project):
  return project.name

# Get the first page of projects
projectsList = core_client.get_projects()
projectsList.sort(key=myFunc)

for project in projectsList:
    pprint.pprint(project.name)

