# Azure OpenAI Integration

This document describes the Azure OpenAI integration feature added to AVS RVTools Analyzer.

## Overview

The Azure OpenAI integration provides AI-powered risk analysis suggestions to help users understand and mitigate Azure VMware Solution migration risks. This feature enhances the existing risk detection capabilities with intelligent recommendations through environment variable configuration.

## Prerequisites

Before using the Azure OpenAI integration, you need to set up the following Azure resources:

### 1. Azure OpenAI Resource

Create an Azure OpenAI resource in your Azure subscription:

1. **Sign in to Azure Portal**: Go to [portal.azure.com](https://portal.azure.com)
2. **Create Resource**: Search for "Azure OpenAI" and click "Create"
3. **Configure Settings**:
   - Choose your subscription and resource group
   - Select a region (ensure it supports Azure OpenAI)
   - Choose a pricing tier
4. **Complete Creation**: Review and create the resource

**Documentation**: [Create and deploy an Azure OpenAI Service resource](https://docs.microsoft.com/en-us/azure/cognitive-services/openai/how-to/create-resource)

### 2. Model Deployment

Deploy a compatible language model in your Azure OpenAI resource:

1. **Navigate to Azure OpenAI Studio**: From your resource, click "Go to Azure OpenAI Studio"
2. **Create Deployment**:
   - Go to "Deployments" → "Create new deployment"
   - Choose a model (recommended: `gpt-4`, `gpt-4-turbo`, or `gpt-35-turbo`)
   - Provide a deployment name (e.g., "gpt-4")
   - Configure capacity settings
3. **Note the Deployment Name**: You'll need this for configuration

**Documentation**: [Deploy a model with Azure OpenAI](https://docs.microsoft.com/en-us/azure/cognitive-services/openai/how-to/create-resource?pivots=web-portal#deploy-a-model)

### 3. API Access Configuration

Obtain your endpoint URL and API key:

1. **Endpoint URL**: Found in your Azure OpenAI resource overview (e.g., `https://your-resource.openai.azure.com/`)
2. **API Key**: Go to "Keys and Endpoint" section in your Azure OpenAI resource
3. **Note Security**: Keep your API key secure and never commit it to version control

**Documentation**: [How to switch between OpenAI and Azure OpenAI endpoints](https://docs.microsoft.com/en-us/azure/cognitive-services/openai/how-to/switching-endpoints)

## Configuration

The Azure OpenAI integration uses **environment variables only** for security and deployment flexibility. There is no user interface configuration form.

### Environment Variables

Set the following environment variables:

```bash
export AZURE_OPENAI_ENDPOINT="https://your-resource.openai.azure.com/"
export AZURE_OPENAI_API_KEY="your-api-key"
export AZURE_OPENAI_DEPLOYMENT_NAME="gpt-4"
```

### Using .env File (Development)

For development environments, create a `.env` file in the project root:

```env
AZURE_OPENAI_ENDPOINT=https://your-resource.openai.azure.com/
AZURE_OPENAI_API_KEY=your-api-key
AZURE_OPENAI_DEPLOYMENT_NAME=gpt-4
```

**Note**: The `.env` file should be added to `.gitignore` to prevent committing credentials.

## Features

### 1. Environment Variable Configuration
- **Server-Side Only**: Configure Azure OpenAI using `AZURE_OPENAI_ENDPOINT`, `AZURE_OPENAI_API_KEY`, and `AZURE_OPENAI_DEPLOYMENT_NAME` environment variables
- **Automatic Detection**: Service automatically detects environment configuration and enables AI functionality
- **Secure Deployment**: Eliminates client-side credential handling, providing enterprise-ready security
- **.env File Support**: Development-friendly configuration using `.env` files

### 2. AI-Powered Suggestions
- **Per-Risk Analysis**: Each detected risk can receive AI-powered suggestions by clicking "AI Suggestion" buttons
- **Direct HTML Output**: AI generates HTML markup directly, eliminating client-side transformations
- **Structured Content**: Support for heading levels h5 and below for proper content hierarchy
- **Comprehensive Analysis**: AI provides impact assessment, recommended actions, migration strategy, and timeline considerations
- **Contextual Recommendations**: AI analyzes the specific risk data to provide relevant suggestions

### 3. User Experience
- **Always-Visible Disclaimer**: Prominent warning about AI-generated content appears when AI functionality is available
- **Progressive Enhancement**: Existing functionality remains unchanged when AI is not configured
- **Loading States**: Visual feedback during AI suggestion generation
- **Error Handling**: Graceful error handling for API failures
- **Production Ready**: No configuration forms or user credential inputs - pure environment-based deployment

## Usage

### Setup

1. **Configure Environment Variables**: Set the required environment variables or create a `.env` file as described in the Configuration section above
2. **Start the Application**: Run the AVS RVTools Analyzer application
3. **Automatic Detection**: The application will automatically detect the Azure OpenAI configuration and enable AI functionality

### Getting AI Suggestions

1. **Upload RVTools Data**: Upload your RVTools Excel file through the web interface
2. **Review Detected Risks**: The application will analyze your data and display detected migration risks
3. **Generate AI Suggestions**: Click the "AI Suggestion" button on any risk card you want to analyze
4. **Review Analysis**: Wait for the AI to generate the analysis (typically 2-10 seconds) and review the comprehensive suggestions provided
5. **Use Results**: Apply the AI recommendations to your migration planning process

### Visual Indicators

When Azure OpenAI is properly configured via environment variables:
- **Disclaimer Visible**: A prominent disclaimer about AI-generated content appears at the top
- **AI Suggestion Buttons**: "AI Suggestion" buttons appear on each risk card
- **Loading States**: Buttons show loading indicators while generating suggestions

## API Endpoints

### GET /api/azure-openai-status
Check Azure OpenAI configuration status.

**Response:**
```json
{
  "is_configured": true,
  "deployment_name": "gpt-4"
}
```

### POST /api/ai-suggestion
Generate AI-powered risk analysis suggestions.

**Request Body:**
```json
{
  "risk_name": "detect_vusb_devices",
  "risk_description": "vUSB devices connected to VMs",
  "risk_data": [...],
  "risk_level": "blocking"
}
```

**Response:**
```json
{
  "success": true,
  "suggestion": "<h5>Risk Analysis</h5><p>AI-generated HTML content...</p>",
  "risk_name": "detect_vusb_devices"
}
```

**Note**: The API automatically uses the Azure OpenAI configuration from environment variables. No credentials need to be provided in the request.
```

## Security Considerations

- **Environment Variable Storage**: API keys are securely stored as environment variables on the server
- **No Client-Side Credentials**: Eliminates client-side credential handling and storage
- **HTTPS Required**: Azure OpenAI endpoints use HTTPS for secure communication
- **Server-Side Configuration**: All configuration is done server-side for enhanced security
- **.env File Security**: Ensure `.env` files are not committed to version control
- **Production Deployment**: Use proper secret management systems (Azure Key Vault, Kubernetes secrets, etc.) in production environments

## Technical Implementation

### Backend Components
- **AzureOpenAIService**: Handles Azure OpenAI API communication using environment variables
- **Environment Configuration**: Automatic detection of Azure OpenAI configuration from environment variables
- **API Models**: Pydantic models for request/response validation
- **API Endpoints**: FastAPI routes for AI functionality and status checking

### Frontend Components
- **Automatic Detection**: JavaScript automatically detects when AI is available via status endpoint
- **AI Suggestion Buttons**: Dynamic display of suggestion buttons when AI is configured
- **CSS Styling**: Consistent with existing application theme
- **Global Data Store**: Reliable risk data transmission using JavaScript global objects

### Environment Integration
- **python-dotenv**: Support for `.env` file loading in development
- **Environment Variables**: Production-ready configuration using system environment variables
- **Automatic Loading**: Environment variables loaded at application startup

## Dependencies

- **openai**: Python OpenAI library for Azure OpenAI integration
- **python-dotenv**: Environment variable loading from `.env` files
- **pydantic**: For API request/response validation
- **fastapi**: For API endpoint implementation

## Error Handling

The integration includes comprehensive error handling for:
- Missing or invalid environment variables
- Invalid credentials or endpoints
- Network connectivity issues
- API rate limiting
- Service unavailability
- Invalid deployment names
- Risk data transmission issues

Errors are displayed to users with clear, actionable messages, and detailed logging is provided for administrators.

## Deployment

### Production Deployment

For production environments:

1. **Set Environment Variables**: Configure the three required environment variables in your deployment environment
2. **Secure Secret Management**: Use proper secret management systems:
   - **Azure**: Azure Key Vault
   - **Kubernetes**: Kubernetes Secrets
   - **Docker**: Docker Secrets
   - **Cloud Providers**: AWS Secrets Manager, Google Secret Manager
3. **Restart Application**: Restart the application after setting environment variables
4. **Verify Configuration**: Check the application logs to confirm Azure OpenAI is detected

### Development Deployment

For development environments:

1. **Create .env File**: Add the `.env` file to your project root with the required variables
2. **Add to .gitignore**: Ensure `.env` is in your `.gitignore` file
3. **Start Application**: The application will automatically load variables from `.env`
4. **Test Functionality**: Verify AI suggestions work correctly

### Docker Deployment

Example Docker environment configuration:

```dockerfile
ENV AZURE_OPENAI_ENDPOINT=https://your-resource.openai.azure.com/
ENV AZURE_OPENAI_API_KEY=your-api-key
ENV AZURE_OPENAI_DEPLOYMENT_NAME=gpt-4
```

### Kubernetes Deployment

Example Kubernetes secret and deployment:

```yaml
apiVersion: v1
kind: Secret
metadata:
  name: azure-openai-secret
type: Opaque
stringData:
  AZURE_OPENAI_ENDPOINT: https://your-resource.openai.azure.com/
  AZURE_OPENAI_API_KEY: your-api-key
  AZURE_OPENAI_DEPLOYMENT_NAME: gpt-4
---
apiVersion: apps/v1
kind: Deployment
metadata:
  name: avs-rvtools-analyzer
spec:
  template:
    spec:
      containers:
      - name: app
        envFrom:
        - secretRef:
            name: azure-openai-secret
```

## Future Enhancements

Potential future improvements could include:
- Support for multiple AI providers (OpenAI, other Azure Cognitive Services)
- Caching of AI suggestions to reduce API calls
- Customizable prompt templates via environment variables
- Batch processing for multiple risks
- Integration with Azure Managed Identity for credential management
- Support for different Azure OpenAI API versions
- Custom model fine-tuning for AVS-specific recommendations