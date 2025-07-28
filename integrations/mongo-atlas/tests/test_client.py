from typing import Any
from unittest.mock import AsyncMock, MagicMock, Mock, patch

import pytest
from httpx import Request, Response
from port_ocean.context.ocean import initialize_port_ocean_context
from port_ocean.exceptions.context import PortOceanContextAlreadyInitializedError

from mongoatlas.client import MongoAtlasClient

@pytest.fixture(autouse=True)
def mock_ocean_context() -> None:
    """Fixture to mock the Ocean context initialization."""
    try:
        mock_ocean_app = MagicMock()
        mock_ocean_app.config = MagicMock()
        mock_ocean_app.config.oauth_access_token_file_path = None
        mock_ocean_app.config.integration.config = {
            "mongoatlas_public_key": "asdf",
            "mongoatlas_private_key": "asdf",
        }
        mock_ocean_app.integration_router = MagicMock()
        mock_ocean_app.port_client = MagicMock()
        mock_ocean_app.cache_provider = AsyncMock()
        mock_ocean_app.load_external_oauth_access_token = MagicMock(return_value=None)
        mock_ocean_app.cache_provider.get.return_value = None
        initialize_port_ocean_context(mock_ocean_app)
    except PortOceanContextAlreadyInitializedError:
        pass

@pytest.fixture
def client():
    return MongoAtlasClient("test_id", "test_secret")

@pytest.mark.asyncio
@patch("mongoatlas.client.http_async_client")
async def test_get_access_token(mock_http_async_client, client):
    mock_response = AsyncMock()
    mock_response.raise_for_status = Mock(return_value=None)  # <-- Fix here
    mock_response.json = Mock(return_value={"access_token": "abc123"})
    mock_http_async_client.post.return_value = mock_response

    token = await client.get_access_token()
    assert token == "abc123"
    assert client.access_token == "abc123"

@pytest.mark.asyncio
@patch("mongoatlas.client.http_async_client")
async def test_send_api_request(mock_http_async_client, client):
    client.access_token = "abc123"
    mock_response = AsyncMock()
    mock_response.raise_for_status = Mock(return_value=None)  # <-- Fix here
    mock_response.json = lambda: {"foo": "bar"}
    mock_http_async_client.request.return_value = mock_response

    result = await client.send_api_request("v2/test")
    assert result == {"foo": "bar"}

@pytest.mark.asyncio
@patch.object(MongoAtlasClient, "send_api_request", new_callable=AsyncMock)
async def test_get_clusters_flattening(mock_send_api_request, client):
    mock_send_api_request.return_value = {
        "results": [
            {
                "groupId": "g1",
                "groupName": "Project1",
                "orgId": "o1",
                "orgName": "Org1",
                "clusters": [
                    {
                        "clusterId": "c1",
                        "name": "Cluster1",
                        "type": "REPLICASET",
                        "alertCount": 2,
                        "availability": "available",
                        "authEnabled": True,
                        "backupEnabled": False,
                        "sslEnabled": True,
                        "versions": ["6.0"],
                    }
                ],
            }
        ]
    }
    clusters = await client.get_clusters()
    assert len(clusters) == 1
    cluster = clusters[0]
    assert cluster["organization_id"] == "o1"
    assert cluster["organization_name"] == "Org1"
    assert cluster["project_id"] == "g1"
    assert cluster["project_name"] == "Project1"
    assert cluster["cluster_id"] == "c1"
    assert cluster["cluster_name"] == "Cluster1"
    assert cluster["cluster_type"] == "REPLICASET"
    assert cluster["cluster_alerts"] == 2
    assert cluster["cluster_availability"] == "Available"
    assert cluster["cluster_auth_enabled"] is True
    assert cluster["cluster_backup_enabled"] is False
    assert cluster["cluster_ssl_enabled"] is True
    assert cluster["cluster_versions"] == ["6.0"]

@pytest.mark.asyncio
@patch.object(MongoAtlasClient, "send_api_request", new_callable=AsyncMock)
async def test_get_clusters_empty_results(mock_send_api_request, client):
    mock_send_api_request.return_value = {"results": []}
    clusters = await client.get_clusters()
    assert clusters == []

@pytest.mark.asyncio
@patch.object(MongoAtlasClient, "send_api_request", new_callable=AsyncMock)
async def test_get_clusters_malformed_results(mock_send_api_request, client):
    mock_send_api_request.return_value = {"results": "notalist"}
    with pytest.raises(ValueError):
        await client.get_clusters()
