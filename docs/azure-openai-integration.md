# Azure OpenAI Integration

This document describes the Azure OpenAI integration feature added to AVS RVTools Analyzer.

## Overview

The Azure OpenAI integration provides AI-powered risk analysis suggestions to help users understand and mitigate Azure VMware Solution migration risks. This feature enhances the existing risk detection capabilities with intelligent recommendations.

## Features

### 1. Configuration Interface
- **Azure OpenAI Endpoint**: Input field for your Azure OpenAI resource endpoint
- **API Key**: Secure input field for your OpenAI API key
- **Deployment Name**: Configurable deployment name (defaults to "gpt-4")
- **Connection Testing**: Test your credentials before using the feature
- **Optional Integration**: Feature only appears when properly configured

### 2. AI-Powered Suggestions
- **Per-Risk Analysis**: Each detected risk can receive AI-powered suggestions
- **Comprehensive Analysis**: AI provides impact assessment, recommended actions, migration strategy, and timeline considerations
- **Contextual Recommendations**: AI analyzes the specific risk data to provide relevant suggestions
- **Formatted Output**: Suggestions are displayed with proper formatting and structure

### 3. User Experience
- **Progressive Enhancement**: Existing functionality remains unchanged
- **Clear Status Messages**: Users receive feedback on configuration and API calls
- **Loading States**: Visual feedback during AI suggestion generation
- **Error Handling**: Graceful error handling for API failures
- **Secure Handling**: API keys are not stored permanently

## Usage

### Setup
1. Click on "AI-Powered Risk Analysis (Optional)" to expand the configuration section
2. Enter your Azure OpenAI endpoint URL (e.g., `https://your-resource.openai.azure.com/`)
3. Enter your OpenAI API key
4. Optionally modify the deployment name (default: gpt-4)
5. Click "Test Connection" to verify your credentials (optional but recommended)
6. Click "Configure" to enable the AI suggestion feature

### Getting AI Suggestions
1. After configuration, "AI Suggestion" buttons will appear on each risk card
2. Click the "AI Suggestion" button for any risk you want to analyze
3. Wait for the AI to generate the analysis (typically 2-10 seconds)
4. Review the comprehensive suggestions provided
5. Use the close button to hide suggestions when done

## API Endpoints

### POST /api/ai-suggestion
Generate AI-powered risk analysis suggestions.

**Request Body:**
```json
{
  "risk_name": "detect_vusb_devices",
  "risk_description": "vUSB devices connected to VMs",
  "risk_data": [...],
  "risk_level": "blocking",
  "azure_endpoint": "https://your-resource.openai.azure.com/",
  "api_key": "your-api-key",
  "deployment_name": "gpt-4"
}
```

**Response:**
```json
{
  "success": true,
  "suggestion": "AI-generated suggestion text...",
  "risk_name": "detect_vusb_devices"
}
```

### POST /api/test-azure-openai
Test Azure OpenAI connection with provided credentials.

**Request Body:**
```json
{
  "azure_endpoint": "https://your-resource.openai.azure.com/",
  "api_key": "your-api-key",
  "deployment_name": "gpt-4"
}
```

**Response:**
```json
{
  "success": true,
  "message": "Connection test successful",
  "response": "Connection successful"
}
```

## Security Considerations

- **API Key Handling**: API keys are only stored in browser memory during the session
- **No Persistent Storage**: Credentials are not saved to disk or databases
- **HTTPS Required**: Azure OpenAI endpoints use HTTPS for secure communication
- **Client-Side Configuration**: All configuration is done client-side for security

## Technical Implementation

### Backend Components
- **AzureOpenAIService**: Handles Azure OpenAI API communication
- **API Models**: Pydantic models for request/response validation
- **API Endpoints**: FastAPI routes for AI functionality

### Frontend Components
- **Configuration UI**: Bootstrap-based configuration form
- **JavaScript Functions**: Handle API calls and UI updates
- **CSS Styling**: Consistent with existing application theme

## Dependencies

- **openai**: Python OpenAI library for Azure OpenAI integration
- **pydantic**: For API request/response validation
- **fastapi**: For API endpoint implementation

## Error Handling

The integration includes comprehensive error handling for:
- Invalid credentials or endpoints
- Network connectivity issues
- API rate limiting
- Service unavailability
- Invalid deployment names

Errors are displayed to users with clear, actionable messages.

## Future Enhancements

Potential future improvements could include:
- Support for multiple AI providers (OpenAI, other Azure Cognitive Services)
- Caching of AI suggestions to reduce API calls
- Customizable prompt templates
- Batch processing for multiple risks
- Integration with Azure Key Vault for credential management