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
   - Choose a model (recommended: `gpt-4.1`, `gpt-4-turbo`, or `gpt-35-turbo`)
   - Provide a deployment name (e.g., "gpt-4.1")
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
export AZURE_OPENAI_DEPLOYMENT_NAME="gpt-4.1"
```

### Using .env File (Development)

For development environments, create a `.env` file in the project root:

```env
AZURE_OPENAI_ENDPOINT=https://your-resource.openai.azure.com/
AZURE_OPENAI_API_KEY=your-api-key
AZURE_OPENAI_DEPLOYMENT_NAME=gpt-4.1
```

## Features

### 1. Environment Variable Configuration

- **Server-Side**: Configure Azure OpenAI using `AZURE_OPENAI_ENDPOINT`, `AZURE_OPENAI_API_KEY`, and `AZURE_OPENAI_DEPLOYMENT_NAME` environment variables
- **Automatic Detection**: Service automatically detects environment configuration and enables AI functionality
- **.env File Support**: Development-friendly configuration using `.env` files

### 2. AI-Powered Suggestions

- **Per-Risk Analysis**: Each detected risk can receive AI-powered suggestions by clicking "AI Suggestion" buttons
- **Direct HTML Output**: AI generates recommendations with HTML markup
- **Comprehensive Analysis**: AI provides impact assessment, recommended actions, migration strategy, and timeline considerations
- **Contextual Recommendations**: AI analyzes the specific risk data to provide relevant suggestions

### 3. User Experience

- **AI related Disclaimer**: Prominent warning about AI-generated content appears when AI functionality is available
- **Loading States**: Visual feedback during AI suggestion generation
- **Error Handling**: Graceful error handling for API failures

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
