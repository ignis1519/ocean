from typing import Any
from loguru import logger
from port_ocean.core.ocean_types import ASYNC_GENERATOR_RESYNC_TYPE
from port_ocean.context.ocean import ocean
from mongoatlas.client import MongoAtlasClient
from kinds import Kinds as ObjectKind


## Helper function to initialize the MongoAtlas client
def init_client() -> MongoAtlasClient:
    return MongoAtlasClient(
        ocean.integration_config["mongoatlas_public_key"],
        ocean.integration_config["mongoatlas_private_key"],
    )


@ocean.on_resync(ObjectKind.CLUSTER)
async def on_resync_projects(kind: str) -> ASYNC_GENERATOR_RESYNC_TYPE:
    # This function will only be called for CLUSTER kind
    client = init_client()
    async for clusters in client.get_clusters():
        yield clusters


@ocean.on_start()
async def on_start() -> None:
    # Something to do when the integration starts
    # For example create a client to query 3rd party services - GitHub, Jira, etc...
    print("Starting mongo-atlas integration")
