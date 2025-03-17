<script>
	import { goto } from '$app/navigation';
	import { WEBUI_NAME, config } from '$lib/stores';
	import { onMount, getContext } from 'svelte';

	const i18n = getContext('i18n');

	let loaded = false;
	let backendStatus = "Checking backend connection...";
	let configData = null;

	onMount(async () => {
		console.log("Component mounted, checking backend connection...");
		
		// Debug: Check if config is already loaded
		console.log("Initial config state:", $config);
		
		// Test backend connectivity using the proxy
		try {
			console.log("try getting backend config");
			
			// Use the proxied path rather than the direct URL
			const response = await fetch('/api/config', {
				method: 'GET',
				// Important: include credentials for cookies
				credentials: 'include',
				headers: {
					'Accept': 'application/json',
					'Cache-Control': 'no-cache'
				}
			});
			
			if (response.ok) {
				const data = await response.json();
				console.log("Backend responded successfully:", data);
				backendStatus = "Backend connected successfully";
				configData = data;
				
				// Update the config store
				config.set(data);
			} else {
				console.error("Backend returned error status:", response.status);
				backendStatus = `Backend error: ${response.status} ${response.statusText}`;
			}
		} catch (error) {
			console.error("Failed to connect to backend:", error);
			backendStatus = `Connection error: ${error.message}`;
		}
		
		// Check if config store was populated
		if ($config) {
			console.log("Config store is populated:", $config);
			await goto('/');
		} else {
			console.warn("Config store is still undefined after backend check");
		}

		loaded = true;
	});
</script>

{#if loaded}
	<div class="absolute w-full h-full flex z-50">
		<div class="absolute rounded-xl w-full h-full backdrop-blur-sm flex justify-center">
			<div class="m-auto pb-44 flex flex-col justify-center">
				<div class="max-w-md">
					<div class="text-center text-2xl font-medium z-50">
						{$i18n.t('{{webUIName}} Backend Required', { webUIName: $WEBUI_NAME })}
					</div>

					<div class="mt-4 text-center text-sm w-full">
						{$i18n.t(
							"Oops! You're using an unsupported method (frontend only). Please serve the WebUI from the backend."
						)}

						<br class=" " />
						<div class="mt-2 p-2 bg-gray-100 rounded text-xs text-left">
							<strong>Debug Info:</strong><br />
							Status: {backendStatus}<br />
							Config: {configData ? 'Received' : 'Not received'}<br />
							Store: {$config ? 'Loaded' : 'Not loaded'}
						</div>

						<br class=" " />
						<a class="font-semibold underline" href="https://github.com/open-webui/open-webui#how-to-install-" target="_blank">
							{$i18n.t('See readme.md for instructions')}
						</a>
						{$i18n.t('or')}
						<a class="font-semibold underline" href="https://discord.gg/5rJgQTnV4s" target="_blank">
							{$i18n.t('join our Discord for help.')}
						</a>
					</div>

					<div class="mt-6 mx-auto relative group w-fit">
						<button
							class="relative z-20 flex px-5 py-2 rounded-full bg-gray-100 hover:bg-gray-200 transition font-medium text-sm"
							on:click={() => {
								console.log("Check Again clicked, reloading page");
								location.href = '/';
							}}
						>
							{$i18n.t('Check Again')}
						</button>
					</div>
				</div>
			</div>
		</div>
	</div>
{/if}