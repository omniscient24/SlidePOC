# Salesforce OAuth Implementation for Navigator

This implementation adds OAuth authentication support to the Navigator application, making the security token optional.

## Features

1. **OAuth 2.0 Authentication** - Secure authentication without sharing passwords
2. **Optional Security Token** - Works with IP whitelisting
3. **Dual Authentication Methods** - Users can choose between OAuth or traditional login

## Setup Instructions

### 1. Create a Connected App in Salesforce

1. Go to Setup → App Manager → New Connected App
2. Fill in the basic information:
   - Connected App Name: Navigator OAuth
   - API Name: Navigator_OAuth
   - Contact Email: your-email@example.com

3. Enable OAuth Settings:
   - Check "Enable OAuth Settings"
   - Callback URL: 
     - Development: `http://localhost:3000/api/salesforce/oauth/callback`
     - Production: `https://your-domain.com/api/salesforce/oauth/callback`
   - Select OAuth Scopes:
     - Access and manage your data (api)
     - Access your basic information (id)
     - Access unique user identifiers (openid)
     - Perform requests on your behalf at any time (refresh_token, offline_access)
     - Access custom permissions (custom_permissions)
     - Provide access to your data via the Web (web)

4. Save the Connected App

5. After saving, note down:
   - Consumer Key (Client ID)
   - Consumer Secret (Client Secret)

### 2. Configure Environment Variables

Update your `.env.local` file with the OAuth credentials:

```env
# Salesforce OAuth Configuration
SF_OAUTH_CLIENT_ID=your_consumer_key_here
SF_OAUTH_CLIENT_SECRET=your_consumer_secret_here
NEXT_PUBLIC_APP_URL=http://localhost:3000
```

### 3. Apply the Code Changes

Copy the following files to your Navigator project:

1. **OAuth Routes:**
   - Copy `api/salesforce/oauth/route.ts` to `navigator/app/api/salesforce/oauth/route.ts`
   - Copy `api/salesforce/oauth/callback/route.ts` to `navigator/app/api/salesforce/oauth/callback/route.ts`

2. **Updated Connect Route:**
   - Replace `navigator/app/api/salesforce/connect/route.ts` with the new version

3. **Updated UI Component:**
   - Replace `navigator/components/SalesforceOrgSelector.tsx` with the new version

### 4. IP Whitelisting (Optional)

To use the traditional login without a security token:

1. Go to Setup → Security → Network Access
2. Click "New"
3. Add your IP address or IP range
4. Save

## Usage

### OAuth Authentication (Recommended)
1. Select "OAuth" as the connection method
2. Choose your organization type
3. Click "Connect with Salesforce OAuth"
4. Log in to Salesforce when prompted
5. Authorize the application

### Traditional Authentication
1. Select "Username & Password" as the connection method
2. Enter your credentials
3. Security token is now optional:
   - If your IP is whitelisted: Leave security token blank
   - If not whitelisted: Enter your security token

## Security Benefits

1. **OAuth Benefits:**
   - No password stored in the application
   - Automatic token refresh
   - Can be revoked from Salesforce at any time
   - Follows Salesforce security best practices

2. **IP Whitelisting Benefits:**
   - No need to manage security tokens
   - Simpler login process
   - Still secure when combined with strong passwords

## Troubleshooting

### OAuth Issues
- Ensure the callback URL in your Connected App matches your environment
- Check that all required OAuth scopes are selected
- Verify environment variables are set correctly

### Traditional Login Issues
- If login fails without security token, check IP whitelisting
- The error message will guide you on what to do
- You can always fall back to using a security token

## Migration Notes

- Existing saved organizations with security tokens will continue to work
- Users can gradually migrate to OAuth at their own pace
- No breaking changes to existing functionality