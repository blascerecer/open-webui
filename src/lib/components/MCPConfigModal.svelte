<script lang="ts">
	import { toast } from 'svelte-sonner';
	import { createEventDispatcher } from 'svelte';
	import { onMount, getContext } from 'svelte';
	import Modal from './common/Modal.svelte';
	import Spinner from './common/Spinner.svelte';
	import { updateActiveMCPServers } from '$lib/apis/mcps';
	import { fetchMCPDetails } from '$lib/apis/mcps';

	const i18n = getContext('i18n');
	const dispatch = createEventDispatcher();

	export let show = false;
	export let server = null;

	let saving = false;
	let loading = false;
	let configData = {};
	let currentConfig = null;
	let serverDetails = null;
	let configSchema = null;
	let debugInfo = null;
	let secretVisibility = {}; // Track visibility state of secret fields

	// Fetch the server details and initialize form fields
	const initConfig = async () => {
		loading = true;
		
		try {
			if (!server) {
				throw new Error("No server provided");
			}
			
			if (!server.id) {
				throw new Error("Server has no ID");
			}
			
			// Try with qualifiedName if id doesn't work
			const serverIdToUse = server.qualifiedName || server.id;
			serverDetails = await fetchMCPDetails(serverIdToUse);
			
			// Get config schema from connections if available
			if (serverDetails && serverDetails.connections && serverDetails.connections.length > 0) {
				const connection = serverDetails.connections.find(conn => conn.configSchema);
				if (connection && connection.configSchema) {
					configSchema = connection.configSchema;
					
					// Initialize config data with properties from schema, excluding command and args
					if (configSchema.properties) {
						// Start with existing config values
						configData = { ...server.config };
						
						// Ensure all schema properties exist in configData with defaults
						Object.entries(configSchema.properties)
							.filter(([key]) => key !== 'command' && key !== 'args')
							.forEach(([key, prop]) => {
								if (configData[key] === undefined) {
									// Set default value based on property type
									if (prop.type === 'boolean') {
										configData[key] = false;
									} else if (prop.type === 'number') {
										configData[key] = 0;
									} else {
										configData[key] = '';
									}
								}
							});
					}
					
					// Store the schema for display purposes
					currentConfig = JSON.stringify(configSchema, null, 2);
				}
			} else {
				// Fallback to basic config if no schema available
				configData = { ...server.config };
				currentConfig = JSON.stringify(server.config, null, 2);
			}
		} catch (error) {
			console.error('Failed to fetch MCP details:', error);
			
			toast.error(`Failed to load configuration for ${server?.name || 'server'}. Error: ${error.message}`);
			
			// Fallback to basic config
			configData = server?.config ? { ...server.config } : {};
			currentConfig = server?.config ? JSON.stringify(server.config, null, 2) : null;
		} finally {
			loading = false;
		}
	};

	// Submit the configuration and add the server
	const submitHandler = async () => {
		saving = true;

		try {
			if (!server || !server.id) {
				throw new Error("Invalid server information");
			}
			
			// Filter out internal properties and keep only actual configuration values
			// Create a new object to hold only the user-entered config fields
			const configFields = {};
			
			// Identify fields that are likely part of the user configuration
			// and not internal implementation details
			Object.keys(configData).forEach(key => {
				// Exclude command, args, and other internal properties and empty values
				if (
					key !== 'command' && 
					key !== 'args' && 
					key !== 'id' &&
					key !== 'name' &&
					key !== 'qualifiedName' &&
					configData[key] !== undefined && 
					configData[key] !== null && 
					configData[key] !== ''
				) {
					configFields[key] = configData[key];
				}
			});
			
			// Example format of what we want: \"{\\\"spotifyClientId\\\":\\\"value\\\",\\\"spotifyClientSecret\\\":\\\"value\\\"}\"
			// First create the proper JSON string
			const jsonConfig = JSON.stringify(configFields);
			
			// Then apply the exact escaping pattern needed (one level of escaping for quotes)
			const escapedJsonConfig = jsonConfig.replace(/"/g, '\\"');
			
			// Then wrap in quotes with exactly the right format
			const configArgValue = `\"${escapedJsonConfig}\"`;
			
			// Build the server configs object
			const serverConfigs = {
				[server.id]: {
					"command": "npx",
					"args": [
						"-y",
						"@smithery/cli@latest",
						"run",
						server.qualifiedName || server.id,
						"--config",
						configArgValue
					]
				}
			};
			
			// Call API to add the server with configuration
			await updateActiveMCPServers(serverConfigs, []);
			
			// Show success message
			toast.success(`Added ${server.name}`);
			
			// Notify parent component that server was added
			dispatch('save', { server, added: true });
			
			// Close modal
			show = false;
		} catch (error) {
			console.error('Failed to add MCP server:', error);
			toast.error(`Failed to add ${server?.name || 'server'}. Error: ${error.message}`);
		} finally {
			saving = false;
		}
	};

	// Reset and initialize when modal is shown
	$: if (show) {
		// Reset secret visibility
		secretVisibility = {};
		if (server) {
			initConfig();
		}
	}
</script>

<Modal size="sm" bind:show class="z-[9999]">
	<div>
		<!-- Header section -->
		<div class="flex justify-between dark:text-gray-300 px-5 pt-4 pb-2 border-b border-gray-200 dark:border-gray-700">
			<div class="text-lg font-medium self-center">
				{#if server}
					Configure {server.name || 'Server'}
				{:else}
					Configure Server
				{/if}
			</div>
			<button
				class="self-center"
				on:click={() => {
					show = false;
				}}
			>
				<svg
					xmlns="http://www.w3.org/2000/svg"
					viewBox="0 0 20 20"
					fill="currentColor"
					class="w-5 h-5"
				>
					<path
						d="M6.28 5.22a.75.75 0 00-1.06 1.06L8.94 10l-3.72 3.72a.75.75 0 101.06 1.06L10 11.06l3.72 3.72a.75.75 0 101.06-1.06L11.06 10l3.72-3.72a.75.75 0 00-1.06-1.06L10 8.94 6.28 5.22z"
					/>
				</svg>
			</button>
		</div>

		<!-- Content section -->
		<div class="flex flex-col w-full px-5 py-4 dark:text-gray-200">
			{#if loading}
				<div class="flex justify-center py-4">
					<Spinner className="size-5" />
				</div>
			{:else if server}
				<!-- Server information section -->
				<div class="mb-4">
					<div class="flex flex-col space-y-3 mb-4">
						<!-- Description -->
						<p class="text-sm text-gray-700 dark:text-gray-300">
							{serverDetails?.description || server.description || 'Configure this server to add it to your workspace.'}
						</p>
						
						<!-- Smithery ID with Remote badge -->
						{#if server.qualifiedName}
							<div class="flex items-center">
								<span class="text-sm font-medium text-gray-700 dark:text-gray-300 mr-1">Smithery ID:</span>
								<span class="text-xs font-mono text-gray-600 dark:text-gray-400">
									{server.qualifiedName}
								</span>
								{#if serverDetails?.remote}
									<span class="ml-2 px-2 py-0.5 text-xs bg-blue-100 text-blue-800 dark:bg-blue-900 dark:text-blue-200 rounded">Remote</span>
								{/if}
							</div>
						{/if}
						
						<!-- Documentation link -->
						{#if server.url}
							<div class="text-sm">
								<span class="font-medium text-gray-700 dark:text-gray-300 mr-1">More info:</span> 
								<a href={server.url} target="_blank" rel="noopener noreferrer" class="text-blue-600 hover:underline dark:text-blue-400">
									View documentation
									<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20" fill="currentColor" class="w-4 h-4 inline-block ml-0.5 mb-0.5">
										<path fill-rule="evenodd" d="M4.25 5.5a.75.75 0 00-.75.75v8.5c0 .414.336.75.75.75h8.5a.75.75 0 00.75-.75v-4a.75.75 0 011.5 0v4A2.25 2.25 0 0112.75 17h-8.5A2.25 2.25 0 012 14.75v-8.5A2.25 2.25 0 014.25 4h5a.75.75 0 010 1.5h-5z" clip-rule="evenodd" />
										<path fill-rule="evenodd" d="M6.194 12.753a.75.75 0 001.06.053L16.5 4.44v2.81a.75.75 0 001.5 0v-4.5a.75.75 0 00-.75-.75h-4.5a.75.75 0 000 1.5h2.553l-9.056 8.194a.75.75 0 00-.053 1.06z" clip-rule="evenodd" />
									</svg>
								</a>
							</div>
						{/if}
					</div>
					
					{#if configSchema && configSchema.properties && Object.entries(configSchema.properties).filter(([key]) => key !== 'command' && key !== 'args').length > 0}
						<!-- Has configuration fields -->
						<div class="mt-3">
							<div class="text-sm font-medium text-gray-800 dark:text-gray-200 mb-2 px-1">
								Required Configuration:
							</div>
							<div class="space-y-4 mb-4">
								{#each Object.entries(configSchema.properties).filter(([key]) => key !== 'command' && key !== 'args') as [key, prop]}
									<div class="bg-white dark:bg-gray-800 p-3 rounded-md border border-gray-200 dark:border-gray-700">
										<label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1" for={`config-${key}`}>
											{key.charAt(0).toUpperCase() + key.slice(1).replace(/_/g, ' ')}
											{#if configSchema.required && configSchema.required.includes(key)}
												<span class="text-red-500 ml-0.5">*</span>
											{/if}
										</label>
										
										{#if prop.type === 'boolean'}
											<label class="inline-flex items-center">
												<input
													type="checkbox"
													id={`config-${key}`}
													bind:checked={configData[key]}
													class="rounded border-gray-300 text-blue-600 focus:ring-blue-500"
												/>
												<span class="ml-2 text-sm text-gray-700 dark:text-gray-300">Enabled</span>
											</label>
										{:else if prop.type === 'number'}
											<input
												type="number"
												id={`config-${key}`}
												bind:value={configData[key]}
												class="w-full px-3 py-2 text-sm border rounded-md dark:bg-gray-700 dark:border-gray-600 dark:text-white"
											/>
										{:else if key.includes('password') || key.includes('token') || key.includes('secret') || key.includes('api_key') || key.includes('apiKey')}
											<div class="relative">
												{#if secretVisibility[key]}
													<!-- Text input when visible -->
													<input
														type="text"
														id={`config-${key}`}
														bind:value={configData[key]}
														placeholder={prop.default || ''}
														class="w-full px-3 py-2 text-sm border rounded-md dark:bg-gray-700 dark:border-gray-600 dark:text-white pr-10"
													/>
												{:else}
													<!-- Password input when hidden -->
													<input
														type="password"
														id={`config-${key}`}
														bind:value={configData[key]}
														placeholder={prop.default || ''}
														class="w-full px-3 py-2 text-sm border rounded-md dark:bg-gray-700 dark:border-gray-600 dark:text-white pr-10"
													/>
												{/if}
												<button 
													type="button"
													class="absolute inset-y-0 right-0 pr-3 flex items-center text-gray-500 hover:text-gray-700 dark:text-gray-400 dark:hover:text-gray-300"
													on:click={() => secretVisibility[key] = !secretVisibility[key]}
												>
													{#if secretVisibility[key]}
														<!-- Eye open icon -->
														<svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke-width="1.5" stroke="currentColor" class="w-5 h-5">
															<path stroke-linecap="round" stroke-linejoin="round" d="M2.036 12.322a1.012 1.012 0 0 1 0-.639C3.423 7.51 7.36 4.5 12 4.5c4.638 0 8.573 3.007 9.963 7.178.07.207.07.431 0 .639C20.577 16.49 16.64 19.5 12 19.5c-4.638 0-8.573-3.007-9.963-7.178Z" />
															<path stroke-linecap="round" stroke-linejoin="round" d="M15 12a3 3 0 1 1-6 0 3 3 0 0 1 6 0Z" />
														</svg>
													{:else}
														<!-- Eye crossed icon -->
														<svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke-width="1.5" stroke="currentColor" class="w-5 h-5">
															<path stroke-linecap="round" stroke-linejoin="round" d="M3.98 8.223A10.477 10.477 0 0 0 1.934 12C3.226 16.338 7.244 19.5 12 19.5c.993 0 1.953-.138 2.863-.395M6.228 6.228A10.451 10.451 0 0 1 12 4.5c4.756 0 8.773 3.162 10.065 7.498a10.522 10.522 0 0 1-4.293 5.774M6.228 6.228 3 3m3.228 3.228 3.65 3.65m7.894 7.894L21 21m-3.228-3.228-3.65-3.65m0 0a3 3 0 1 0-4.243-4.243m4.242 4.242L9.88 9.88" />
														</svg>
													{/if}
												</button>
											</div>
											{#if prop.description}
												<p class="mt-1 text-xs text-gray-500 dark:text-gray-400">{prop.description}</p>
											{/if}
										{:else}
											<input
												type="text"
												id={`config-${key}`}
												bind:value={configData[key]}
												placeholder={prop.default || ''}
												class="w-full px-3 py-2 text-sm border rounded-md dark:bg-gray-700 dark:border-gray-600 dark:text-white"
											/>
											{#if prop.description}
												<p class="mt-1 text-xs text-gray-500 dark:text-gray-400">{prop.description}</p>
											{/if}
										{/if}
									</div>
								{/each}
							</div>
						</div>
					{:else if server.config && typeof server.config === 'object' && Object.entries(server.config).filter(([key]) => key !== 'command' && key !== 'args').length > 0}
						<!-- Has server.config fields -->
						<div class="mt-3">
							<div class="text-sm font-medium text-gray-800 dark:text-gray-200 mb-2 px-1">
								Configuration:
							</div>
							<div class="space-y-4 mb-4">
								{#each Object.entries(server.config).filter(([key]) => key !== 'command' && key !== 'args') as [key, defaultValue]}
									<div class="bg-white dark:bg-gray-800 p-3 rounded-md border border-gray-200 dark:border-gray-700">
										<label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1" for={`config-${key}`}>
											{key.charAt(0).toUpperCase() + key.slice(1).replace(/_/g, ' ')}
										</label>
										
										{#if typeof defaultValue === 'boolean'}
											<label class="inline-flex items-center">
												<input
													type="checkbox"
													id={`config-${key}`}
													bind:checked={configData[key]}
													class="rounded border-gray-300 text-blue-600 focus:ring-blue-500"
												/>
												<span class="ml-2 text-sm text-gray-700 dark:text-gray-300">Enabled</span>
											</label>
										{:else if typeof defaultValue === 'number'}
											<input
												type="number"
												id={`config-${key}`}
												bind:value={configData[key]}
												class="w-full px-3 py-2 text-sm border rounded-md dark:bg-gray-700 dark:border-gray-600 dark:text-white"
											/>
										{:else if key.includes('password') || key.includes('token') || key.includes('secret') || key.includes('api_key') || key.includes('apiKey')}
											<div class="relative">
												{#if secretVisibility[key]}
													<!-- Text input when visible -->
													<input
														type="text"
														id={`config-${key}`}
														bind:value={configData[key]}
														placeholder={typeof defaultValue === 'string' ? defaultValue : ''}
														class="w-full px-3 py-2 text-sm border rounded-md dark:bg-gray-700 dark:border-gray-600 dark:text-white pr-10"
													/>
												{:else}
													<!-- Password input when hidden -->
													<input
														type="password"
														id={`config-${key}`}
														bind:value={configData[key]}
														placeholder={typeof defaultValue === 'string' ? defaultValue : ''}
														class="w-full px-3 py-2 text-sm border rounded-md dark:bg-gray-700 dark:border-gray-600 dark:text-white pr-10"
													/>
												{/if}
												<button 
													type="button"
													class="absolute inset-y-0 right-0 pr-3 flex items-center text-gray-500 hover:text-gray-700 dark:text-gray-400 dark:hover:text-gray-300"
													on:click={() => secretVisibility[key] = !secretVisibility[key]}
												>
													{#if secretVisibility[key]}
														<!-- Eye open icon -->
														<svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke-width="1.5" stroke="currentColor" class="w-5 h-5">
															<path stroke-linecap="round" stroke-linejoin="round" d="M2.036 12.322a1.012 1.012 0 0 1 0-.639C3.423 7.51 7.36 4.5 12 4.5c4.638 0 8.573 3.007 9.963 7.178.07.207.07.431 0 .639C20.577 16.49 16.64 19.5 12 19.5c-4.638 0-8.573-3.007-9.963-7.178Z" />
															<path stroke-linecap="round" stroke-linejoin="round" d="M15 12a3 3 0 1 1-6 0 3 3 0 0 1 6 0Z" />
														</svg>
													{:else}
														<!-- Eye crossed icon -->
														<svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke-width="1.5" stroke="currentColor" class="w-5 h-5">
															<path stroke-linecap="round" stroke-linejoin="round" d="M3.98 8.223A10.477 10.477 0 0 0 1.934 12C3.226 16.338 7.244 19.5 12 19.5c.993 0 1.953-.138 2.863-.395M6.228 6.228A10.451 10.451 0 0 1 12 4.5c4.756 0 8.773 3.162 10.065 7.498a10.522 10.522 0 0 1-4.293 5.774M6.228 6.228 3 3m3.228 3.228 3.65 3.65m7.894 7.894L21 21m-3.228-3.228-3.65-3.65m0 0a3 3 0 1 0-4.243-4.243m4.242 4.242L9.88 9.88" />
														</svg>
													{/if}
												</button>
											</div>
											<p class="mt-1 text-xs text-gray-500 dark:text-gray-400">
												{typeof defaultValue === 'string' && defaultValue ? `Default format: ${defaultValue.replace(/./g, '*')}` : 'Enter a secure value'}
											</p>
										{:else}
											<input
												type="text"
												id={`config-${key}`}
												bind:value={configData[key]}
												placeholder={typeof defaultValue === 'string' ? defaultValue : ''}
												class="w-full px-3 py-2 text-sm border rounded-md dark:bg-gray-700 dark:border-gray-600 dark:text-white"
											/>
											{#if typeof defaultValue === 'string' && defaultValue}
												<p class="mt-1 text-xs text-gray-500 dark:text-gray-400">
													Default: {defaultValue}
												</p>
											{/if}
										{/if}
									</div>
								{/each}
							</div>
						</div>
					{:else}
						<!-- No configuration required -->
						<div class="mt-3 mb-3">
							<div class="text-sm font-medium text-gray-800 dark:text-gray-200 mb-1 px-1">
								Configuration:
							</div>
							<div class="text-sm text-gray-600 dark:text-gray-400 p-3 bg-gray-50 dark:bg-gray-800 rounded-md border border-gray-200 dark:border-gray-700">
								No configuration keys required for this server.
							</div>
						</div>
					{/if}
				</div>
				
				<!-- Buttons section -->
				<div class="flex justify-end pt-4 text-sm font-medium border-t border-gray-200 dark:border-gray-700 mt-2">
					<button
						type="button"
						class="mr-3 px-4 py-2 text-sm font-medium text-gray-700 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-700 transition rounded-md"
						on:click={() => {
							show = false;
						}}
					>
						{$i18n.t('Cancel')}
					</button>
					
					<button
						class="px-4 py-2 text-sm font-medium bg-blue-600 hover:bg-blue-700 text-white dark:bg-blue-600 dark:hover:bg-blue-700 transition rounded-md {saving ? 'opacity-70 cursor-not-allowed' : ''}"
						on:click={submitHandler}
						disabled={saving}
					>
						<span class="flex items-center">
							{$i18n.t('Add Server')}

							{#if saving}
								<svg
									class="w-4 h-4 ml-2 animate-spin"
									viewBox="0 0 24 24"
									fill="none"
									xmlns="http://www.w3.org/2000/svg"
								>
									<circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
									<path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
								</svg>
							{/if}
						</span>
					</button>
				</div>
			{:else}
				<div class="text-center py-4 text-gray-500 dark:text-gray-400">
					No server information provided.
				</div>
			{/if}
		</div>
	</div>
</Modal>

<style>
	input::-webkit-outer-spin-button,
	input::-webkit-inner-spin-button {
		-webkit-appearance: none;
		margin: 0;
	}

	input[type='number'] {
		-moz-appearance: textfield;
	}
	
	/* Fix for modal appearing behind sidebar */
	:global(.modal-container) {
		z-index: 9999 !important;
	}
	
	:global(.modal-backdrop) {
		z-index: 9998 !important;
	}
	
	/* Styling for configuration display */
	pre {
		font-family: 'Menlo', 'Monaco', 'Courier New', monospace;
	}
</style>