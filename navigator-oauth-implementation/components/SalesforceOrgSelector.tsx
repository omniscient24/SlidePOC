'use client';

import React, { useState, useEffect, useCallback } from 'react';
import { Settings, ChevronDown, Trash2, Key, Cloud } from 'lucide-react';
import { useSalesforce } from '../context/SalesforceContext';
import { SuccessModal } from './SuccessModal';
import { useRouter, useSearchParams } from 'next/navigation';

interface SalesforceCredentials {
  name: string;
  orgType: 'sandbox' | 'production' | 'developer';
  username: string;
  password: string;
  securityToken: string;
}

interface SavedOrg {
  name: string;
  username: string;
  orgType: 'sandbox' | 'production' | 'developer';
  password: string;
  securityToken: string;
}

const SalesforceOrgSelector = () => {
  const { setConnection } = useSalesforce();
  const router = useRouter();
  const searchParams = useSearchParams();
  
  const [authMethod, setAuthMethod] = useState<'oauth' | 'credentials'>('oauth');
  const [credentials, setCredentials] = useState<SalesforceCredentials>({
    name: '',
    orgType: 'sandbox',
    username: '',
    password: '',
    securityToken: '',
  });
  const [savedOrgs, setSavedOrgs] = useState<SavedOrg[]>([]);
  const [isConnecting, setIsConnecting] = useState(false);
  const [error, setError] = useState('');
  const [showSavedOrgs, setShowSavedOrgs] = useState(false);
  const [showSuccessModal, setShowSuccessModal] = useState(false);
  const [successMessage, setSuccessMessage] = useState('');

  // Check for OAuth callback
  useEffect(() => {
    const oauth = searchParams.get('oauth');
    const data = searchParams.get('data');
    const errorParam = searchParams.get('error');
    const errorMessage = searchParams.get('message');
    
    if (oauth === 'success' && data) {
      try {
        const connectionData = JSON.parse(Buffer.from(data, 'base64').toString());
        setConnection(connectionData);
        setSuccessMessage(`Successfully connected to ${connectionData.userInfo.organizationName} via OAuth`);
        setShowSuccessModal(true);
        
        // Clear URL parameters
        router.replace('/org-login');
      } catch (err) {
        console.error('Failed to process OAuth callback:', err);
        setError('Failed to process OAuth authentication');
      }
    } else if (errorParam) {
      setError(errorMessage || 'OAuth authentication failed');
    }
  }, [searchParams, setConnection, router]);

  // Load saved orgs
  useEffect(() => {
    const saved = localStorage.getItem('salesforceOrgs');
    if (saved) {
      try {
        const parsedOrgs = JSON.parse(saved);
        console.log('Loading saved orgs:', parsedOrgs);
        // Ensure all required fields are present
        const validatedOrgs = parsedOrgs.map((org: SavedOrg) => ({
          name: org.name || '',
          username: org.username || '',
          orgType: org.orgType || 'sandbox',
          password: org.password || '',
          securityToken: org.securityToken || ''
        }));
        setSavedOrgs(validatedOrgs);
      } catch (err) {
        console.error('Error loading saved orgs:', err);
      }
    }
  }, []);

  const handleOAuthConnect = useCallback(() => {
    setIsConnecting(true);
    setError('');
    
    // Redirect to OAuth endpoint
    window.location.href = `/api/salesforce/oauth?orgType=${credentials.orgType}`;
  }, [credentials.orgType]);

  const handleConnect = useCallback(async (e: React.FormEvent) => {
    console.log('handleConnect triggered');
    e.preventDefault();
    setIsConnecting(true);
    setError('');

    try {
      console.log('Attempting to connect with credentials:', {
        ...credentials,
        password: '[HIDDEN]',
        securityToken: credentials.securityToken ? '[HIDDEN]' : 'NOT PROVIDED'
      });

      const response = await fetch('/api/salesforce/connect', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(credentials),
      });

      const result = await response.json();

      if (!response.ok || !result.success) {
        throw new Error(result.error || 'Failed to connect to Salesforce');
      }

      console.log('Connection successful:', result);
      
      // Add credentials to the result for reconnection functionality
      const resultWithCredentials = {
        ...result,
        password: credentials.password,
        securityToken: credentials.securityToken
      };
      
      setConnection(resultWithCredentials);
      setError(''); // Clear any previous errors

      // Save the org details only if a security token was provided
      if (credentials.securityToken) {
        const newOrg: SavedOrg = {
          name: credentials.name || credentials.username.split('@')[0], // Use custom name or fallback to username
          username: credentials.username,
          orgType: credentials.orgType,
          password: credentials.password,
          securityToken: credentials.securityToken
        };

        // Update saved orgs
        const updatedOrgs = [...savedOrgs.filter(org => org.username !== newOrg.username), newOrg];
        setSavedOrgs(updatedOrgs);
        localStorage.setItem('salesforceOrgs', JSON.stringify(updatedOrgs));
      }

      // Clear the form
      setCredentials({
        name: '',
        orgType: 'sandbox',
        username: '',
        password: '',
        securityToken: '',
      });

      // Show success modal
      setSuccessMessage(`Successfully connected to ${result.userInfo.organizationName}`);
      setShowSuccessModal(true);

    } catch (err) {
      console.error('Connection error:', err);
      setError(err instanceof Error ? err.message : 'An error occurred while connecting');
    } finally {
      setIsConnecting(false);
    }
  }, [credentials, setConnection, savedOrgs, setIsConnecting, setError, setSavedOrgs, setCredentials, setSuccessMessage, setShowSuccessModal]);

  const handleSelectSavedOrg = (org: SavedOrg) => {
    console.log('Selecting org:', org);
    
    // Create new credentials object with all saved fields
    const newCredentials: SalesforceCredentials = {
      name: org.name || '',
      orgType: org.orgType || 'sandbox',
      username: org.username || '',
      password: org.password || '',
      securityToken: org.securityToken || ''
    };
    
    console.log('Setting new credentials:', {
      ...newCredentials,
      password: newCredentials.password ? '[HIDDEN]' : '',
      securityToken: newCredentials.securityToken ? '[HIDDEN]' : ''
    });
    
    setCredentials(newCredentials);
    setShowSavedOrgs(false);
    setAuthMethod('credentials'); // Switch to credentials method
  };

  const handleDeleteOrg = useCallback((orgToDelete: SavedOrg, event: React.MouseEvent) => {
    event.stopPropagation(); // Prevent triggering the parent button's onClick
    
    const updatedOrgs = savedOrgs.filter(org => org.username !== orgToDelete.username);
    setSavedOrgs(updatedOrgs);
    
    localStorage.setItem('salesforceOrgs', JSON.stringify(updatedOrgs));
    
    // Reset credentials if the deleted org was selected
    if (credentials.username === orgToDelete.username) {
      setCredentials({
        name: '',
        orgType: 'sandbox',
        username: '',
        password: '',
        securityToken: '',
      });
    }
    
    if (updatedOrgs.length === 0) {
      setShowSavedOrgs(false);
    }
  }, [credentials.username, savedOrgs]);

  return (
    <div className="bg-white p-6 rounded-lg shadow-lg max-w-md w-full mx-auto">
      <div className="flex items-center mb-6">
        <Settings className="h-6 w-6 text-blue-600 mr-2" />
        <h2 className="text-xl font-semibold">Connect to Salesforce</h2>
      </div>

      {/* Auth Method Selector */}
      <div className="mb-6">
        <label className="block text-sm font-medium text-gray-700 mb-2">
          Connection Method
        </label>
        <div className="grid grid-cols-2 gap-2">
          <button
            type="button"
            onClick={() => setAuthMethod('oauth')}
            className={`flex items-center justify-center px-4 py-2 rounded-md border ${
              authMethod === 'oauth'
                ? 'border-blue-500 bg-blue-50 text-blue-700'
                : 'border-gray-300 bg-white text-gray-700 hover:bg-gray-50'
            }`}
          >
            <Cloud className="h-4 w-4 mr-2" />
            OAuth (Recommended)
          </button>
          <button
            type="button"
            onClick={() => setAuthMethod('credentials')}
            className={`flex items-center justify-center px-4 py-2 rounded-md border ${
              authMethod === 'credentials'
                ? 'border-blue-500 bg-blue-50 text-blue-700'
                : 'border-gray-300 bg-white text-gray-700 hover:bg-gray-50'
            }`}
          >
            <Key className="h-4 w-4 mr-2" />
            Username & Password
          </button>
        </div>
      </div>

      {/* Organization Type (for both methods) */}
      <div className="mb-6">
        <label className="block text-sm font-medium text-gray-700">
          Organization Type
        </label>
        <div className="relative mt-1">
          <select
            value={credentials.orgType}
            onChange={(e) => {
              const newType = e.target.value as SalesforceCredentials['orgType'];
              console.log('Changing org type to:', newType);
              setCredentials(prev => ({ ...prev, orgType: newType }));
            }}
            className="block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500 bg-white"
          >
            <option value="sandbox">Sandbox</option>
            <option value="production">Production</option>
            <option value="developer">Developer Edition</option>
          </select>
        </div>
      </div>

      {authMethod === 'oauth' ? (
        // OAuth Method
        <div className="space-y-4">
          <div className="bg-blue-50 border border-blue-200 rounded-md p-4">
            <h3 className="text-sm font-medium text-blue-900 mb-2">OAuth Authentication</h3>
            <p className="text-sm text-blue-700 mb-3">
              The most secure way to connect. You'll be redirected to Salesforce to log in.
            </p>
            <ul className="text-sm text-blue-600 space-y-1">
              <li>• No need to share your password</li>
              <li>• No security token required</li>
              <li>• Automatic token refresh</li>
            </ul>
          </div>

          <button
            type="button"
            onClick={handleOAuthConnect}
            disabled={isConnecting}
            className="w-full flex justify-center py-3 px-4 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-indigo-600 hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500 disabled:opacity-50"
          >
            {isConnecting ? 'Redirecting...' : 'Connect with Salesforce OAuth'}
          </button>
        </div>
      ) : (
        // Credentials Method
        <>
          {savedOrgs.length > 0 && (
            <div className="mb-6">
              <div className="relative">
                <button
                  type="button"
                  onClick={() => setShowSavedOrgs(!showSavedOrgs)}
                  className="w-full flex items-center justify-between px-4 py-2 border border-gray-300 rounded-md bg-white text-sm hover:bg-gray-50"
                >
                  <span>{credentials.username || 'Select a saved organization'}</span>
                  <ChevronDown className={`h-4 w-4 transform transition-transform ${showSavedOrgs ? 'rotate-180' : ''}`} />
                </button>
                
                {showSavedOrgs && (
                  <div className="absolute z-10 w-full mt-1 bg-white border border-gray-300 rounded-md shadow-lg max-h-60 overflow-auto">
                    {savedOrgs.map((org, index) => (
                      <div
                        key={index}
                        className="flex items-center justify-between px-4 py-2 hover:bg-gray-100 border-b border-gray-100 last:border-b-0"
                      >
                        <button
                          onClick={() => handleSelectSavedOrg(org)}
                          className="flex-1 text-left focus:outline-none"
                        >
                          <div className="font-medium text-gray-900">{org.name}</div>
                          <div className="text-sm text-gray-500">
                            {org.username} ({org.orgType})
                          </div>
                        </button>
                        <button
                          onClick={(e) => handleDeleteOrg(org, e)}
                          className="ml-2 p-1 text-gray-400 hover:text-red-500 focus:outline-none"
                          title="Delete organization"
                        >
                          <Trash2 className="h-4 w-4" />
                        </button>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            </div>
          )}

          <form onSubmit={handleConnect} className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-gray-700">
                Organization Name (Optional)
              </label>
              <input
                type="text"
                value={credentials.name}
                onChange={(e) => setCredentials(prev => ({ ...prev, name: e.target.value }))}
                placeholder="Enter a friendly name for this organization"
                className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700">
                Username
              </label>
              <input
                type="email"
                value={credentials.username}
                onChange={(e) => setCredentials(prev => ({ ...prev, username: e.target.value }))}
                className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500"
                required
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700">
                Password
              </label>
              <input
                type="password"
                value={credentials.password}
                onChange={(e) => setCredentials(prev => ({ ...prev, password: e.target.value }))}
                className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500"
                required
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700">
                Security Token (Optional)
              </label>
              <input
                type="password"
                value={credentials.securityToken}
                onChange={(e) => setCredentials(prev => ({ ...prev, securityToken: e.target.value }))}
                className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500"
                placeholder="Leave blank if your IP is whitelisted"
              />
              <p className="mt-1 text-xs text-gray-500">
                Not required if your IP address is added to Network Access in Salesforce Setup
              </p>
            </div>

            {error && (
              <div className="text-red-600 text-sm mt-2 whitespace-pre-line">{error}</div>
            )}

            <button
              type="submit"
              disabled={isConnecting}
              className="w-full flex justify-center py-3 px-4 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-indigo-600 hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500 disabled:opacity-50"
            >
              {isConnecting ? 'Connecting...' : 'Connect'}
            </button>
          </form>
        </>
      )}

      <SuccessModal
        isOpen={showSuccessModal}
        onClose={() => setShowSuccessModal(false)}
        message={successMessage}
      />
    </div>
  );
};

export default SalesforceOrgSelector;