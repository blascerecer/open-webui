import { MCP_BRIDGE_API_BASE_URL } from '$lib/constants';

interface MCPServerConfig {
  command: string;
  env: Record<string, string>;
}

/**
 * Smithery Registry Client
 * 
 * TypeScript functions to interact with the Smithery Registry API.
 * Allows developers to discover MCP servers that can be installed or integrated
 * into their applications.
 */

// Server response interfaces based on the documentation
interface ServerListResponse {
  servers: Array<{
    qualifiedName: string;
    displayName: string;
    description: string;
    homepage: string;
    useCount: string;
    isDeployed: boolean;
    createdAt: string;
  }>;
  pagination: {
    currentPage: number;
    pageSize: number;
    totalPages: number;
    totalCount: number;
  };
}

interface ServerDetailsResponse {
  qualifiedName: string;
  displayName: string;
  deploymentUrl: string;
  connections: Array<{
    type: string;
    url?: string;
    configSchema: any; // JSONSchema
  }>;
}

interface SearchOptions {
  query?: string;
  owner?: string;
  repo?: string;
  isDeployed?: boolean;
  page?: number;
  pageSize?: number;
}

/**
 * Fetches MCP server names by calling the /mcp/tools endpoint
 * @param token Optional authentication token
 * @returns Array of MCP server names
 */
export const getMCPServers = async (token: string = ''): Promise<string[]> => {
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
    .then((json) => {
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
  
  // Extract server names (keys) from the response object
  return Object.keys(res);
};

/**
 * Updates the MCP server configuration
 * @param serverConfigs Object containing server configurations where keys are server IDs and values are their configurations
 * @param serversToRemove Array of server IDs to remove
 * @returns Promise that resolves with the update result
 */
export const updateActiveMCPServers = async (
  serverConfigs: Record<string, any> = {},
  serversToRemove: string[] = []
): Promise<any> => {
  try {
    // Log input parameters
    console.log('Function called with parameters:');
    console.log('serverConfigs:', JSON.stringify(serverConfigs, null, 2));
    console.log('serversToRemove:', serversToRemove);
  
    // Extract server IDs to add from the configs object
    const serversToAdd = Object.keys(serverConfigs);
    console.log('Servers to add:', serversToAdd);
    
    // Log request data before sending
    const requestBody = { 
      serversToAdd, 
      serverConfigs: serverConfigs, // Make sure this matches the backend Pydantic model
      serversToRemove 
    };
    console.log('Sending request to:', `${MCP_BRIDGE_API_BASE_URL}mcp/tools/servers/update`);
    console.log('Request body:', JSON.stringify(requestBody, null, 2));
    
    const response = await fetch(`${MCP_BRIDGE_API_BASE_URL}mcp/tools/servers/update`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
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
        throw new Error(errorData.detail || 'Failed to update MCP servers');
      } catch (parseError) {
        console.error('Failed to parse error response as JSON:', parseError);
        throw new Error(`Failed to update MCP servers: ${text.substring(0, 100)}...`);
      }
    }
    
    const result = await response.json();
    console.log('Update successful. Result data:', JSON.stringify(result, null, 2));
    
    // Process and handle server installation failures
    if (result.changes && result.changes.installation_failed && result.changes.installation_failed.length > 0) {
      console.warn('Some servers failed to install:', result.changes.installation_failed);
      // You could add UI notifications here
    }
    
    // Log any specific success metrics or important return values
    if (result.changes) {
      if (result.changes.added) console.log('Added servers:', result.changes.added);
      if (result.changes.updated) console.log('Updated servers:', result.changes.updated);
      if (result.changes.removed) console.log('Removed servers:', result.changes.removed);
    }
    
    return result;
  } catch (error) {
    console.error('Exception caught while updating MCP server configuration:', error);
    console.error('Error stack:', error.stack);
    throw error;
  }
};

/**
 * Fetches detailed information about a specific MCP server
 * 
 * @param qualifiedName The qualified name of the MCP server
 * @returns Promise resolving to the server details
 */
export async function fetchMCPDetails(
  qualifiedName: string
): Promise<ServerDetailsResponse> {
  // UPDATED: Use proxy path instead of direct API URL
  const apiUrl = `/smithery-api/registry/servers/${encodeURIComponent(qualifiedName)}`;
  
  try {
    console.log(`Fetching MCP details via proxy for: ${qualifiedName}`);
    const response = await fetch(apiUrl, {
      headers: {
        'Accept': 'application/json',
      }
    });
    
    if (!response.ok) {
      throw new Error(`Failed to fetch MCP details: ${response.status} ${response.statusText}`);
    }
    
    return await response.json();
    
  } catch (error) {
    console.error(`Error fetching details for MCP ${qualifiedName}:`, error);
    
    // Provide a fallback for Brave Search during development
    if (qualifiedName === '@smithery-ai/brave-search') {
      console.log('Using fallback data for Brave Search');
      return {
        qualifiedName: '@smithery-ai/brave-search',
        displayName: 'Brave Search',
        deploymentUrl: 'https://server.smithery.ai/@smithery-ai/brave-search',
        connections: [
          {
            type: 'ws',
            deploymentUrl: 'https://server.smithery.ai/@smithery-ai/brave-search',
            configSchema: {
              type: 'object',
              required: ['braveApiKey'],
              properties: {
                braveApiKey: {
                  type: 'string',
                  description: 'The API key for the BRAVE Search server.'
                }
              }
            }
          }
        ]
      };
    }
    
    throw error;
  }
}

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
    const serverNames = await getMCPServers();
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

/**
 * Creates a WebSocket URL for connecting to a Smithery MCP server
 * 
 * @param serverUrl The base URL of the server
 * @param config Configuration object matching the server's schema
 * @returns Formatted WebSocket URL with encoded config
 */
export function createSmitheryWebSocketUrl(
  serverUrl: string,
  config: Record<string, any>
): string {
  // Base64 encode the config object
  const encodedConfig = btoa(JSON.stringify(config));
  
  // Format: https://server.smithery.ai/${qualifiedName}/ws?config=${base64encode(config)}
  return `${serverUrl}?config=${encodedConfig}`;
};