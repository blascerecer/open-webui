from fastapi import HTTPException
from datetime import datetime
import base64
import json
import os

from kubernetes import client, config
from kubernetes.client.rest import ApiException

from mcp_bridge_manager.models import InferenceServer, McpServer, KeyRequest
from mcp_bridge_manager.config import settings

# Initialize Kubernetes client
try:
    # Inside cluster config
    config.load_incluster_config()
except:
    # Local development fallback
    config.load_kube_config()

# Create API clients
apps_v1 = client.AppsV1Api()
core_v1 = client.CoreV1Api()

# Get current namespace
namespace = settings.kubernetes_namespace

def generate_bridge_name(user_id: str) -> str:
    """Generate a Kubernetes-safe name for the bridge."""
    # Ensure the name is DNS-1123 compliant
    safe_id = user_id.lower().replace('_', '-').replace('@', '-').replace('.', '-')
    return f"mcp-bridge-{safe_id}"

def create_config_map(user_id: str, inference_server: InferenceServer, mcp_servers: dict):
    """Create ConfigMap for the user's MCP Bridge."""
    bridge_name = generate_bridge_name(user_id)
    
    # Generate config.json
    config_json = {
        "inferenceServer": {
            "baseUrl": inference_server.baseUrl
        },
        "network": {
            "host": "0.0.0.0",
            "port": 9090
        },
        "logging": {
            "logLevel": "INFO"
        }
    }
    
    # Generate mcp_config.json
    mcp_config_json = {
        "mcpServers": {}
    }
    
    for server_name, server in mcp_servers.items():
        mcp_config_json["mcpServers"][server_name] = {
            "command": server.command,
            "args": server.args
        }
        # API key will come from the secret, not included here
    
    # Create ConfigMap
    config_map = client.V1ConfigMap(
        metadata=client.V1ObjectMeta(
            name=f"{bridge_name}-config",
            labels={"app": "mcp-bridge", "user": user_id}
        ),
        data={
            "config.json": json.dumps(config_json),
            "mcp_config.json": json.dumps(mcp_config_json)
        }
    )
    
    try:
        try:
            core_v1.read_namespaced_config_map(f"{bridge_name}-config", namespace)
            core_v1.replace_namespaced_config_map(f"{bridge_name}-config", namespace, config_map)
        except ApiException as e:
            if e.status == 404:
                core_v1.create_namespaced_config_map(namespace, config_map)
            else:
                raise
    except ApiException as e:
        raise HTTPException(status_code=500, detail=f"Failed to create ConfigMap: {str(e)}")

def create_secrets(user_id: str, inference_server: InferenceServer, mcp_servers: dict):
    """Create Secrets for the user's API keys."""
    bridge_name = generate_bridge_name(user_id)
    
    # Create inference server secret
    inference_secret = client.V1Secret(
        metadata=client.V1ObjectMeta(
            name=f"{bridge_name}-inference",
            labels={"app": "mcp-bridge", "user": user_id}
        ),
        type="Opaque",
        data={
            "api-key": base64.b64encode(inference_server.apiKey.encode()).decode()
        }
    )
    
    try:
        try:
            core_v1.read_namespaced_secret(f"{bridge_name}-inference", namespace)
            core_v1.replace_namespaced_secret(f"{bridge_name}-inference", namespace, inference_secret)
        except ApiException as e:
            if e.status == 404:
                core_v1.create_namespaced_secret(namespace, inference_secret)
            else:
                raise
    except ApiException as e:
        raise HTTPException(status_code=500, detail=f"Failed to create inference secret: {str(e)}")
    
    # Create MCP server secrets
    for server_name, server in mcp_servers.items():
        if server.apiKey or server.credentials:
            data = {}
            if server.apiKey:
                data["api-key"] = base64.b64encode(server.apiKey.encode()).decode()
            if server.credentials:
                data["credentials"] = base64.b64encode(json.dumps(server.credentials).encode()).decode()
                
            server_secret = client.V1Secret(
                metadata=client.V1ObjectMeta(
                    name=f"{bridge_name}-{server_name}",
                    labels={"app": "mcp-bridge", "user": user_id, "server": server_name}
                ),
                type="Opaque",
                data=data
            )
            
            try:
                try:
                    core_v1.read_namespaced_secret(f"{bridge_name}-{server_name}", namespace)
                    core_v1.replace_namespaced_secret(f"{bridge_name}-{server_name}", namespace, server_secret)
                except ApiException as e:
                    if e.status == 404:
                        core_v1.create_namespaced_secret(namespace, server_secret)
                    else:
                        raise
            except ApiException as e:
                raise HTTPException(status_code=500, detail=f"Failed to create server secret: {str(e)}")

