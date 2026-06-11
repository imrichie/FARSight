// Sets the name of the existing Azure OpenAI resource the models deploy onto
@description('Name of the existing Azure OpenAI resource')
param openAIResourceName string = 'oai-farsight'

// Sets the deployment name for the embedding model — this is the name the SDK addresses
@description('Deployment name for the embedding model')
param embeddingDeploymentName string = 'text-embedding-3-small'

// Sets the deployment name for the chat model — this is the name the SDK addresses
@description('Deployment name for the chat model')
param chatDeploymentName string = 'gpt-5.4-mini'

// Controls throughput capacity in units of 1,000 tokens per minute —
// 10 (10K TPM) is plenty for a low-traffic portfolio workload
@description('Capacity in 1K tokens-per-minute units for each deployment')
param deploymentCapacity int = 10

// References the existing oai-farsight resource — does not create or modify it
resource azureOpenAIResource 'Microsoft.CognitiveServices/accounts@2024-10-01' existing = {
  name: openAIResourceName
}

// Creates the embedding model deployment — used for chunk and question vectors
resource embeddingModelDeployment 'Microsoft.CognitiveServices/accounts/deployments@2024-10-01' = {
  parent: azureOpenAIResource
  name: embeddingDeploymentName

  // Establishes pay-per-call throughput at the capacity set above
  sku: {
    name: 'Standard'
    capacity: deploymentCapacity
  }

  properties: {
    // Pins the exact model and version for reproducible deployments
    model: {
      format: 'OpenAI'
      name: 'text-embedding-3-small'
      version: '1'
    }
  }
}

// Creates the chat model deployment — used to generate cited answers
resource chatModelDeployment 'Microsoft.CognitiveServices/accounts/deployments@2024-10-01' = {
  parent: azureOpenAIResource
  name: chatDeploymentName

  // Waits for the embedding deployment first — Azure OpenAI rejects
  // parallel deployment creation on the same resource
  dependsOn: [embeddingModelDeployment]

  // Establishes pay-per-call throughput at the capacity set above —
  // GlobalStandard because gpt-5.4-mini does not offer the regional Standard SKU
  sku: {
    name: 'GlobalStandard'
    capacity: deploymentCapacity
  }

  properties: {
    // Pins the exact model and version for reproducible deployments —
    // verified available and not deprecated in westus as of June 2026
    model: {
      format: 'OpenAI'
      name: 'gpt-5.4-mini'
      version: '2026-03-17'
    }
  }
}

// Outputs the embedding deployment name so it can be copied into .env
@description('Deployment name the SDK uses to address the embedding model')
output embeddingDeploymentName string = embeddingModelDeployment.name

// Outputs the chat deployment name so it can be copied into .env
@description('Deployment name the SDK uses to address the chat model')
output chatDeploymentName string = chatModelDeployment.name
