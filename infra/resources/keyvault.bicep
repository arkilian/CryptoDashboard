// Azure Key Vault for secure secrets management
@description('Name of the Key Vault (max 24 chars)')
@maxLength(24)
param name string

@description('Location for the Key Vault')
param location string

@description('Resource tags')
param tags object = {}

@description('Principal ID of the managed identity to grant access')
param principalId string

// ========================================
// KEY VAULT
// ========================================
resource keyVault 'Microsoft.KeyVault/vaults@2023-07-01' = {
  name: name
  location: location
  tags: tags
  properties: {
    sku: {
      family: 'A'
      name: 'standard'
    }
    tenantId: subscription().tenantId
    enableRbacAuthorization: false // Using access policies
    enabledForDeployment: false
    enabledForDiskEncryption: false
    enabledForTemplateDeployment: true
    enableSoftDelete: true
    softDeleteRetentionInDays: 7
    enablePurgeProtection: null // Can be set to true for production
    networkAcls: {
      defaultAction: 'Allow' // Allow Azure services
      bypass: 'AzureServices'
    }
    accessPolicies: [
      {
        tenantId: subscription().tenantId
        objectId: principalId
        permissions: {
          secrets: [
            'get'
            'list'
          ]
        }
      }
    ]
  }
}

// ========================================
// OUTPUTS
// ========================================
output id string = keyVault.id
output name string = keyVault.name
output uri string = keyVault.properties.vaultUri
