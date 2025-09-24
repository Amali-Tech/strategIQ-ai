# API Gateway CORS Configuration for Local Development

## Overview

The API Gateway has been configured with comprehensive CORS (Cross-Origin Resource Sharing) support to enable local development and frontend integration.

## CORS Features Implemented

### 1. **Comprehensive Headers**

- `Access-Control-Allow-Origin: *` - Allows requests from any origin
- `Access-Control-Allow-Methods` - Supports DELETE, GET, HEAD, OPTIONS, PATCH, POST, PUT
- `Access-Control-Allow-Headers` - Includes all common headers:
  - Content-Type, X-Amz-Date, Authorization, X-Api-Key, X-Amz-Security-Token
  - X-Requested-With, Accept, Accept-Version, Content-Length, Content-MD5, Date, X-Api-Version
- `Access-Control-Allow-Credentials: false` - No credentials required
- `Access-Control-Max-Age: 86400` - Cache preflight requests for 24 hours

### 2. **Full Method Coverage**

- **OPTIONS methods** - Proper preflight support for both `/upload` and `/status/{imageHash}`
- **POST /upload** - CORS headers on actual responses
- **GET /status/{imageHash}** - CORS headers on actual responses
- **Error responses** - CORS headers on 4XX and 5XX errors

### 3. **No Authentication Required**

- **Authorization: NONE** - No authentication tokens required
- **API Key Required: false** - No API keys needed
- **No Cognito/Lambda Authorizers** - Open access for all endpoints
- **Public API** - Anyone can call the endpoints without credentials

## API Endpoints

### Upload Endpoint

```
POST https://your-api-gateway-url/dev/upload
OPTIONS https://your-api-gateway-url/dev/upload (preflight)
```

### Status Endpoint

```
GET https://your-api-gateway-url/dev/status/{imageHash}
OPTIONS https://your-api-gateway-url/dev/status/{imageHash} (preflight)
```

## Testing CORS Locally

### 1. **Browser Console Test**

```javascript
// Test preflight request
fetch("https://your-api-gateway-url/dev/upload", {
  method: "OPTIONS",
  headers: {
    "Content-Type": "application/json",
    "Access-Control-Request-Method": "POST",
  },
}).then((response) => {
  console.log("CORS headers:", response.headers);
});

// Test actual POST request - NO AUTH REQUIRED!
fetch("https://your-api-gateway-url/dev/upload", {
  method: "POST",
  headers: {
    "Content-Type": "application/json",
    // NO Authorization header needed!
    // NO API key required!
  },
  body: JSON.stringify({
    /* your data */
  }),
})
  .then((response) => response.json())
  .then((data) => console.log(data));
```

### 2. **curl Testing**

```bash
# Test OPTIONS preflight
curl -X OPTIONS \
  -H "Origin: http://localhost:3000" \
  -H "Access-Control-Request-Method: POST" \
  -H "Access-Control-Request-Headers: Content-Type" \
  -v https://your-api-gateway-url/dev/upload

# Test POST with CORS - NO AUTH REQUIRED!
curl -X POST \
  -H "Origin: http://localhost:3000" \
  -H "Content-Type: application/json" \
  -d '{"test": "data"}' \
  -v https://your-api-gateway-url/dev/upload
# Note: No Authorization header or API key needed!
```

### 3. **Local Development Setup**

#### React/Vue/Angular Apps

```javascript
// No additional configuration needed
// CORS is handled server-side by API Gateway

const API_BASE_URL = "https://your-api-gateway-url/dev";

// Upload example
const uploadFile = async (file) => {
  const response = await fetch(`${API_BASE_URL}/upload`, {
    method: "POST",
    body: file,
  });
  return response.json();
};

// Status check example
const checkStatus = async (imageHash) => {
  const response = await fetch(`${API_BASE_URL}/status/${imageHash}`);
  return response.json();
};
```

#### Node.js/Express Development Server

```javascript
// No CORS middleware needed on your dev server
// API Gateway handles all CORS headers

app.get("/api/*", (req, res) => {
  // Proxy to API Gateway - CORS already handled
  proxy("https://your-api-gateway-url/dev")(req, res);
});
```

## Common CORS Issues and Solutions

### 1. **"No 'Access-Control-Allow-Origin' header"**

- ✅ **Fixed**: All endpoints return proper CORS headers
- The API Gateway now includes CORS headers on all responses

### 2. **"CORS preflight failed"**

- ✅ **Fixed**: OPTIONS methods properly configured
- Preflight requests return all required headers

### 3. **"Method not allowed in CORS policy"**

- ✅ **Fixed**: All HTTP methods are allowed
- Supports DELETE, GET, HEAD, OPTIONS, PATCH, POST, PUT

### 4. **"Header not allowed in CORS policy"**

- ✅ **Fixed**: Comprehensive header list included
- Common headers like Content-Type, Authorization, X-Requested-With are allowed

## Deployment Notes

After deploying with `terraform apply`, the API Gateway will automatically:

- Handle all CORS preflight requests
- Add CORS headers to all API responses
- Support requests from any origin (including localhost)
- Cache preflight responses for 24 hours to improve performance

## No Authentication Configuration

### ✅ **What's Disabled**

- **No Authorization Required**: All methods set to `authorization = "NONE"`
- **No API Keys**: All methods have `api_key_required = false`
- **No AWS Cognito**: No user pools or identity pools configured
- **No Lambda Authorizers**: No custom authorization functions
- **No IAM Authorization**: No AWS credentials required for API calls

### 🎯 **Perfect for Development**

```bash
# These work without ANY authentication:
curl -X POST https://your-api-gateway-url/dev/upload
curl -X GET https://your-api-gateway-url/dev/status/abc123

# JavaScript - no auth headers needed:
fetch('https://your-api-gateway-url/dev/upload', { method: 'POST' })
```

### ⚠️ **Production Considerations**

For production deployment, consider adding:

- API keys for rate limiting: `api_key_required = true`
- AWS Cognito for user authentication
- Lambda authorizers for custom auth logic
- Resource-based policies for IP restrictions

## Security Considerations

**For Production**: Consider restricting `Access-Control-Allow-Origin` to specific domains:

```terraform
# In terraform/modules/api-gateway/main.tf
# Change from "*" to specific domains like:
"gatewayresponse.header.Access-Control-Allow-Origin" = "'https://your-production-domain.com'"
```

**Authentication Options for Later**:

```terraform
# To add API key requirement later:
api_key_required = true

# To add AWS Cognito authorization:
authorization = "COGNITO_USER_POOLS"
authorizer_id = aws_api_gateway_authorizer.cognito.id
```

## Monitoring CORS

Check CloudWatch logs for CORS-related errors:

- API Gateway execution logs
- Lambda function logs
- Browser developer console network tab
