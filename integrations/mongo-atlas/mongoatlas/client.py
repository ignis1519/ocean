import base64
from typing import Any, Optional

import httpx
from loguru import logger

from port_ocean.utils import http_async_client

ATLAS_OAUTH_URL = "https://cloud.mongodb.com/api/oauth/token"
ATLAS_BASE_URL = "https://cloud.mongodb.com/api/atlas"


class MongoAtlasClient:
    def __init__(self, client_id: str, client_secret: str):
        self.client_id = client_id
        self.client_secret = client_secret
        self.access_token: str | None = None

    async def get_access_token(self) -> str:
        auth_string = f"{self.client_id}:{self.client_secret}"
        auth_header = base64.b64encode(auth_string.encode()).decode()

        headers = {
            "Accept": "application/json",
            "Authorization": f"Basic {auth_header}",
            "Content-Type": "application/x-www-form-urlencoded",
            "Cache-Control": "no-cache",
        }

        data = {"grant_type": "client_credentials"}

        response = await http_async_client.post(
            ATLAS_OAUTH_URL, data=data, headers=headers
        )
        response.raise_for_status()
        token_data = response.json()
        self.access_token = token_data["access_token"]
        return self.access_token

    @property
    def api_headers(self) -> dict[str, Any]:
        return {
            "Content-Type": "application/json",
        }

    async def send_api_request(
        self,
        endpoint: str,
        method: str = "GET",
        params: dict[str, Any] = None,
        json_data: dict[str, Any] = None,
    ) -> dict[str, Any]:
        if not self.access_token:
            await self.get_access_token()

        headers = {
            "Authorization": f"Bearer {self.access_token}",
            "Accept": "application/vnd.atlas.2023-02-01+json",
            "Content-Type": "application/json",
        }

        try:
            response = await http_async_client.request(
                method=method,
                url=f"{ATLAS_BASE_URL}/{endpoint}",
                headers=headers,
                params=params,
                json=json_data,
            )
            response.raise_for_status()
            return response.json()
        except httpx.HTTPStatusError as e:
            logger.error(
                f"HTTP error with status code: {e.response.status_code} and response text: {e.response.text}"
            )
            raise


    async def get_clusters(self) -> list[dict[str, Any]]:
        """Fetch and flatten clusters from /v2/clusters endpoint"""
        raw_data = await self.send_api_request("v2/clusters")

        logger.debug("Raw response from /v2/clusters:\n{}", raw_data)

        flattened_clusters = []

        results = raw_data.get("results", [])
        if not isinstance(results, list):
            logger.error("Expected 'results' to be a list, got: {}", type(results))
            raise ValueError("Malformed response: 'results' is not a list")

        for project_entry in results:
            project_id = project_entry.get("groupId")
            project_name = project_entry.get("groupName")
            org_id = project_entry.get("orgId")
            org_name = project_entry.get("orgName")

            clusters = project_entry.get("clusters", [])
            if not isinstance(clusters, list):
                logger.warning("Expected 'clusters' to be a list, got: {}", type(clusters))
                continue

            for cluster in clusters:
                flattened = {
                    "organization_id": org_id,
                    "organization_name": org_name,
                    "project_id": project_id,
                    "project_name": project_name,
                    "cluster_id": cluster.get("clusterId"),
                    "cluster_name": cluster.get("name"),
                    "cluster_type": cluster.get("type"),
                    "cluster_alerts": cluster.get("alertCount"),
                    "cluster_availability": str(cluster.get("availability")).capitalize(),
                    "cluster_auth_enabled": cluster.get("authEnabled"),
                    "cluster_backup_enabled": cluster.get("backupEnabled"),
                    "cluster_ssl_enabled": cluster.get("sslEnabled"),
                    "cluster_versions": cluster.get("versions"),
                }
                logger.debug("Flattened cluster: {}", flattened)
                flattened_clusters.append(flattened)

        logger.debug("Total clusters flattened: {}", len(flattened_clusters))
        logger.debug("Returning: {}", flattened_clusters)
        return flattened_clusters
