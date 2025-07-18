import { NextResponse } from 'next/server';
import jsforce from 'jsforce';

export async function POST(request: Request) {
  try {
    const body = await request.json();
    console.log('Received connection request for org type:', body.orgType);

    const { orgType, username, password, securityToken } = body;

    if (!orgType || !username || !password) {
      return NextResponse.json(
        { 
          success: false, 
          error: 'Missing required fields (username and password are required)' 
        },
        { status: 400 }
      );
    }

    // Determine login URL based on org type
    const loginUrl = orgType === 'sandbox' 
      ? 'https://test.salesforce.com' 
      : 'https://login.salesforce.com';

    console.log('Attempting connection to:', loginUrl);

    // Create connection
    const conn = new jsforce.Connection({
      loginUrl,
    });

    // Attempt to login
    try {
      // First try without security token (works if IP is whitelisted)
      console.log('Attempting login without security token (IP whitelist)...');
      await conn.login(username, password);
      console.log('Successfully connected to Salesforce (IP whitelisted)');
    } catch (firstAttemptError) {
      console.log('Login without security token failed, trying with token...');
      
      // If first attempt fails and we have a security token, try with it
      if (securityToken) {
        try {
          await conn.login(username, password + securityToken);
          console.log('Successfully connected to Salesforce with security token');
        } catch (secondAttemptError) {
          console.error('Login with security token also failed:', secondAttemptError);
          throw new Error('Login failed. Please check your credentials and security token.');
        }
      } else {
        // No security token provided, give helpful error message
        throw new Error(
          'Login failed. Either:\n' +
          '1. Add your IP address to Network Access in Salesforce Setup, or\n' +
          '2. Provide your security token, or\n' +
          '3. Use OAuth authentication instead'
        );
      }
    }
    
    // Get organization info
    const org = await conn.query('SELECT Name, OrganizationType FROM Organization LIMIT 1');
    const orgInfo = org.records[0] as any;
    
    return NextResponse.json({
      success: true,
      userInfo: {
        ...conn.userInfo,
        organizationName: orgInfo.Name,
        organizationType: body.orgType,
        url: conn.instanceUrl,
      },
      accessToken: conn.accessToken,
      instanceUrl: conn.instanceUrl,
    });
  } catch (error) {
    console.error('Request processing error:', error);
    return NextResponse.json(
      { 
        success: false, 
        error: error instanceof Error ? error.message : 'Failed to process request' 
      },
      { status: 400 }
    );
  }
}