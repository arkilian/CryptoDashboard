"""Deploy direto via Kudu ZIP Deploy API"""
import subprocess
import json
import requests
import sys

# Obter publishing credentials
result = subprocess.run([
    'az', 'webapp', 'deployment', 'list-publishing-credentials',
    '--name', 'arkilian-webapp',
    '--resource-group', 'arkilian-group',
    '--query', '{username:publishingUserName,password:publishingPassword}',
    '-o', 'json'
], capture_output=True, text=True)

if result.returncode != 0:
    print(f"Erro ao obter credenciais: {result.stderr}")
    sys.exit(1)

creds = json.loads(result.stdout)
username = creds['username']
password = creds['password']

# Kudu ZIP Deploy endpoint
url = 'https://arkilian-webapp-def7evcab7gghrfn.scm.francecentral-01.azurewebsites.net/api/zipdeploy'

print(f"Deploying deploy.zip to {url}...")

with open('deploy.zip', 'rb') as f:
    response = requests.post(
        url,
        auth=(username, password),
        data=f,
        headers={'Content-Type': 'application/zip'},
        timeout=600
    )

print(f"Status: {response.status_code}")
print(f"Response: {response.text}")

if response.status_code in (200, 202):
    print("✅ Deploy successful!")
    sys.exit(0)
else:
    print("❌ Deploy failed!")
    sys.exit(1)
