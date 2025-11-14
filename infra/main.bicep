// Main infrastructure orchestration for CryptoDashboard
// Deploys: Web App, PostgreSQL, Key Vault, Monitoring, Managed Identity
targetScope = 'resourceGroup'

@minLength(1)
@maxLength(64)
@description('Name of the environment for resource naming and tagging')
param environmentName string

@minLength(1)
@description('Primary location for all resources')
param location string = resourceGroup().location

@description('Resource token for unique naming')
var resourceToken = uniqueString(subscription().id, resourceGroup().id, location, environmentName)

@description('Tags applied to all resources')
var tags = {
  'azd-env-name': environmentName
  project: 'CryptoDashboard'
  'managed-by': 'azd'
}

// ========================================
// MANAGED IDENTITY (required by azd)
// ========================================
module identity 'resources/identity.bicep' = {
  name: 'identity-deployment'
  params: {
    name: 'azid${resourceToken}'
    location: location
    tags: tags
  }
}

// ========================================
// MONITORING (Log Analytics + App Insights)
// ========================================
module monitoring 'resources/monitoring.bicep' = {
  name: 'monitoring-deployment'
  params: {
    logAnalyticsName: 'azlog${resourceToken}'
    appInsightsName: 'azai${resourceToken}'
    location: location
    tags: tags
  }
}

// ========================================
// KEY VAULT (Secrets management)
// ========================================
module keyVault 'resources/keyvault.bicep' = {
  name: 'keyvault-deployment'
  params: {
    name: 'azkv${resourceToken}'
    location: location
    tags: tags
    principalId: identity.outputs.principalId
  }
}

// ========================================
// POSTGRESQL FLEXIBLE SERVER
// ========================================
module database 'resources/database.bicep' = {
  name: 'database-deployment'
  params: {
    serverName: 'azpg${resourceToken}'
    databaseName: 'cryptodashboard'
    location: location
    tags: tags
    administratorLogin: 'dbadmin'
    administratorPassword: 'P@ssw0rd${resourceToken}!' // Temporary - should be changed post-deployment
    keyVaultName: keyVault.outputs.name
  }
}

// ========================================
// WEB APP SERVICE (Streamlit Application)
// ========================================
module webApp 'resources/web.bicep' = {
  name: 'web-deployment'
  params: {
    appServicePlanName: 'azasp${resourceToken}'
    webAppName: 'azapp${resourceToken}'
    location: location
    tags: tags
    serviceName: 'web' // Must match azure.yaml service name
    appInsightsConnectionString: monitoring.outputs.appInsightsConnectionString
    appInsightsInstrumentationKey: monitoring.outputs.appInsightsInstrumentationKey
    managedIdentityId: identity.outputs.id
    keyVaultName: keyVault.outputs.name
    dbName: 'cryptodashboard'
  }
  dependsOn: [
    database
  ]
}

// ========================================
// OUTPUTS (required by azd)
// ========================================
output RESOURCE_GROUP_ID string = resourceGroup().id
output WEB_APP_URL string = webApp.outputs.webAppUrl
output WEB_APP_NAME string = webApp.outputs.webAppName
output POSTGRESQL_SERVER_NAME string = database.outputs.serverName
output POSTGRESQL_SERVER_FQDN string = database.outputs.serverFqdn
output KEY_VAULT_NAME string = keyVault.outputs.name
output KEY_VAULT_URI string = keyVault.outputs.uri
output APP_INSIGHTS_NAME string = monitoring.outputs.appInsightsName
output MANAGED_IDENTITY_CLIENT_ID string = identity.outputs.clientId
