// Sets the name of the Azure OpenAI resource
@description('Name of the Azure OpenAI resource')
param openAIResourceName string = 'oai-farsight'

// Defines the Azure region — westus is used because it serves both models
// FARSight needs (text-embedding-3-small and gpt-4o-mini); westus2 does not
@description('Azure region for the Azure OpenAI resource')
param location string = 'westus'

// Controls the pricing tier — S0 is pay-per-call with no idle cost
@description('Pricing tier for the Azure OpenAI resource')
@allowed(['S0'])
param skuName string = 'S0'

// Creates the Azure OpenAI resource using the parameters defined above
resource azureOpenAIResource 'Microsoft.CognitiveServices/accounts@2024-10-01' = {
  name: openAIResourceName
  location: location

  // Identifies this as an Azure OpenAI resource (not a general AI Services one)
  kind: 'OpenAI'

  // Establishes the pricing tier for this resource
  sku: {
    name: skuName
  }

  properties: {
    // Gives the resource its own subdomain — required for the endpoint URL
    customSubDomainName: openAIResourceName
  }
}

// Outputs the endpoint URL so it can be copied into .env after deployment
@description('The endpoint URL for the Azure OpenAI resource')
output openAIEndpoint string = azureOpenAIResource.properties.endpoint

// Outputs the provisioned resource name for reference
@description('The name of the provisioned Azure OpenAI resource')
output openAIResourceName string = azureOpenAIResource.name