def create_deployment(user_id: str):
    """Create a Deployment for the user's MCP Bridge."""
    bridge_name = generate_bridge_name(user_id)
    
    # Define container
    container = client.V1Container(
        name="mcp-bridge",
        image=settings.mcp_bridge_image,
        image_pull_policy="Always",
        ports=[client.V1ContainerPort(container_port=9090)],
        env=[
            client.V1EnvVar(
                name="INFERENCE_SERVER_API_KEY",
                value_from=client.V1EnvVarSource(
                    secret_key_ref=client.V1SecretKeySelector(
                        name=f"{bridge_name}-inference",
                        key="api-key"
                    )
                )
            )
        ],
        volume_mounts=[
            client.V1VolumeMount(
                name="config-volume",
                mount_path="/mcp_bridge/config.json",
                sub_path="config.json"
            ),
            client.V1VolumeMount(
                name="config-volume",
                mount_path="/mcp_bridge/mcp_config.json",
                sub_path="mcp_config.json"
            )
        ],
        resources=client.V1ResourceRequirements(
            requests={"cpu": "200m", "memory": "256Mi"},
            limits={"cpu": "500m", "memory": "512Mi"}
        )
    )
    
    # Define volumes
    volumes = [
        client.V1Volume(
            name="config-volume",
            config_map=client.V1ConfigMapVolumeSource(
                name=f"{bridge_name}-config"
            )
        )
    ]
    
    # Define template
    template = client.V1PodTemplateSpec(
        metadata=client.V1ObjectMeta(
            labels={"app": "mcp-bridge", "user": user_id}
        ),
        spec=client.V1PodSpec(
            containers=[container],
            volumes=volumes
        )
    )
    
    # Define deployment
    deployment = client.V1Deployment(
        metadata=client.V1ObjectMeta(
            name=bridge_name,
            labels={"app": "mcp-bridge", "user": user_id}
        ),
        spec=client.V1DeploymentSpec(
            replicas=1,
            selector=client.V1LabelSelector(
                match_labels={"app": "mcp-bridge", "user": user_id}
            ),
            template=template
        )
    )
    
    try:
        # Check if deployment already exists
        try:
            apps_v1.read_namespaced_deployment(bridge_name, namespace)
            # If it exists, update it
            apps_v1.replace_namespaced_deployment(bridge_name, namespace, deployment)
        except ApiException as e:
            if e.status == 404:
                # If it doesn't exist, create it
                apps_v1.create_namespaced_deployment(namespace, deployment)
            else:
                raise
    except ApiException as e:
        raise HTTPException(status_code=500, detail=f"Failed to create deployment: {str(e)}")

def create_service(user_id: str):
    """Create a Service for the user's MCP Bridge."""
    bridge_name = generate_bridge_name(user_id)
    
    service = client.V1Service(
        metadata=client.V1ObjectMeta(
            name=f"{bridge_name}-service",
            labels={"app": "mcp-bridge", "user": user_id}
        ),
        spec=client.V1ServiceSpec(
            selector={"app": "mcp-bridge", "user": user_id},
            ports=[client.V1ServicePort(port=9090, target_port=9090)],
            type="ClusterIP"
        )
    )
    
    try:
        # Check if service already exists
        try:
            core_v1.read_namespaced_service(f"{bridge_name}-service", namespace)
            # If it exists, update it
            core_v1.replace_namespaced_service(f"{bridge_name}-service", namespace, service)
        except ApiException as e:
            if e.status == 404:
                # If it doesn't exist, create it
                core_v1.create_namespaced_service(namespace, service)
            else:
                raise
    except ApiException as e:
        raise HTTPException(status_code=500, detail=f"Failed to create service: {str(e)}")

def delete_bridge(user_id: str):
    """Delete the user's MCP Bridge and related resources."""
    bridge_name = generate_bridge_name(user_id)
    
    # Delete deployment
    try:
        apps_v1.delete_namespaced_deployment(
            bridge_name,
            namespace,
            body=client.V1DeleteOptions(
                propagation_policy="Foreground"
            )
        )
    except ApiException as e:
        if e.status != 404:  # Ignore if already deleted
            raise HTTPException(status_code=500, detail=f"Failed to delete deployment: {str(e)}")
    
    # Delete service
    try:
        core_v1.delete_namespaced_service(
            f"{bridge_name}-service",
            namespace
        )
    except ApiException as e:
        if e.status != 404:  # Ignore if already deleted
            raise HTTPException(status_code=500, detail=f"Failed to delete service: {str(e)}")
    
    # Delete ConfigMap
    try:
        core_v1.delete_namespaced_config_map(
            f"{bridge_name}-config",
            namespace
        )
    except ApiException as e:
        if e.status != 404:  # Ignore if already deleted
            raise HTTPException(status_code=500, detail=f"Failed to delete ConfigMap: {str(e)}")
    
    # We don't delete secrets here to preserve user API keys for next login

