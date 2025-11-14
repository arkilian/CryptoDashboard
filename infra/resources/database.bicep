// Azure Database for PostgreSQL Flexible Server
@description('Name of the PostgreSQL server')
param serverName string

@description('Name of the database to create')
param databaseName string

@description('Location for the PostgreSQL server')
param location string

@description('Resource tags')
param tags object = {}

@description('Administrator login name')
param administratorLogin string

@description('Administrator password')
@secure()
param administratorPassword string

@description('Key Vault name to store the connection string')
param keyVaultName string

// ========================================
// POSTGRESQL FLEXIBLE SERVER
// ========================================
resource postgresServer 'Microsoft.DBforPostgreSQL/flexibleServers@2023-03-01-preview' = {
  name: serverName
  location: location
  tags: tags
  sku: {
    name: 'Standard_B1ms'
    tier: 'Burstable'
  }
  properties: {
    administratorLogin: administratorLogin
    administratorLoginPassword: administratorPassword
    version: '14'
    storage: {
      storageSizeGB: 32
      autoGrow: 'Enabled'
    }
    backup: {
      backupRetentionDays: 7
      geoRedundantBackup: 'Disabled'
    }
    highAvailability: {
      mode: 'Disabled'
    }
    network: {
      // Public access with firewall rules
    }
  }
}

// ========================================
// FIREWALL RULE: Allow Azure Services
// ========================================
resource firewallRule 'Microsoft.DBforPostgreSQL/flexibleServers/firewallRules@2023-03-01-preview' = {
  parent: postgresServer
  name: 'AllowAllAzureServices'
  properties: {
    startIpAddress: '0.0.0.0'
    endIpAddress: '0.0.0.0'
  }
}

// ========================================
// DATABASE CREATION
// ========================================
resource database 'Microsoft.DBforPostgreSQL/flexibleServers/databases@2023-03-01-preview' = {
  parent: postgresServer
  name: databaseName
  properties: {
    charset: 'UTF8'
    collation: 'en_US.utf8'
  }
}

// ========================================
// CONFIGURATION: Require SSL
// ========================================
resource sslConfig 'Microsoft.DBforPostgreSQL/flexibleServers/configurations@2023-03-01-preview' = {
  parent: postgresServer
  name: 'require_secure_transport'
  properties: {
    value: 'on'
    source: 'user-override'
  }
}

// ========================================
// STORE CONNECTION STRING IN KEY VAULT
// ========================================
resource keyVault 'Microsoft.KeyVault/vaults@2023-07-01' existing = {
  name: keyVaultName
}

resource dbHostSecret 'Microsoft.KeyVault/vaults/secrets@2023-07-01' = {
  parent: keyVault
  name: 'db-host'
  properties: {
    value: postgresServer.properties.fullyQualifiedDomainName
  }
}

resource dbUserSecret 'Microsoft.KeyVault/vaults/secrets@2023-07-01' = {
  parent: keyVault
  name: 'db-user'
  properties: {
    value: administratorLogin
  }
}

resource dbPasswordSecret 'Microsoft.KeyVault/vaults/secrets@2023-07-01' = {
  parent: keyVault
  name: 'db-password'
  properties: {
    value: administratorPassword
  }
}

resource dbConnectionStringSecret 'Microsoft.KeyVault/vaults/secrets@2023-07-01' = {
  parent: keyVault
  name: 'postgresql-connection-string'
  properties: {
    value: 'host=${postgresServer.properties.fullyQualifiedDomainName} port=5432 dbname=${databaseName} user=${administratorLogin} password=${administratorPassword} sslmode=require'
  }
}

// ========================================
// OUTPUTS
// ========================================
output serverId string = postgresServer.id
output serverName string = postgresServer.name
output serverFqdn string = postgresServer.properties.fullyQualifiedDomainName
output databaseName string = database.name
