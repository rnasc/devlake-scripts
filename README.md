# Scripts de carregamento

Esses scripts foram criados para permitir a leitura e carregamento de dados ao Devlake.

## Requisitos

Copiar o arquivo .env.example para .env.
Preencher as variáveis de ambiente necessárias:
- VIVO_PAT: Token pessoal do Devlake
- DEVLAKE_URL: url onde serão feitas as chamadas de API

# Próximos Passos

Automatizar o fluxo de criação de connections, projects e execução de extração para qualquer sigla.
<ol>
	<li>Cria a Connection [azuredevops, azuredevops_go, sonarqube] [DIP, FNIX, EMDP]</li>
	<li>Cria a Scope Config associado a Connection</li>
	<li>Adiciona os Data Scopes</li>
	<li>Associa o Scope Config com os Data Scopes</li>
	<li>Cria o Project</li>
	<li>Adiciona a Connection</li>
</ol>

Para extração de projetos do Azure DevOps via PowerShell e API da Azure
<ol>
	<li>$pat = "{INSERIR_O_PAT}"</li>
	<li>$base64AuthInfo = [Convert]::ToBase64String([Text.Encoding]::ASCII.GetBytes(("{0}:{1}" -f user," user,"pat")))</li>
	<li>$headers = @{Authorization=("Basic {0}" -f $base64AuthInfo)}</li>
	<li>$azureDevOpsUrl = "https://dev.azure.com/telefonica-vivo-brasil"</li>
	<li>projects=Invoke−RestMethod−Uri"azureDevOpsUrl/_apis/projects" -Method Get -Headers $headers -ContentType application/json -OutFile projetos_azure_devops.json</li>
</ol>
