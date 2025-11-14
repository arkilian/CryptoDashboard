// User Assigned Managed Identity for secure authentication
@description('Name of the managed identity')
param name string

@description('Location for the managed identity')
param location string

@description('Resource tags')
param tags object = {}

// ========================================
// USER ASSIGNED MANAGED IDENTITY
// ========================================
resource managedIdentity 'Microsoft.ManagedIdentity/userAssignedIdentities@2023-01-31' = {
  name: name
  location: location
  tags: tags
}

// ========================================
// OUTPUTS
// ========================================
output id string = managedIdentity.id
output clientId string = managedIdentity.properties.clientId
output principalId string = managedIdentity.properties.principalId
output name string = managedIdentity.name
