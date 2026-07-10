@description('Azure region for the backend hosting resources. Defaults to the resource group location.')
param location string = resourceGroup().location

@description('Name of the Log Analytics workspace used by Container Apps logs.')
param logAnalyticsWorkspaceName string = 'log-farsight-aca-dev'

@description('Name of the Azure Container Registry used for FastAPI backend images. Must be globally unique and alphanumeric.')
param containerRegistryName string = 'acrfarsight${uniqueString(resourceGroup().id)}'

@description('Azure Container Registry SKU.')
@allowed([
  'Basic'
  'Standard'
  'Premium'
])
param containerRegistrySku string = 'Basic'

@description('Name of the user-assigned managed identity used for ACR pull access.')
param acrPullIdentityName string = 'id-farsight-acr-pull-dev'

@description('Name of the Container Apps managed environment.')
param containerAppsEnvironmentName string = 'cae-farsight-dev'

@description('Name of the FastAPI backend Container App.')
param containerAppName string = 'ca-farsight-api-dev'

@description('Name of the container inside the Container App revision.')
param containerName string = 'farsight-api'

@description('Public placeholder image used until the real FastAPI image is built and deployed in #26.')
param placeholderImage string = 'mcr.microsoft.com/azuredocs/containerapps-helloworld:latest'

@description('Container port exposed by the placeholder image. #26 should set this to 8000 when deploying the real FastAPI image.')
param targetPort int = 80

@description('CPU cores for the backend container. Container Apps accepts fractional CPU values.')
@allowed([
  '0.25'
  '0.5'
  '1.0'
])
param containerCpu string = '0.5'

@description('Memory for the backend container.')
@allowed([
  '0.5Gi'
  '1.0Gi'
  '2.0Gi'
])
param containerMemory string = '1.0Gi'

@description('Minimum replicas. Zero enables scale-to-zero when idle.')
@minValue(0)
param minReplicas int = 0

@description('Maximum replicas for the portfolio demo backend.')
@minValue(1)
param maxReplicas int = 1

@description('Concurrent HTTP requests per replica before Container Apps scales out.')
@minValue(1)
param httpConcurrentRequests int = 20

resource logAnalyticsWorkspace 'Microsoft.OperationalInsights/workspaces@2023-09-01' = {
  name: logAnalyticsWorkspaceName
  location: location
  properties: {
    retentionInDays: 30
    sku: {
      name: 'PerGB2018'
    }
  }
}

resource containerRegistry 'Microsoft.ContainerRegistry/registries@2023-07-01' = {
  name: containerRegistryName
  location: location
  sku: {
    name: containerRegistrySku
  }
  properties: {
    adminUserEnabled: false
  }
}

resource acrPullIdentity 'Microsoft.ManagedIdentity/userAssignedIdentities@2023-01-31' = {
  name: acrPullIdentityName
  location: location
}

resource acrPullRoleAssignment 'Microsoft.Authorization/roleAssignments@2022-04-01' = {
  name: guid(containerRegistry.id, acrPullIdentity.id, 'AcrPull')
  scope: containerRegistry
  properties: {
    principalId: acrPullIdentity.properties.principalId
    principalType: 'ServicePrincipal'
    roleDefinitionId: subscriptionResourceId(
      'Microsoft.Authorization/roleDefinitions',
      '7f951dda-4ed3-4680-a7ca-43fe172d538d'
    )
  }
}

resource containerAppsEnvironment 'Microsoft.App/managedEnvironments@2026-01-01' = {
  name: containerAppsEnvironmentName
  location: location
  properties: {
    appLogsConfiguration: {
      destination: 'log-analytics'
      logAnalyticsConfiguration: {
        customerId: logAnalyticsWorkspace.properties.customerId
        sharedKey: logAnalyticsWorkspace.listKeys().primarySharedKey
      }
    }
  }
}

resource containerApp 'Microsoft.App/containerApps@2026-01-01' = {
  name: containerAppName
  location: location
  identity: {
    type: 'UserAssigned'
    userAssignedIdentities: {
      '${acrPullIdentity.id}': {}
    }
  }
  properties: {
    managedEnvironmentId: containerAppsEnvironment.id
    configuration: {
      activeRevisionsMode: 'Single'
      ingress: {
        external: true
        targetPort: targetPort
        transport: 'auto'
        allowInsecure: false
      }
      registries: [
        {
          server: containerRegistry.properties.loginServer
          identity: acrPullIdentity.id
        }
      ]
    }
    template: {
      containers: [
        {
          name: containerName
          image: placeholderImage
          resources: {
            cpu: json(containerCpu)
            memory: containerMemory
          }
        }
      ]
      scale: {
        minReplicas: minReplicas
        maxReplicas: maxReplicas
        rules: [
          {
            name: 'http-concurrency'
            http: {
              metadata: {
                concurrentRequests: string(httpConcurrentRequests)
              }
            }
          }
        ]
      }
    }
  }
  dependsOn: [
    acrPullRoleAssignment
  ]
}

@description('URL for the Container Apps backend.')
output backendUrl string = 'https://${containerApp.properties.configuration.ingress.fqdn}'

@description('Name of the FastAPI backend Container App.')
output containerAppName string = containerApp.name

@description('Name of the Container Apps managed environment.')
output containerAppsEnvironmentName string = containerAppsEnvironment.name

@description('Name of the Azure Container Registry.')
output containerRegistryName string = containerRegistry.name

@description('Login server for the Azure Container Registry.')
output containerRegistryLoginServer string = containerRegistry.properties.loginServer
