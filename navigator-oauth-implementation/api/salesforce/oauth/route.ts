import { NextResponse } from 'next/server';
import jsforce from 'jsforce';

// OAuth 2.0 configuration
const oauth2 = new jsforce.OAuth2({
  clientId: process.env.SF_OAUTH_CLIENT_ID!,
  clientSecret: process.env.SF_OAUTH_CLIENT_SECRET!,
  redirectUri: `${process.env.NEXT_PUBLIC_APP_URL}/api/salesforce/oauth/callback`
});

export async function GET(request: Request) {
  const { searchParams } = new URL(request.url);
  const orgType = searchParams.get('orgType') || 'production';
  
  // Determine login URL based on org type
  const loginUrl = orgType === 'sandbox' 
    ? 'https://test.salesforce.com' 
    : 'https://login.salesforce.com';
  
  // Store org type in state parameter for callback
  const state = JSON.stringify({ orgType });
  
  // Generate authorization URL
  const authUrl = oauth2.getAuthorizationUrl({
    scope: 'api id web refresh_token offline_access',
    state: state,
    prompt: 'login' // Force re-authentication
  });
  
  // Override the base URL with the correct login URL
  const finalAuthUrl = authUrl.replace('https://login.salesforce.com', loginUrl);
  
  return NextResponse.redirect(finalAuthUrl);
}