def get_bridge_status(user_id: str):
    """Get status of the user's MCP Bridge."""
    from mcp_bridge_manager.models import BridgeInfo
    bridge_name = generate_bridge_name(user_id)
    
    try:
        # Check deployment status
        deployment = apps_v1.read_namespaced_deployment_status(bridge_name, namespace)
        
        if deployment.status.available_replicas and deployment.status.available_replicas > 0:
            status = "running"
        else:
            status = "starting"
            
        # Get available servers
        label_selector = f"app=mcp-bridge,user={user_id},server"
        secrets = core_v1.list_namespaced_secret(namespace, label_selector=label_selector)
        available_servers = [s.metadata.labels.get("server") for s in secrets.items if "server" in s.metadata.labels]
        
        return BridgeInfo(
            status=status,
            endpoint=f"{bridge_name}-service:9090",
            availableServers=available_servers
        )
        
    except ApiException as e:
        if e.status == 404:
            return BridgeInfo(
                status="not_found",
                endpoint="",
                availableServers=[]
            )
        else:
            raise HTTPException(status_code=500, detail=f"Failed to get bridge status: {str(e)}")

def store_api_key(user_id: str, request: KeyRequest):
    """Store a new API key for a user."""
    bridge_name = generate_bridge_name(user_id)
    server_name = request.server
    
    # Update the secret
    secret_name = f"{bridge_name}-{server_name}"
    
    secret_data = {
        "api-key": base64.b64encode(request.apiKey.encode()).decode()
    }
    
    secret = client.V1Secret(
        metadata=client.V1ObjectMeta(
            name=secret_name,
            labels={"app": "mcp-bridge", "user": user_id, "server": server_name}
        ),
        type="Opaque",
        data=secret_data
    )
    
    try:
        try:
            core_v1.read_namespaced_secret(secret_name, namespace)
            core_v1.replace_namespaced_secret(secret_name, namespace, secret)
        except ApiException as e:
            if e.status == 404:
                core_v1.create_namespaced_secret(namespace, secret)
            else:
                raise
    except ApiException as e:
        raise HTTPException(status_code=500, detail=f"Failed to store API key: {str(e)}")
    
    # Update ConfigMap to include the new server
    try:
        config_map_name = f"{bridge_name}-config"
        config_map = core_v1.read_namespaced_config_map(config_map_name, namespace)
        
        # Get existing MCP config
        mcp_config = json.loads(config_map.data["mcp_config.json"])
        
        # Add or update server
        mcp_config["mcpServers"][server_name] = {
            "command": request.command,
            "args": request.args
        }
        
        # Update ConfigMap
        config_map.data["mcp_config.json"] = json.dumps(mcp_config)
        core_v1.replace_namespaced_config_map(config_map_name, namespace, config_map)
        
    except ApiException as e:
        raise HTTPException(status_code=500, detail=f"Failed to update ConfigMap: {str(e)}")
    
    # Restart the deployment if it exists
    try:
        # Patch deployment with a slight change to force restart
        patch = {"spec": {"template": {"metadata": {"annotations": {"restartedAt": str(datetime.now())}}}}}
        apps_v1.patch_namespaced_deployment(bridge_name, namespace, patch)
    except ApiException as e:
        if e.status != 404:  # Ignore if deployment doesn't exist
            raise HTTPException(status_code=500, detail=f"Failed to restart deployment: {str(e)}")
    
    return {"message": f"API key for {server_name} stored successfully"}

def list_api_keys(user_id: str):
    """List available MCP Servers for a user."""
    bridge_name = generate_bridge_name(user_id)
    
    try:
        # Find all secrets for this user with server label
        label_selector = f"app=mcp-bridge,user={user_id},server"
        secrets = core_v1.list_namespaced_secret(namespace, label_selector=label_selector)
        
        servers = [s.metadata.labels.get("server") for s in secrets.items if "server" in s.metadata.labels]
        return {"servers": servers}
        
    except ApiException as e:
        raise HTTPException(status_code=500, detail=f"Failed to list API keys: {str(e)}")