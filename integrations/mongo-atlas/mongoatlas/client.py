from enum import StrEnum
from typing import Any, Optional, AsyncGenerator, Union

import httpx
from httpx import DigestAuth
from loguru import logger

from port_ocean.context.event import event
from port_ocean.utils import http_async_client

ATLAS_BASE_URL = "https://cloud.mongodb.com/api/atlas"


class MongoAtlasClient:
    def __init__(self, public_key: str, private_key: str):
        self.public_key = public_key
        self.private_key = private_key
        self.http_client = http_async_client
        self.http_client.headers.update(self.api_auth_header)

    @property
    def api_auth_header(self) -> dict[str, Any]:
        return {
            "Content-Type": "application/json",
        }

    async def send_api_request(
        self,
        endpoint: str,
        method: str = "GET",
        query_params: Optional[dict[str, Any]] = None,
        json_data: Optional[dict[str, Any]] = None,
    ) -> dict[str, Any]:
        try:
            response = await self.http_client.request(
                auth=DigestAuth(self.public_key, self.private_key),
                method=method,
                url=f"{ATLAS_BASE_URL}/{endpoint}",
                params=query_params,
                json=json_data,
                headers=self.api_auth_header,
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

        flattened_clusters = []

        for project_entry in raw_data.get("results", []):
            project_id = project_entry.get("groupId")
            project_name = project_entry.get("groupName")
            org_id = project_entry.get("orgId")
            org_name = project_entry.get("orgName")

            for cluster in project_entry.get("clusters", []):
                flattened_clusters.append({
                    "organization_id": org_id,
                    "organization_name": org_name,
                    "project_id": project_id,
                    "project_name": project_name,
                    "cluster_id": cluster.get("clusterId"),
                    "cluster_name": cluster.get("name"),
                    "cluster_type": cluster.get("type"),
                    "cluster_alerts": cluster.get("alertCount"),
                    "cluster_availability": cluster.get("availability"),
                    "cluster_auth_enabled": cluster.get("authEnabled"),
                    "cluster_backup_enabled": cluster.get("backupEnabled"),
                    "cluster_ssl_enabled": cluster.get("sslEnabled"),
                    "cluster_versions": cluster.get("versions"),
                })

        return flattened_clusters

# Reference taken from the FirehydrantClient class
