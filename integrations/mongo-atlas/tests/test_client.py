from typing import Any
from unittest.mock import AsyncMock, MagicMock, patch

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
def mock_mongoatlas_client() -> MongoAtlasClient:
    """Fixture to initialize MongoAtlasClient with mock parameters."""
    return MongoAtlasClient(
        public_key="dummy_public_key",
        private_key="dummy_private_key",
    )


@pytest.mark.asyncio
async def test_client_initialization(mock_mongoatlas_client: MongoAtlasClient) -> None:
    """Test the correct initialization of MongoAtlasClient."""
    assert mock_mongoatlas_client.public_key == "dummy_public_key"
    assert mock_mongoatlas_client.private_key == "dummy_private_key"
    assert mock_mongoatlas_client.http_client is not None
    assert mock_mongoatlas_client.http_client.headers.get("Content-Type") == "application/json"

# @pytest.mark.asyncio
# async def test_send_api_request_failure(mock_mongoatlas_client: MongoAtlasClient) -> None:
#     """Test API request raising exceptions."""
#     with patch.object(
#         mock_mongoatlas_client, "send_api_request", new_callable=AsyncMock
#     ) as mock_request:
#         mock_request.return_value = Response(
#             404, request=Request("GET", "http://example.com")
#         )
#         with pytest.raises(Exception):
#             await mock_mongoatlas_client.send_api_request(endpoint="/v2/clusters", method="GET")

@pytest.mark.asyncio
async def test_get_cluster_list(mock_mongoatlas_client: MongoAtlasClient) -> None:
    """Test send_api_request method to get cluster list."""
    clusters_data = {
        "links": [
            {
                "href": "https://cloud.mongodb.com/api/atlas",
                "rel": "self"
            }
        ],
        "results": [
            {
                "clusters": [
                    {
                        "alertCount": 42,
                        "authEnabled": True,
                        "availability": "available",
                        "backupEnabled": True,
                        "clusterId": "string",
                        "dataSizeBytes": 42,
                        "name": "string",
                        "nodeCount": 42,
                        "sslEnabled": True,
                        "type": "REPLICA_SET",
                        "versions": [
                            "string"
                        ]
                    }
                ],
                "groupId": "string",
                "groupName": "string",
                "orgId": "string",
                "orgName": "string",
                "planType": "string",
                "tags": [
                    "string"
                ]
            }
        ],
        "totalCount": 1
    }

    with patch.object(
        mock_mongoatlas_client, "send_api_request", new_callable=AsyncMock
    ) as mock_request:
        mock_request.return_value = clusters_data
        result = await mock_mongoatlas_client.send_api_request(endpoint="/v2/clusters", method="GET")

        mock_request.assert_called_once_with(
            endpoint="/v2/clusters", method="GET"
        )
        assert result == clusters_data
