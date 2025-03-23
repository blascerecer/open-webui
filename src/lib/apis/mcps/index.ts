import { MCP_RUN_PROFILE_NAME, MCP_RUN_PROFILE_ID, MCP_RUN_SESSION_ID, MCP_BRIDGE_API_BASE_URL } from '$lib/constants';

/**
 * Gets the required MCP environment variables
 * @returns Object containing required MCP environment variables
 * @throws Error if any required variables are missing
 */
const getMCPEnvironmentVars = () => {
  const profileName = MCP_RUN_PROFILE_NAME;
  const profileId = MCP_RUN_PROFILE_ID;
  const sessionId = MCP_RUN_SESSION_ID;
  
  if (!profileName || !profileId || !sessionId) {
    throw new Error('Missing required environment variables for MCP operations');
  }
  
  return { profileName, profileId, sessionId };
};

export const getActiveTools = async (token: string = ''): Promise<any[]> => {
  let error = null;
  
  const res = await fetch(`${MCP_BRIDGE_API_BASE_URL}mcp/tools`, {
    method: 'GET',
    headers: {
      Accept: 'application/json',
      'Content-Type': 'application/json',
      ...(token && { authorization: `Bearer ${token}` })
    }
  })
    .then(async (res) => {
      if (!res.ok) throw await res.json();
      const json = await res.json();
      console.log('getMCPServers: ', json);
      return json;
    })
    .catch((err) => {
      error = err;
      console.log(err);
      return null;
    });
  
  if (error) {
    throw error;
  }

  console.log('getActiveTools: ', res);
  
  // Extract the tools array from the mcpx object
  return res?.mcpx?.tools || [];
};


/**
 * Fetches installed servlets on an MCP profile
 * @param token Optional authentication token (not used if session ID is available)
 * @returns Array of installed servlet names
 */
export const getActiveMCPServers = async (token: string = ''): Promise<string[]> => {
  console.log('getActiveMCPServers: ', token);
  try {
    // Get environment variables
    const { profileName, profileId, sessionId } = getMCPEnvironmentVars();
    
    // Use the proxy path instead of direct URL
    // This will route through your Vite dev server using the proxy configuration
    const response = await fetch(`/mcp-api/profiles/${profileId}/${profileName}/installations`, {
      method: 'GET',
      headers: {
        Accept: 'application/json',
        'Content-Type': 'application/json',
        'Cookie': `api-key=${sessionId}`
      }
    });

    console.log('getMCPServers: ', JSON.stringify(response, null, 2));
    
    if (!response.ok) {
      const errorText = await response.text();
      try {
        const errorData = JSON.parse(errorText);
        throw errorData;
      } catch (parseError) {
        throw new Error(`Failed to fetch MCP servlets: ${errorText.substring(0, 100)}...`);
      }
    }
    
    const installationData = await response.json();
    console.log('getMCPServers: ', installationData);
    
    // Extract server names from the installation data
    // Note: Adjust this extraction logic based on the actual response structure
    return Array.isArray(installationData) 
      ? installationData.map(installation => installation.name) 
      : Object.keys(installationData);
    
  } catch (error) {
    console.error('Error fetching MCP servers:', error);
    throw error;
  }
};

/**
 * Updates the MCP server configuration
 * @param name Name of the installation
 * @param servletSlug The slug of the servlet to install
 * @param configSettings Configuration settings for the servlet
 * @param networkSettings Network settings (domains)
 * @param filesystemSettings Filesystem settings (volumes)
 * @param allowUpdate Whether to allow updates to existing installations
 * @returns Promise that resolves with the installation result
 */
export const addMCPServer = async (
  name: string,
  servletSlug: string,
  configSettings: Record<string, any> = {},
  networkSettings: { enabled: boolean, domains: string[] } = { enabled: true, domains: [] },
  filesystemSettings: { enabled: boolean, volumes: Record<string, string> } = { enabled: true, volumes: {} },
  allowUpdate: boolean = true
): Promise<any> => {
  try {
    // Get environment variables using the shared function
    const { profileName, profileId, sessionId } = getMCPEnvironmentVars();
    
    // Log input parameters
    console.log('Function called with parameters:');
    console.log('name:', name);
    console.log('servletSlug:', servletSlug);
    console.log('configSettings:', JSON.stringify(configSettings, null, 2));
    console.log('networkSettings:', JSON.stringify(networkSettings, null, 2));
    console.log('filesystemSettings:', JSON.stringify(filesystemSettings, null, 2));
    console.log('sessionid:', sessionId);
    
    // Prepare request body
    const requestBody = {
      name,
      servlet_slug: servletSlug,
      allow_update: allowUpdate,
      settings: {
        config: configSettings,
        network: networkSettings,
        filesystem: filesystemSettings
      }
    };
    
    // Use the proxy path instead of direct URL
    console.log('Sending request to:', `/mcp-api/profiles/${profileId}/${profileName}/installations`);
    console.log('Request body:', JSON.stringify(requestBody, null, 2));
    
    const response = await fetch(`/mcp-api/profiles/${profileId}/${profileName}/installations`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Cookie': `api-key=${sessionId}`
      },
      body: JSON.stringify(requestBody),
    });
    
    console.log('Response status:', response.status);
    console.log('Response status text:', response.statusText);
    
    if (!response.ok) {
      const text = await response.text();
      console.error('Error response body:', text);
      try {
        const errorData = JSON.parse(text);
        console.error('Parsed error data:', errorData);
        throw new Error(errorData.detail || 'Failed to install MCP servlet');
      } catch (parseError) {
        console.error('Failed to parse error response as JSON:', parseError);
        throw new Error(`Failed to install MCP servlet: ${text.substring(0, 100)}...`);
      }
    }
    
    const result = await response.json();
    console.log('Installation successful. Result data:', JSON.stringify(result, null, 2));
    
    return result;
  } catch (error) {
    console.error('Exception caught while installing MCP servlet:', error);
    console.error('Error stack:', error.stack);
    throw error;
  }
};

export async function refreshActiveMCPs({
  onStart = () => {},           // Callback when loading starts
  onSuccess = (serverNames) => {}, // Callback when loading succeeds
  onError = (error) => {},      // Callback when error occurs
  onFinish = () => {}           // Callback when loading finishes (success or error)
} = {}) {
  try {
    // Signal loading has started
    onStart();
    
    // Fetch the MCP servers
    const serverNames = await getActiveMCPServers();
    console.log("Fetched server names:", serverNames);
    
    // Call success callback with the server names
    onSuccess(serverNames);
    
    return serverNames;
  } catch (err) {
    console.error('Failed to fetch active MCP servers:', err);
    
    // Extract the error message from the response if possible
    let processedError;
    
    if (err.response && err.response.json) {
      try {
        const errorData = await err.response.json();
        processedError = errorData;
      } catch (jsonError) {
        // If can't parse as JSON, use the raw error
        processedError = err;
      }
    } else if (err.json) {
      // Some fetch implementations might have the json method directly on the error
      try {
        const errorData = await err.json();
        processedError = errorData;
      } catch (jsonError) {
        processedError = err;
      }
    } else {
      // Fallback to the raw error
      processedError = err;
    }
    
    // Call error callback with the processed error
    onError(processedError);
    
    // Re-throw the processed error for proper error handling
    throw processedError;
  } finally {
    // Signal loading has finished (regardless of success or error)
    onFinish();
  }
}
