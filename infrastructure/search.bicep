// Sets the name of the Azure AI Search service
@description('Name of the Azure AI Search service')
param searchServiceName string = 'srch-farsight-dev'

// Defines the Azure region where the service will be deployed
@description('Azure region for the search service')
param location string = 'westus2'

// Controls the pricing tier — free is sufficient for development and review purposes
@description('Pricing tier for the search service')
@allowed(['free', 'basic', 'standard'])
param skuName string = 'free'

// Creates the Azure AI Search service using the parameters defined above
resource azureSearchService 'Microsoft.Search/searchServices@2023-11-01' = {
  name: searchServiceName
  location: location

  // Establishes the pricing tier for this service
  sku: {
    name: skuName
  }

  properties: {
    // Sets a single replica and partition — appropriate for a development workload
    replicaCount: 1
    partitionCount: 1

    // Uses the standard hosting mode — required for the free tier
    hostingMode: 'default'
  }
}

// Outputs the endpoint URL so it can be copied into .env after deployment
@description('The endpoint URL for the Azure AI Search service')
output searchServiceEndpoint string = 'https://${azureSearchService.name}.search.windows.net'

// Outputs the provisioned resource name for reference
@description('The name of the provisioned Azure AI Search service')
output searchServiceName string = azureSearchService.name
