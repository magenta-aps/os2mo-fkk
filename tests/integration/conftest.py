# SPDX-FileCopyrightText: Magenta ApS <https://magenta.dk>
# SPDX-License-Identifier: MPL-2.0

import pytest
from asgi_lifespan import LifespanManager
from asgi_lifespan._types import ASGIApp
from collections.abc import AsyncIterator
from fastapi import FastAPI
from gql.client import AsyncClientSession
from httpx import ASGITransport
from httpx import AsyncClient
from pytest import MonkeyPatch
from respx import MockRouter

from os2mo_fkk.app import create_app


@pytest.fixture
async def _app(monkeypatch: MonkeyPatch) -> FastAPI:
    app = create_app()
    return app


@pytest.fixture
async def asgiapp(_app: FastAPI) -> AsyncIterator[ASGIApp]:
    """ASGI app with lifespan run."""
    async with LifespanManager(_app) as manager:
        yield manager.app


@pytest.fixture
async def app(_app: FastAPI, asgiapp: ASGIApp) -> FastAPI:
    """FastAPI app with lifespan run."""
    return _app


@pytest.fixture
async def test_client(asgiapp: ASGIApp) -> AsyncIterator[AsyncClient]:
    """Create test client with associated lifecycles."""
    transport = ASGITransport(app=asgiapp, client=("1.2.3.4", 123))  # type: ignore
    async with AsyncClient(
        transport=transport, base_url="http://example.com"
    ) as client:
        yield client


@pytest.fixture
async def graphql_client(app: FastAPI) -> AsyncClientSession:
    """Authenticated GraphQL codegen client for OS2mo."""
    return app.state.context["graphql_client"]


@pytest.fixture(autouse=True)
def passthrough_fkk(respx_mock: MockRouter) -> None:
    """Allow calls to FKK."""
    respx_mock.route(
        host="adgangsstyring.eksterntest-stoettesystemerne.dk"
    ).pass_through()
    respx_mock.route(
        host="klassifikation.eksterntest-stoettesystemerne.dk"
    ).pass_through()
