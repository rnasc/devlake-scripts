import requests
import logging
import json
import pprint
import os

from azure.devops.connection import Connection
from msrest.authentication import BasicAuthentication
from requests.adapters import HTTPAdapter
from requests.auth import HTTPBasicAuth
from urllib3.util.retry import Retry
from dotenv import load_dotenv

load_dotenv()
pat = os.environ['VIVO_PAT']
url = os.environ['DEVLAKE_URL']

session = requests.Session()
retry = Retry(connect=3, backoff_factor=0.5)
adapter = HTTPAdapter(max_retries=retry)
session.mount('http://', adapter)
session.mount('https://', adapter)

basic = HTTPBasicAuth('admin', 'admin')

#URLs
connUrl = url + "/plugins/{}/connections"
scopesUrl = url + "/plugins/{}/connections/{}/scopes"
scopeUrl = url + "/plugins/{}/connections/{}/scopes/{}"
scopeConfigUrl = url + "/plugins/{}/connections/{}/scope-configs"
remoteScopesUrl = url + "/plugins/{}/connections/{}/remote-scopes"
projectsUrl = url + "/projects"
projectUrl = url + "/projects/{}"
blueprintsUrl = url + "/blueprints"
blueprintUrl = url + "/blueprints/{}"
sonarqubeRemoteSearchUrl = url + "/plugins/sonarqube/connections/{}/search-remote-scopes"

#Azure Connection
# azurePAT = "{INSERIR O PAT}"
azurePAT = pat
azureOrgId = "telefonica-vivo-brasil"
# azureConnectionType = "azuredevops_go"
azureConnectionType = "azuredevops"

#SonarQube Connection
# sonarqubePAT = "{INSERIR O PAT}"
sonarqubePAT = pat
sonarqubeEndpoint = "http://sonar-devops.redecorp.br/"
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

def getConnection(connectionType, projectRef):
    queryParams = { "pageSize": 800, "page": 1 }
    # Call the Get Connection API
    responseConnection = session.get(connUrl.format(str(connectionType)), params=queryParams, auth=basic)
    # Converts the response to json
    page = responseConnection.json()
    # Filter the connections that starts with the projectRef
    filtrado = list(filter(lambda x: x["name"].startswith(projectRef), page))
    # Returns the id of the exising connection
    if(len(filtrado) > 0):
        return filtrado[0]["id"]

def getSonarQubeConnection(projectRef):
    queryParams = { "pageSize": 800, "page": 1 }
    # Call the Get Connection API
    responseConnection = session.get(connUrl.format("sonarqube"), params=queryParams, auth=basic)
    # Converts the response to json
    page = responseConnection.json()
    # Filter the connections that starts with the projectRef
    filtrado = list(filter(lambda x: x["name"].startswith(projectRef), page))
    # Returns the id of the exising connection
    if(len(filtrado) > 0):
        return filtrado[0]["id"]

def getConnectionScopesQuantity(connectionId, connectionType, projectRef):
    if connectionId:
        # Creates the query parameter
        queryParams = { "groupId": "{}/{}".format(azureOrgId, str(projectRef)), "pageSize": 800, "page": 1 }
        # Call the Get Scopes API to get the scopes (repositories) already linked to the connection
        respPartial = session.get(scopesUrl.format(str(connectionType), str(connectionId)), params=queryParams, auth=basic)
        # Converts the response to JSON and get the 'count' content
        return respPartial.json()["count"]

def getSonarQubeScopesQuantity(connectionId, projectRef):
    if connectionId:
        # Creates the query parameter
        queryParamsPartial = { "searchTerm": "{}".format(str(projectRef)), "pageSize": 500, "page": 1 }
        # Call the Get Scopes API to get the scopes (repositories) already linked to the connection
        respPartial = session.get(scopesUrl.format(str("sonarqube"), str(connectionId)), params=queryParamsPartial, auth=basic)
        # Converts the response to JSON and get the 'count' content
        return respPartial.json()["count"]

def run(projectRefs):
    try:
        for projectRef in projectRefs:
            ### Creates the Principal Connection ###
            connectionId = getConnection(azureConnectionType, projectRef)
            nrProjectScopes = getConnectionScopesQuantity(connectionId, azureConnectionType, projectRef)
            sonarQubeConnectionId = getSonarQubeConnection(projectRef)
            nrSonarScopes = getSonarQubeScopesQuantity(sonarQubeConnectionId, projectRef)
            print("{}:{}:{}".format(projectRef, nrProjectScopes, nrSonarScopes))
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

