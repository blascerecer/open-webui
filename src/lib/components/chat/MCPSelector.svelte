<script lang="ts">
	import { getContext, onMount } from 'svelte';
	import { DropdownMenu } from 'bits-ui';
	import { flyAndScale } from '$lib/utils/transitions';
	import { createEventDispatcher } from 'svelte';

	import ChevronDown from '$lib/components/icons/ChevronDown.svelte';
	import Search from '$lib/components/icons/Search.svelte';
	import PlusIcon from '$lib/components/icons/Plus.svelte';
	import MinusIcon from '$lib/components/icons/Minus.svelte';
	import EditIcon from '$lib/components/icons/Edit.svelte'; 

	import {
		user,
		mobile,
		settings,
		config
	} from '$lib/stores';
	import { toast } from 'svelte-sonner';
	import Tooltip from '$lib/components/common/Tooltip.svelte';
	import MCPConfigModal from '../MCPConfigModal.svelte';
	
	// Import the JSON file directly
	import serverData from '$lib/utils/smithery-servers.json';
	import { getMCPServers, updateActiveMCPServers, refreshActiveMCPs } from '$lib/apis/mcps';

	const i18n = getContext('i18n');
	const dispatch = createEventDispatcher();

	export let id = 'mcp';
	export let values: string[] = [];
	export let placeholder = 'Select MCPs';
	export let searchEnabled = true;
	export let searchPlaceholder = $i18n.t('Search Server');
	export let showSetDefault = true;

	export let items: {
		label: string;
		value: string;
		description?: string;
		url?: string;
		popularity?: string;
		isActive?: boolean;
		qualifiedName?: string;
		config?: any; // Server configuration object
		// eslint-disable-next-line @typescript-eslint/no-explicit-any
		[key: string]: any;
	}[] = [];

	export let className = 'w-[32rem]';
	export let triggerClassName = 'text-lg';

	let show = false;
	let searchValue = '';
	let selectedItems: { label: string, value: string }[] = [];
	let activeMCPs: string[] = [];
	let loadingActiveMCPs = true;
	let loadingError: any = null;
	
	// Config modal state
	let showConfigModal = false;
	let selectedServer = null;
	
	$: selectedItems = items.filter((item) => values.includes(item.value));
	$: displayText = selectedItems.length > 0 
		? selectedItems.length === 1 
			? selectedItems[0].label 
			: `${selectedItems.length} servers selected`
		: placeholder;

	$: filteredItems = searchValue
		? items.filter(item => 
			item.label.toLowerCase().includes(searchValue.toLowerCase()) ||
			item.value.toLowerCase().includes(searchValue.toLowerCase()) ||
			(item.description && item.description.toLowerCase().includes(searchValue.toLowerCase())))
		: items;

	let selectedItemIdx = 0;
	
	// For displaying raw JSON data
	let isLoading = true;
	
	/**
	 * Add an MCP server with configuration
	 */
	async function addMCP(mcp) {
		try {
			// Always show the config modal for MCPs
			// Close the dropdown before showing the modal
			show = false;
			
			// Wait a small tick for the UI to update
			await new Promise(resolve => setTimeout(resolve, 10));
			
			// Prepare server object for the modal
			selectedServer = {
				id: mcp.qualifiedName,
				name: mcp.displayName,
				description: mcp.description,
				qualifiedName: mcp.qualifiedName, // Pass the qualifiedName to the modal
				url: mcp.url,
				config: mcp.config || {} // Ensure config exists
			};

			console.log("addMCP Selected server:", selectedServer);
			
			// Show config modal after dropdown is closed
			showConfigModal = true;
		} catch (err) {
			console.error(`Failed to add MCP ${mcp.label}:`, err);
			toast.error(`Failed to add ${mcp.label}`);
		}
	}
	
	/**
	 * Edit an existing MCP server configuration
	 */
	async function editMCP(mcpValue) {
		try {
			// Get the MCP item
			const mcpItem = items.find(item => item.value === mcpValue);
			if (!mcpItem) {
				throw new Error(`MCP with value ${mcpValue} not found`);
			}
			
			// Close the dropdown before showing the modal
			show = false;
			
			// Wait a small tick for the UI to update
			await new Promise(resolve => setTimeout(resolve, 10));
			
			// Prepare server object for the modal
			selectedServer = {
				id: mcpItem.qualifiedName,
				name: mcpItem.label,
				description: mcpItem.description,
				qualifiedName: mcpItem.qualifiedName,
				url: mcpItem.url,
				config: mcpItem.config || {} // Ensure config exists
			};
			
			console.log("editMCP Selected server:", selectedServer);
			
			// Show config modal after dropdown is closed
			showConfigModal = true;
		} catch (err) {
			console.error(`Failed to edit MCP ${mcpValue}:`, err);
			toast.error(`Failed to edit server configuration`);
		}
	}

	/**
	 * Remove an MCP server
	 */
	async function removeMCP(mcpValue) {
		try {
			// Get the MCP item
			const mcpItem = items.find(item => item.value === mcpValue);
			if (!mcpItem) {
				throw new Error(`MCP with value ${mcpValue} not found`);
			}
			
			// Update server configuration
			await updateActiveMCPServers({}, [mcpValue]);
			
			// Close the dropdown before showing the toast
			show = false;
			
			// Show success toast
			toast.success(`Removed ${mcpItem.label}`);
			
			// Refresh to update UI
			await handleRefreshMCPs();
			
			// Dispatch event with the updated active items
			dispatch('removeServer', { 
				server: mcpItem,
				activeItems: items.filter(item => item.isActive)
			});
		} catch (err) {
			console.error(`Failed to remove MCP ${mcpValue}:`, err);
			toast.error(`Failed to remove server`);
		}
	}

	/**
	 * Save MCP configuration and add the server
	 */
	async function saveMCP(mcpValue, config = {}) {
		try {
			// Get the MCP item
			const mcpItem = items.find(item => item.value === mcpValue);
			if (!mcpItem) {
				throw new Error(`MCP with value ${mcpValue} not found`);
			}
			
			// Create server configurations object
			const serverConfigs = {
				[mcpValue]: config
			};
			
			// Update active servers
			await updateActiveMCPServers(serverConfigs, []);
			
			// Hide config modal if open
			showConfigModal = false;
			selectedServer = null;
			
			// Show success toast
			toast.success(`Added ${mcpItem.label}`);
			
			// Refresh to update UI
			await handleRefreshMCPs();
			
			// Dispatch event with the updated active items
			dispatch('addServer', { 
				server: mcpItem,
				activeItems: items.filter(item => item.isActive)
			});
		} catch (err) {
			console.error(`Failed to add MCP ${mcpValue}:`, err);
			toast.error(`Failed to add server`);
		}
	}
	
	function getActiveItems() {
		return items.filter(item => item.isActive);
	}
	
	// Handle saving of configuration from modal
	function handleConfigSave(event) {
		const { server, added } = event.detail;
		console.log("Received save event from modal for server:", server.id);
		
		// No need to call saveMCP since MCPConfigModal already made the API call
		// Just refresh the UI to get the updated server list
		handleRefreshMCPs().then(() => {
			// Dispatch event with the updated active items
			dispatch('addServer', { 
				server: items.find(item => item.value === server.id),
				activeItems: items.filter(item => item.isActive)
			});
		});
	}
	
	// Wrapper function to use the imported refreshActiveMCPs
	async function handleRefreshMCPs() {
		try {
			// Set loading state
			loadingActiveMCPs = true;
			loadingError = null;
			
			// Call the imported function with proper callbacks
			const serverNames = await refreshActiveMCPs({
				onError: (err) => {
					loadingError = err;
				}
			});
			
			// Update component state with the server names
			activeMCPs = [...serverNames];
			
			// Update the active status of items - match by value
			items = items.map(item => ({
				...item,
				isActive: serverNames.includes(item.value)
			}));
			
			// Get the values (IDs) of active servers
			values = [...serverNames];
			
			dispatch('activeChange', { activeMCPs });
		} catch (err) {
			// Error already handled by onError callback
			// Any additional error handling can go here
		} finally {
			loadingActiveMCPs = false;
		}
	}
	
	// Initialize items from the imported JSON file and fetch active MCPs
	onMount(async () => {
		try {
			isLoading = true;
			
			// Map the server data to the items format based on new schema
			items = serverData.servers.map(server => ({
				label: server.displayName,
				value: server.qualifiedName,
				qualifiedName: server.qualifiedName, // Store the qualified name for later use
				description: server.description,
				url: server.homepage,
				popularity: server.useCount > 1000 ? "Popular" : (server.useCount > 100 ? "Common" : "New"),
				// Always set config to a default configuration object to trigger the modal
				config: {
					command: "npx",
					args: [
						"-y",
						"@smithery/cli@latest",
						"run",
						server.qualifiedName,
						"--config",
						"\"{}\""
					]
				},
				isActive: false // Initialize as inactive, will update when we fetch active MCPs
			}));
			
			// Wait for active MCP servers
			await handleRefreshMCPs();
			
		} catch (error) {
			console.error('Failed to load server data:', error);
		} finally {
			isLoading = false;
		}
	});
