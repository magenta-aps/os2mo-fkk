# SPDX-FileCopyrightText: Magenta ApS <https://magenta.dk>
# SPDX-License-Identifier: MPL-2.0
import pytest
from httpx import AsyncClient
from unittest.mock import ANY


@pytest.mark.integration_test
async def test_read_raw(test_client: AsyncClient) -> None:
    """Test fetch from FKK."""
    response = await test_client.get("/read/0095665f-3685-498b-8ba7-2339d05a5bda/raw")
    assert response.text


@pytest.mark.integration_test
async def test_read_raw_non_existent(test_client: AsyncClient) -> None:
    """Test return None."""
    response = await test_client.get("/read/00000000-0000-0000-0000-000000000000/raw")
    assert response.status_code == 404


@pytest.mark.integration_test
async def test_read_parsed(test_client: AsyncClient) -> None:
    """Test FKK Klasse parsing."""
    response = await test_client.get(
        "/read/0095665f-3685-498b-8ba7-2339d05a5bda/parsed"
    )
    assert response.json() == {
        "uuid": "0095665f-3685-498b-8ba7-2339d05a5bda",
        "attribut_egenskab": [
            {
                "virkning": {
                    "fra": "1988-01-01T00:00:00+01:00",
                    "til": "9999-12-31T23:59:59.999999Z",
                },
                "brugervendtnoegle": "85.15.02",
                "titel": "IT-sikkerhed og sikkerhedsforanstaltninger",
            }
        ],
        "tilstand_publiceret": [
            {
                "virkning": {
                    "fra": "1988-01-01T00:00:00+01:00",
                    "til": "9999-12-31T23:59:59.999999Z",
                },
                "er_publiceret": True,
            }
        ],
        "relation_overordnet": [
            {
                "virkning": {
                    "fra": "1988-01-01T00:00:00+01:00",
                    "til": "9999-12-31T23:59:59.999999Z",
                },
                "uuid": "8f847ae9-cc68-414a-81b3-6444b46d8480",
            }
        ],
    }


@pytest.mark.integration_test
async def test_read_parsed_non_existent(test_client: AsyncClient) -> None:
    """Test return None."""
    response = await test_client.get(
        "/read/00000000-0000-0000-0000-000000000000/parsed"
    )
    assert response.json() is None


@pytest.mark.integration_test
async def test_read_mo(test_client: AsyncClient) -> None:
    """Test FKK Klasse conversion to MO Class."""
    response = await test_client.get("/read/0095665f-3685-498b-8ba7-2339d05a5bda/mo")
    assert response.json() == [
        {
            "facet": ANY,
            "validity": {"end": None, "start": "1988-01-01T00:00:00+01:00"},
            "uuid": "0095665f-3685-498b-8ba7-2339d05a5bda",
            "user_key": "85.15.02",
            "name": "IT-sikkerhed og sikkerhedsforanstaltninger",
            "parent": "8f847ae9-cc68-414a-81b3-6444b46d8480",
        },
    ]


@pytest.mark.integration_test
async def test_read_mo_non_existent(test_client: AsyncClient) -> None:
    """Test return None."""
    response = await test_client.get("/read/00000000-0000-0000-0000-000000000000/mo")
    assert response.json() is None