run([
    "ACRM - ACCOUNT_RECEIVABLE MGMT",
    "ADBB - AEM B2B",
    "ADCP - CAMUNDA",
    "ADCP - FLUTTER",
    "ADCP - JAVA",
    "ADCP - WEB",
    "AMDP - API Management Digital Plataform",
    "APPV - Framework-Brasil",
    "AXWY - API MANAGEMENT - AXWAY",
    "AXWY - ApiManagementCloud",
    "AXWY - ApiManagementOnPremise",
    "AZR4 - 4P AZURE",
    "BINV - BLUEPLANET INVENTORY",
    "BLMN - BILLING MGMT",
    "BSVN - BPM SAVVION",
    "CLMN - COLLECTION MGMT",
    "CMMR - COMMERCE",
    "CMOC - COMMERCIAL_OFFER CATALOG",
    "CNDF - Condor Financial Transaction Management",
    "CODE - PLATFORM CODE",
    "CODE - PLATFORM CODE DEVELOP",
    "CPDV - CHANNELS PDV",
    "CSCM - CUSTOMER COMMUNICATION",
    "CSCR - CUSTOMER CREDIT e RISK",
    "CSFR - CUSTOMER FRAUD",
    "CSIN - CUSTOMER INFORMATION",
    "CSIT - CUSTOMER INTERACTION",
    "CSJN - CUSTOMER JOURNEY",
    "CSLM - CUSTOMER LIMIT",
    "CSLY - CUSTOMER LOYALTY",
    "CSOM - CUSTOMER ORDER MGMT",
    "CSOR - CUSTOMER ORDER ROUTING",
    "CSSP - CUSTOMER SUPPORT",
    "DINT - DATA INTEGRATION",
    "DIP - DIGITAL INTEGRATION PLATFORM",
    "DTFN - DATAFIN",
    "DevOps",
    "ECMC - Ecomm Cloud B2C",
    "ECVV - ECOSISTEMA VIVO",
    "ELCN - Elastic Connectors",
    "EMDP - Event Management Digital Platform",
    "ESAW - ESIM ACTIVATION WEB",
    "FNIX - Fenix",
    "GEAD - GEOGRAPHIC ADDRESS",
    "GFNO - GF UNIFICADO",
    "GLDV - GITLAB DEVOPS",
    "GNSS - Contact Center",
    "GSIM - GERENCIAMENTO DE SIMCARD",
    "HBPO - Dauto",
    "HBPO - HUB PGTO",
    "HRCL - HÉRCULES",
    "HYBD - SCC B2B",
    "IAC - IPMD - IPaaS",
    "IAC - KB2B - Telco B2B",
    "IAC - KCLI - Clientes",
    "IAC - KCOR - Corporativo",
    "IAC - KCPO - Telco B2C Pós",
    "IAC - KCPR - Telco B2C Pré",
    "IAC - KCSG - Canal Guiado",
    "IAC - KCSS - Customer Self Service",
    "IAC - KFIS - Fiscal",
    "IAC - KOBS - Observabilidade",
    "IAC - KPAR - Parceiros",
    "IAC - KPDV - Loja",
    "IAC - KPGT - Pagamentos",
    "IAC - KQAT - Qualidade",
    "IAC - KREC - Receita",
    "IAC - KSDX - Sandbox",
    "IAC - KVAR - Varejo",
    "IAC - Landing Zone",
    "IAC - SRUS - SIRIUS",
    "IAC - Segurança",
    "IAC - TEAM SQUAD AUTOMAÇÕES",
    "IAC-ADCP - Arquitetura Digital Cloud Platform",
    "IAC-B2C",
    "IAC-DIP - DIGITAL INTEGRATION PLATFORM",
    "IAC-FDCP - Financial Digital Cloud Platform",
    "IAC-OSS - Operation Support System",
    "IAC-SEC - Security",
    "IFRM - INVOICE FORMAT_RENDER MGMT",
    "IPM - Indicadores de Performance e Métricas",
    "IPMD - IPaaS AMDOCS",
    "JIRA - Jira e Confluence",
    "LCMN - LOCATION MANAGEMENT",
    "LMNG - LOCATION MANAGEMENT",
    "MIGR-4Field",
    "MIGR-Abr",
    "MIGR-Analytics_Sc",
    "MIGR-Api-Management",
    "MIGR-Api-Microservices",
    "MIGR-Apoio",
    "MIGR-Aprendendoautomcao",
    "MIGR-Architecture-Docs",
    "MIGR-Arquitetura-Corporativa",
    "MIGR-Arquitetura-Do-Futuro",
    "MIGR-Arquitetura-Solucoes-Inovacoes",
    "MIGR-Atendimentoura8486",
    "MIGR-Atis",
    "MIGR-Atlys",
    "MIGR-Backstage",
    "MIGR-Bcm",
    "MIGR-Bff",
    "MIGR-Bigid",
    "MIGR-Bpm",
    "MIGR-Bss_Automacoes",
    "MIGR-Callidus",
    "MIGR-Cam",
    "MIGR-Canais",
    "MIGR-Canonical-Model",
    "MIGR-Catalogo",
    "MIGR-Cdrone",
    "MIGR-Cenarios-Qa-Automacao",
    "MIGR-Changemanagement",
    "MIGR-Coe",
    "MIGR-Coedev",
    "MIGR-Col",
    "MIGR-Com",
    "MIGR-Common-Domain",
    "MIGR-CommonDomain",
    "MIGR-Conector-Legado",
    "MIGR-Connector",
    "MIGR-Conta-Online",
    "MIGR-Conta-Online-Fixa",
    "MIGR-Conta-Online-Historico",
    "MIGR-Contact-Center",
    "MIGR-Conv86",
    "MIGR-Cpe-Inventory",
    "MIGR-Crc",
    "MIGR-Crmb2B",
    "MIGR-Crmb2B-Everis",
    "MIGR-Crmb2B-Indra-Departamentais",
    "MIGR-Css",
    "MIGR-Cyber",
    "MIGR-Data-Preparation",
    "MIGR-Deployautomation",
    "MIGR-Desenvolvimento-Colaborativo",
    "MIGR-DevOps",
    "MIGR-Diagnose-Service-Problem",
    "MIGR-Diagnoseserviceproblem",
    "MIGR-Dial-My-App",
    "MIGR-Document-Manager",
    "MIGR-Ecommerce-B2B",
    "MIGR-Edutech",
    "MIGR-Engenharia",
    "MIGR-Enterprise-Domain",
    "MIGR-Enterprisedomain",
    "MIGR-Esboss",
    "MIGR-Eta_Direct",
    "MIGR-Eventsplatform",
    "MIGR-FERRAMENTAS-AUTOMACAO-AIOPS",
    "MIGR-FERRAMENTAS-AUTOMACAO-SAN",
    "MIGR-Fb-App-Vivo",
    "MIGR-Febrabans_Legados",
    "MIGR-Fms",
    "MIGR-Foundation-Azure",
    "MIGR-Framework-Brasil",
    "MIGR-Framework-Brasil-Challenges",
    "MIGR-Framework-Mobile",
    "MIGR-Framework-Qa-Automacao",
    "MIGR-Fsw11",
    "MIGR-Ftm",
    "MIGR-Gedoc",
    "MIGR-Genesys",
    "MIGR-Genesys_Wde",
    "MIGR-Geniaus",
    "MIGR-Gestor-Bloqueios",
    "MIGR-Giscover-Fibra",
    "MIGR-Gonext-Wles",
    "MIGR-Governance-App",
    "MIGR-Gps",
    "MIGR-Gps2",
    "MIGR-Gpsnext",
    "MIGR-Gsim",
    "MIGR-Gsimoss",
    "MIGR-Gsimossl",
    "MIGR-Gvox",
    "MIGR-Gvp",
    "MIGR-Hostsbuildpack",
    "MIGR-Hpfms",
    "MIGR-Hpfms-Fraude-Service",
    "MIGR-Hub_Faturas",
    "MIGR-IIKPIs",
    "MIGR-Idm",
    "MIGR-Ifaces-Int",
    "MIGR-Import_Prod",
    "MIGR-Indicare",
    "MIGR-Infra-Integracao",
    "MIGR-Integration-Domain",
    "MIGR-Interfacescac",
    "MIGR-Intermediate",
    "MIGR-Inventario-Sistema",
    "MIGR-Jaimail2",
    "MIGR-Jee",
    "MIGR-Kafka",
    "MIGR-Kenan",
    "MIGR-Lib-Extended",
    "MIGR-Lm",
    "MIGR-Location-Management",
    "MIGR-Locationmanagement",
    "MIGR-Logtracker",
    "MIGR-Lojaonline",
    "MIGR-Lojaonline-B2B",
    "MIGR-Mainframe",
    "MIGR-Manobra-Gpon",
    "MIGR-Manobra-Unica",
    "MIGR-Manobra-Unificada",
    "MIGR-Meu-Vivo-Design-System",
    "MIGR-Meuvivo-B2C-Ecare",
    "MIGR-Meuvivoempresas",
    "MIGR-Mib-Plataforma-Tv",
    "MIGR-Microservicos4P",
    "MIGR-Microservicosmeuvivo",
    "MIGR-Migracao",
    "MIGR-Moft",
    "MIGR-Monitor-Oss",
    "MIGR-Ms",
    "MIGR-Mvno",
    "MIGR-Netcool-Vivo",
    "MIGR-Network-Reallocation",
    "MIGR-Networkreallocation",
    "MIGR-Ngin",
    "MIGR-Ngin_Gestao",
    "MIGR-Nof",
    "MIGR-Novo_Siu",
    "MIGR-Novoportalgf",
    "MIGR-Npac",
    "MIGR-Nsia",
    "MIGR-Number-Inventory",
    "MIGR-Numberinventory",
    "MIGR-Nyx",
    "MIGR-Oam",
    "MIGR-Odp",
    "MIGR-Ods",
    "MIGR-Open-Hack-Azure",
    "MIGR-Oss",
    "MIGR-Oss-Commons",
    "MIGR-Oss-Fixa",
    "MIGR-Oss-Inventory",
    "MIGR-Ossopenapis",
    "MIGR-Oud",
    "MIGR-Ovd",
    "MIGR-Pagina-Investigacao",
    "MIGR-Plataforma-Digital",
    "MIGR-Plataforma_Nds",
    "MIGR-Platon",
    "MIGR-Portabilidade",
    "MIGR-Portal",
    "MIGR-Portal-Arquitetura",
    "MIGR-Portal-Federado",
    "MIGR-Portal-Integra",
    "MIGR-Portal-Lgpd",
    "MIGR-Portal-Swa",
    "MIGR-Portalautomacao",
    "MIGR-Portalbbtx",
    "MIGR-Portalvivo",
    "MIGR-Portalvivofixa",
    "MIGR-Portanum",
    "MIGR-Power-Curve",
    "MIGR-Processum1",
    "MIGR-Processum2",
    "MIGR-Processum3",
    "MIGR-Pruma",
    "MIGR-QuickStart",
    "MIGR-RPA-Tributario",
    "MIGR-Radius",
    "MIGR-Resource-Inventory-Api",
    "MIGR-Resource-Test",
    "MIGR-ResourceInventory",
    "MIGR-Resourceactivation",
    "MIGR-Resourceorder",
    "MIGR-Resourceschemas",
    "MIGR-Ressarcimento-Sas",
    "MIGR-Rm",
    "MIGR-Robomigracaotecnologia",
    "MIGR-Rom-Camunda",
    "MIGR-Roteamento-Genesys",
    "MIGR-Router",
    "MIGR-Rpa-Blue-Prism",
    "MIGR-Rpa-Interno",
    "MIGR-Rrm",
    "MIGR-S2Partner",
    "MIGR-SUSTENTACAO-INTEGRACAO",
    "MIGR-Sagre",
    "MIGR-Salesforce",
    "MIGR-Sap",
    "MIGR-Sap_Fiori",
    "MIGR-Sap_Portal",
    "MIGR-Sas",
    "MIGR-Savvion-Bao",
    "MIGR-Savvion-Billing",
    "MIGR-Savvion-Corporate",
    "MIGR-Savvion-Wom",
    "MIGR-Sbm",
    "MIGR-Scct",
    "MIGR-Science",
    "MIGR-Scm",
    "MIGR-Scpw",
    "MIGR-Scqla",
    "MIGR-Security-Scans",
    "MIGR-Serasa-Premium",
    "MIGR-Service-Test-Management",
    "MIGR-Serviceproblemmanagement",
    "MIGR-Servicetestmanagement",
    "MIGR-Sgci",
    "MIGR-Sgoe",
    "MIGR-Sics",
    "MIGR-Siebel",
    "MIGR-Sigan",
    "MIGR-Sigan-2",
    "MIGR-Sigitm",
    "MIGR-Sigitmoss",
    "MIGR-Sigres",
    "MIGR-Sigres-2",
    "MIGR-Sigres-Dm",
    "MIGR-Sigres-Massiva",
    "MIGR-Sigres-Portal",
    "MIGR-Sigres-Viewer",
    "MIGR-Sigres2",
    "MIGR-Sirius",
    "MIGR-Siscom",
    "MIGR-Sisnum",
    "MIGR-Smap",
    "MIGR-Smartcenter",
    "MIGR-Smartoffers",
    "MIGR-Smartvendas",
    "MIGR-Smsantana",
    "MIGR-Smtx",
    "MIGR-Sonic",
    "MIGR-Squads",
    "MIGR-Sre",
    "MIGR-Staff",
    "MIGR-Star",
    "MIGR-Staross",
    "MIGR-Talc",
    "MIGR-Tbs",
    "MIGR-Technical-Architecture",
    "MIGR-Telefonica",
    "MIGR-Terus",
    "MIGR-Teshuva",
    "MIGR-Test-Schemas",
    "MIGR-Testesvirtuais",
    "MIGR-Testschemas",
    "MIGR-Tmforum-Apis",
    "MIGR-Topologyinventory",
    "MIGR-Traffic-Simulator",
    "MIGR-Troubleticket",
    "MIGR-Twofa",
    "MIGR-Ura-App-Services",
    "MIGR-Ura-Fixa",
    "MIGR-Ura_Atendimento",
    "MIGR-Vantive-Prisma",
    "MIGR-Vidav",
    "MIGR-Visualizador_Nfe_Feb",
    "MIGR-Vivo-Accounts",
    "MIGR-Vivo-Apis-Core",
    "MIGR-Vivo-Mais",
    "MIGR-Vivo-Mis-Tech",
    "MIGR-Vivo360",
    "MIGR-Vivonet",
    "MIGR-Vivonext",
    "MIGR-Vle",
    "MIGR-Vts",
    "MIGR-Wfm",
    "MIGR-Wisetool",
    "MIGR-Workforcemanagement",
    "MIGR-agi",
    "MIGR-autorec",
    "MIGR-axon",
    "MIGR-b2c-dev-legados",
    "MIGR-bpel",
    "MIGR-brm",
    "MIGR-canaispresencias",
    "MIGR-crystal",
    "MIGR-css-atendimento",
    "MIGR-css-batch",
    "MIGR-dasi-datalab",
    "MIGR-data-barn",
    "MIGR-databarn",
    "MIGR-enova",
    "MIGR-framework-sms",
    "MIGR-gonext",
    "MIGR-ods_adh",
    "MIGR-osb",
    "MIGR-ossdevopslabs",
    "MIGR-pix-manager",
    "MIGR-rpa-atendimento",
    "MIGR-rpa-b2b",
    "MIGR-rpa-componentes",
    "MIGR-rpa-controlm",
    "MIGR-rpa-dotnet",
    "MIGR-rpa-engenharia",
    "MIGR-rpa-governanca",
    "MIGR-rpa-ms",
    "MIGR-rpa-nice",
    "MIGR-rpa-rh",
    "MIGR-sat",
    "MIGR-servicos-virtuais",
    "MIGR-sgp",
    "MIGR-sici",
    "MIGR-soa",
    "MIGR-spic-nspic",
    "MIGR-vivocorp",
    "MKNB - MARKETPLACE ENABLER",
    "MVEJ-MVE",
    "MVPA - Setup App Aks",
    "NGIN - NGIN",
    "NGIN - Sustentacao",
    "NQAS - New Quality Assurance",
    "NXBA - NEXT BEST ACTION",
    "NXBO - NEXT BEST OFFERING",
    "OOAP - OSS OPEN API",
    "OPDI - OPERATION DOMAIN INVENTORY",
    "ORSS - ORACLE SOA SUITE",
    "OSS-Sustentacao",
    "OSSD - OSS DEVOPS",
    "PCO3 - Processum 3.0",
    "PSCR - PORTAL SISTEMAS CORPORATIVOS",
    "PYPM - PAYMENT_POS MGMT",
    "PrevTech - Prevencao a fraude",
    "RBQA - ROBOSQA",
    "RBVM - Risk Based Vulnerability Management Segurança Digital",
    "RSPS - RESOURCE PORTABILITY SYSTEM",
    "RSRI - RESOURCE INVENTORY - RI",
    "SCA - SISTEMA DE CONTROLE DE ACESSO",
    "SDU - SISTEMA DE DIAGNOSTICO UNIFICADO",
    "SFMN - SALES FORCE MGMT",
    "SGTM - SIGITM",
    "SLCM - SALES COMMISSION",
    "SLLD - SALES LEAD",
    "SMBS - Smart Bis",
    "SMRC - SMART CGW",
    "SMRH - Smart History",
    "SMRM - Smart-Messages",
    "SMRO - Smart Offers",
    "SMRR - Smart Reports",
    "SMRS - Smart SIM",
    "SRAP - SERVICE APPOINTMENT",
    "SRAV - SERVICE AVAILABILITYY",
    "SRQL - SERVICE QUALIFICATION",
    "SRUS - SIRIUS",
    "SRVY - SERVICE AVAILABILITY",
    "STDS - SITE DE COMPRAS",
    "TEAM - ADPE - Arquitetura Digital e Projetos Especiais",
    "TEAM - AGITECH-Agile Tech",
    "TEAM - ARQ – Gestão Integrada de Demanda",
    "TEAM - ARQ-EstratégiaTech",
    "TEAM - ARQDS - Arq. Dados",
    "TEAM - ARQTC - Arq. Técnica",
    "TEAM - Arq. Cloud",
    "TEAM - Arq. Integração e Solução",
    "TEAM - Arq. Negocio e Aplicacional",
    "TEAM - Azure DevOps Projeto - Segurança Terra",
    "TEAM - CloudFirst",
    "TEAM - Cloud_Engineer",
    "TEAM - Controle das iniciativas de Processos TI (Lean Office,",
    "TEAM - DAET",
    "TEAM - DAET-Analytics e APPs",
    "TEAM - DAET-Comtech",
    "TEAM - DAET-Governança Estratégica",
    "TEAM - DAET-Portfolio de Iniciativas",
    "TEAM - DevEx",
    "TEAM - Engenharia de Software",
    "TEAM - Engenharia de Software Integração - Débitos Técnicos",
    "TEAM - Engenharia de Software de Integração - Squad Enabler",
    "TEAM - GACOP-Governança Arquitetura Corporativa",
    "TEAM - GOVAT-Governança Ativos de Arquitetura",
    "TEAM - Gestão de Demanda Cross",
    "TEAM - LABS",
    "TEAM - LO-Lean Office",
    "TEAM - Melhorias ERT",
    "TEAM - OKRs",
    "TEAM - PEX-Platform-Experience",
    "TEAM - PGDAET-Planejamento e Gestão",
    "TEAM - POC",
    "TEAM - QA",
    "TEAM - RepositorioTI",
    "TEAM - SecurityChampions",
    "TEAM - SegurançaTerra",
    "TEAM - VivoObserva",
    "TEAM - Ways of Working",
    "TEAM - Web Engine",
    "TLCO - TELCO B2C",
    "TPAZ - TECH PRODUCTS AZURE CLOUD",
    "TRTL - Troubleshooting Tools",
    "VTX - Condor_Voucher_Transaction_System",
    "VVFG - VIVO EMPRESTIMO FGTS",
    "VVMS - VIVO MAIS",
    "VVMT - VIVO MAESTRO",
    "VVMY - VIVO MONEY",
    "VVPI - Vivo PAY",
    "VVPP - VIVO PIX PARCELADO",
    "WBCM - WebComponents",
    "WFM - WORKFORCE MANAGEMENT",
    "WFMS - WORKFORCE MANAGEMENT SYSTEM"
    ])
