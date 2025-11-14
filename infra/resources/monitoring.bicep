// Log Analytics Workspace and Application Insights for monitoring
@description('Name of the Log Analytics Workspace')
param logAnalyticsName string

@description('Name of the Application Insights instance')
param appInsightsName string

@description('Location for the resources')
param location string

@description('Resource tags')
param tags object = {}

// ========================================
// LOG ANALYTICS WORKSPACE
// ========================================
resource logAnalytics 'Microsoft.OperationalInsights/workspaces@2022-10-01' = {
  name: logAnalyticsName
  location: location
  tags: tags
  properties: {
    sku: {
      name: 'PerGB2018'
    }
    retentionInDays: 30
    features: {
      enableLogAccessUsingOnlyResourcePermissions: true
    }
  }
}

// ========================================
// APPLICATION INSIGHTS
// ========================================
resource appInsights 'Microsoft.Insights/components@2020-02-02' = {
  name: appInsightsName
  location: location
  tags: tags
  kind: 'web'
  properties: {
    Application_Type: 'web'
    WorkspaceResourceId: logAnalytics.id
    IngestionMode: 'LogAnalytics'
    publicNetworkAccessForIngestion: 'Enabled'
    publicNetworkAccessForQuery: 'Enabled'
  }
}

// ========================================
// OUTPUTS
// ========================================
output logAnalyticsId string = logAnalytics.id
output logAnalyticsWorkspaceId string = logAnalytics.properties.customerId
output logAnalyticsName string = logAnalytics.name
output appInsightsId string = appInsights.id
output appInsightsName string = appInsights.name
output appInsightsInstrumentationKey string = appInsights.properties.InstrumentationKey
output appInsightsConnectionString string = appInsights.properties.ConnectionString
