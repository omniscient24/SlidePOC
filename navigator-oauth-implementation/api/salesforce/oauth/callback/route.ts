import { NextResponse } from 'next/server';
import jsforce from 'jsforce';

const oauth2 = new jsforce.OAuth2({
  clientId: process.env.SF_OAUTH_CLIENT_ID!,
  clientSecret: process.env.SF_OAUTH_CLIENT_SECRET!,
  redirectUri: `${process.env.NEXT_PUBLIC_APP_URL}/api/salesforce/oauth/callback`
});

export async function GET(request: Request) {
  try {
    const { searchParams } = new URL(request.url);
    const code = searchParams.get('code');
    const state = searchParams.get('state');
    
    if (!code) {
      return NextResponse.redirect(`${process.env.NEXT_PUBLIC_APP_URL}/org-login?error=no_code`);
    }
    
    // Parse state to get org type
    let orgType = 'production';
    try {
      const stateData = JSON.parse(state || '{}');
      orgType = stateData.orgType || 'production';
    } catch (e) {
      console.error('Failed to parse state:', e);
    }
    
    // Determine login URL based on org type
    const loginUrl = orgType === 'sandbox' 
      ? 'https://test.salesforce.com' 
      : 'https://login.salesforce.com';
    
    // Create connection with appropriate login URL
    const conn = new jsforce.Connection({
      oauth2: oauth2,
      loginUrl: loginUrl
    });
    
    // Authorize with the code
    await conn.authorize(code);
    
    // Get user and org info
    const userInfo = await conn.identity();
    const org = await conn.query('SELECT Name, OrganizationType FROM Organization LIMIT 1');
    const orgInfo = org.records[0] as any;
    
    // Prepare connection data
    const connectionData = {
      success: true,
      userInfo: {
        id: userInfo.user_id,
        organizationId: userInfo.organization_id,
        url: conn.instanceUrl,
        username: userInfo.username,
        displayName: userInfo.display_name,
        email: userInfo.email,
        organizationName: orgInfo.Name,
        organizationType: orgType,
      },
      accessToken: conn.accessToken,
      refreshToken: conn.refreshToken,
      instanceUrl: conn.instanceUrl,
    };
    
    // Encode connection data for client-side storage
    const encodedData = Buffer.from(JSON.stringify(connectionData)).toString('base64');
    
    // Redirect to success page with connection data
    return NextResponse.redirect(
      `${process.env.NEXT_PUBLIC_APP_URL}/org-login?oauth=success&data=${encodedData}`
    );
    
  } catch (error) {
    console.error('OAuth callback error:', error);
    return NextResponse.redirect(
      `${process.env.NEXT_PUBLIC_APP_URL}/org-login?error=oauth_failed&message=${encodeURIComponent(error instanceof Error ? error.message : 'OAuth authentication failed')}`
    );
  }
}