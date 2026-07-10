// Provisions the Azure Static Web App that hosts the React frontend.
// Deployed through its own GitHub Actions workflow (frontend-deploy.yml)
// using the Azure/static-web-apps-deploy action and a deployment token —
// this resource is not linked to GitHub here, so no GitHub token is ever
// needed in Bicep or Azure AD. See DECISIONS.md for why this replaced the
// original Vercel plan.

@description('Name of the Azure Static Web App.')
param staticWebAppName string = 'stapp-farsight'

@description('Azure region for the Static Web App. Static Web Apps only supports a limited region set (e.g. westus2, centralus, eastus2, eastasia, westeurope) — this must be one of them regardless of the resource group default.')
param location string = 'westus2'

@description('Static Web Apps pricing tier. Free is sufficient — Standard is only needed for linked backends or staging environments, neither of which this project uses.')
@allowed([
  'Free'
  'Standard'
])
param skuName string = 'Free'

// Creates the Static Web App with no repository linkage — deployment is
// handled entirely by our own GitHub Actions workflow and a deployment
// token, not Static Web Apps' native GitHub App integration (which would
// require storing a GitHub personal access token here).
resource staticWebApp 'Microsoft.Web/staticSites@2023-12-01' = {
  name: staticWebAppName
  location: location
  sku: {
    name: skuName
    tier: skuName
  }
  properties: {}
}

@description('Default hostname for the deployed frontend.')
output staticWebAppUrl string = 'https://${staticWebApp.properties.defaultHostname}'

@description('Name of the provisioned Static Web App, used to fetch its deployment token.')
output staticWebAppName string = staticWebApp.name