</script>

<DropdownMenu.Root
	bind:open={show}
	onOpenChange={async () => {
		searchValue = '';
		selectedItemIdx = 0;
		window.setTimeout(() => document.getElementById('mcp-search-input')?.focus(), 0);
	}}
	closeFocus={false}
>
	<DropdownMenu.Trigger
		class="relative w-full font-primary"
		aria-label={placeholder}
		id="mcp-selector-{id}-button"
	>
		<div
			class="flex w-full text-left px-0.5 outline-hidden bg-transparent truncate {triggerClassName} justify-between font-medium placeholder-gray-400 focus:outline-hidden"
		>
			{displayText}
			<ChevronDown className="self-center ml-2 size-3" strokeWidth="2.5" />
		</div>
	</DropdownMenu.Trigger>

	<DropdownMenu.Content
		class="z-40 {$mobile ? `w-full` : `${className}`} max-w-[calc(100vw-1rem)] justify-start rounded-xl bg-white dark:bg-gray-850 dark:text-white shadow-lg outline-hidden"
		transition={flyAndScale}
		side={$mobile ? 'bottom' : 'bottom-start'}
		sideOffset={3}
	>
		<slot>
			{#if searchEnabled}
				<div class="flex items-center gap-2.5 px-5 mt-3.5 mb-1.5">
					<Search className="size-4" strokeWidth="2.5" />

					<input
						id="mcp-search-input"
						bind:value={searchValue}
						class="w-full text-sm bg-transparent outline-hidden"
						placeholder={searchPlaceholder}
						autocomplete="off"
						on:keydown={(e) => {
							if (e.code === 'Enter' && filteredItems.length > 0) {
								const item = filteredItems[selectedItemIdx];
								if (item.isActive) {
									removeMCP(item.value);
								} else {
									addMCP(item);
								}
								return;
							} else if (e.code === 'ArrowDown') {
								selectedItemIdx = Math.min(selectedItemIdx + 1, filteredItems.length - 1);
							} else if (e.code === 'ArrowUp') {
								selectedItemIdx = Math.max(selectedItemIdx - 1, 0);
							} else {
								selectedItemIdx = 0;
							}

							const item = document.querySelector(`[data-mcp-selected="true"]`);
							item?.scrollIntoView({ block: 'center', inline: 'nearest', behavior: 'instant' });
						}}
					/>
				</div>
			{/if}

			<!-- Active MCPs section - only shown if there are active servers -->
			{#if !isLoading && !loadingActiveMCPs && !loadingError && activeMCPs.length > 0}
				<div class="pt-3 mb-1">
					<div class="px-5 py-1 text-sm font-medium text-gray-700 dark:text-gray-200">
						Active MCPs:
					</div>
					
					<div class="px-5 py-2 space-y-2">
						{#each activeMCPs as mcpName}
							<!-- Find the corresponding item to get its label -->
							{@const mcpItem = items.find(item => item.value === mcpName)}
							{#if mcpItem}
								<div class="flex items-center justify-between p-2 rounded-lg bg-blue-50 dark:bg-blue-950 border border-blue-200 dark:border-blue-800">
									<div class="flex items-center space-x-2">
										<!-- Server icon -->
										<div class="rounded-full flex items-center">
											{#if mcpItem.icon}
												<mcpItem.icon class="size-5" />
											{:else}
												<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="size-5">
													<rect width="18" height="18" x="3" y="3" rx="2" />
													<path d="M7 10h10" />
													<path d="M7 14h10" />
												</svg>
											{/if}
										</div>
										
										<!-- Server name and optional popularity badge -->
										<div class="flex items-center">
											<span class="text-sm font-medium text-blue-700 dark:text-blue-300">{mcpItem.label}</span>
											
											{#if mcpItem.popularity}
												<div class="ml-2 text-xs px-1.5 py-0.5 bg-blue-100 dark:bg-blue-900 rounded text-blue-600 dark:text-blue-300">
													{mcpItem.popularity}
												</div>
											{/if}
											
											{#if mcpItem.description}
												<Tooltip content={mcpItem.description}>
													<div class="ml-2 translate-y-[1px]">
														<svg
															xmlns="http://www.w3.org/2000/svg"
															fill="none"
															viewBox="0 0 24 24"
															stroke-width="1.5"
															stroke="currentColor"
															class="w-4 h-4"
														>
															<path
																stroke-linecap="round"
																stroke-linejoin="round"
																d="m11.25 11.25.041-.02a.75.75 0 0 1 1.063.852l-.708 2.836a.75.75 0 0 0 1.063.853l.041-.021M21 12a9 9 0 1 1-18 0 9 9 0 0 1 18 0Zm-9-3.75h.008v.008H12V8.25Z"
															/>
														</svg>
													</div>
												</Tooltip>
											{/if}
										</div>
									</div>
									
									<!-- Action buttons -->
									<div class="flex items-center space-x-1">
										<!-- Edit button -->
										<Tooltip content="Edit">
											<button
												class="text-blue-500 hover:text-blue-700 dark:text-blue-400 dark:hover:text-blue-300 p-1 rounded-full hover:bg-blue-100 dark:hover:bg-blue-900/20"
												on:click={() => editMCP(mcpItem.value)}
											>
												<EditIcon class="size-4" />
											</button>
										</Tooltip>
										
										<!-- Remove button -->
										<Tooltip content="Remove">
											<button
												class="text-red-500 hover:text-red-700 dark:text-red-400 dark:hover:text-red-300 p-1 rounded-full hover:bg-red-100 dark:hover:bg-red-900/20"
												on:click={() => removeMCP(mcpItem.value)}
											>
												<MinusIcon class="size-4" />
											</button>
										</Tooltip>
									</div>
								</div>
							{/if}
						{/each}
					</div>
					<hr class="my-2 border-gray-100 dark:border-gray-800" />
				</div>
			{:else if !isLoading && loadingActiveMCPs}
				<div class="pt-3 mb-1">
					<div class="px-5 py-1 text-sm font-medium text-gray-700 dark:text-gray-200">
						Loading...
					</div>
					<div class="px-5 py-2 text-sm text-gray-500 dark:text-gray-400">
						Loading servers...
					</div>
					<hr class="my-2 border-gray-100 dark:border-gray-800" />
				</div>
			{:else if !isLoading && loadingError}
				<div class="pt-3 mb-1">
					<div class="px-5 py-1 text-sm font-medium text-gray-700 dark:text-gray-200">
						Error
					</div>
					<div class="px-5 py-2 text-sm text-red-500 dark:text-red-400">
						{#if loadingError.detail}
							{loadingError.detail}
						{:else if typeof loadingError === 'string'}
							{loadingError}
						{:else if loadingError.message}
							{loadingError.message}
						{:else}
							Error loading servers.
						{/if}
						<button 
							class="ml-2 text-blue-500 hover:text-blue-400 hover:underline" 
							on:click={handleRefreshMCPs}
						>
							Try again
						</button>
					</div>
					<hr class="my-2 border-gray-100 dark:border-gray-800" />
				</div>
			{/if}
			
			<!-- Available servers section (excluding those already shown in Active MCPs) -->
			<div class="px-5 py-1 text-sm font-medium text-gray-700 dark:text-gray-200">
				Available MCPs:
			</div>
			
			<div class="px-3 mb-4 max-h-64 overflow-y-auto scrollbar-hidden group relative">
				{#each filteredItems.filter(item => !activeMCPs.includes(item.value)) as item, index}
					<div
						class="flex w-full text-left font-medium select-none items-center justify-between rounded-button py-2 pl-3 pr-1.5 text-sm text-gray-700 dark:text-gray-100 outline-hidden transition-all duration-75 hover:bg-gray-100 dark:hover:bg-gray-800 rounded-lg cursor-pointer data-highlighted:bg-muted {index === selectedItemIdx ? 'bg-gray-100 dark:bg-gray-800 group-hover:bg-transparent' : ''}"
						data-mcp-selected={index === selectedItemIdx}
					>
						<div class="flex items-center">
							<div class="flex items-center min-w-fit">
								<div class="rounded-full flex items-center mr-2">
									{#if item.icon}
										<item.icon class="size-5" />
									{:else}
										<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="size-5">
											<rect width="18" height="18" x="3" y="3" rx="2" />
											<path d="M7 10h10" />
											<path d="M7 14h10" />
										</svg>
									{/if}
								</div>
							</div>
							
							<div class="flex flex-col">
								<div class="flex items-center gap-2">
									<Tooltip
										content={$user?.role === 'admin' ? (item?.value ?? '') : ''}
										placement="top-start"
									>
										<span>{item.qualifiedName}</span>
									</Tooltip>
									
									{#if item.popularity}
										<div class="text-xs px-1.5 py-0.5 bg-gray-100 dark:bg-gray-700 rounded text-gray-600 dark:text-gray-300">
											{item.popularity}
										</div>
									{/if}
									
									{#if item.description}
										<Tooltip content={item.description}>
											<div class="translate-y-[1px]">
												<svg
													xmlns="http://www.w3.org/2000/svg"
													fill="none"
													viewBox="0 0 24 24"
													stroke-width="1.5"
													stroke="currentColor"
													class="w-4 h-4"
												>
													<path
														stroke-linecap="round"
														stroke-linejoin="round"
														d="m11.25 11.25.041-.02a.75.75 0 0 1 1.063.852l-.708 2.836a.75.75 0 0 0 1.063.853l.041-.021M21 12a9 9 0 1 1-18 0 9 9 0 0 1 18 0Zm-9-3.75h.008v.008H12V8.25Z"
													/>
												</svg>
											</div>
										</Tooltip>
									{/if}
								</div>
							</div>
						</div>
						
						<!-- Add button -->
						<Tooltip content="Add">
							<button
								class="text-green-500 hover:text-green-700 dark:text-green-400 dark:hover:text-green-300 p-1 rounded-full hover:bg-green-100 dark:hover:bg-green-900/20"
								on:click={() => addMCP(item)}
							>
								<PlusIcon class="size-4" />
							</button>
						</Tooltip>
					</div>
				{:else}
					<div>
						<div class="block px-3 py-2 text-sm text-gray-700 dark:text-gray-100">
							{$i18n.t('No results found')}
						</div>
					</div>
				{/each}
			</div>

			<div class="hidden w-[42rem]" />
			<div class="hidden w-[32rem]" />
		</slot>
	</DropdownMenu.Content>
</DropdownMenu.Root>

<!-- Use the MCPConfigModal component with qualifiedName passed -->
<MCPConfigModal
	bind:show={showConfigModal}
	bind:server={selectedServer}
	on:save={handleConfigSave}
/>