# SPDX-FileCopyrightText: Magenta ApS <https://magenta.dk>
# SPDX-License-Identifier: MPL-2.0
from datetime import UTC
from datetime import datetime
from unittest.mock import MagicMock

import pytest
from fastapi import FastAPI
from httpx import AsyncClient

from os2mo_fkk.klassifikation.api import FKKAPI


@pytest.mark.integration_test
async def test_read_error(test_client: AsyncClient, app: FastAPI) -> None:
    """Test that we handle FKK API errors during read.."""
    # Force status code 40000: "cvc-pattern-valid: Value 'illegal' is not facet-valid".

    bad_uuid = MagicMock()
    bad_uuid.__str__.return_value = "illegal"  # type: ignore[attr-defined]

    fkk_api: FKKAPI = app.state.context["user_context"]["fkk_api"]
    with pytest.raises(LookupError, match="status_code=40000"):
        await fkk_api.read_raw(uuid=bad_uuid)


@pytest.mark.integration_test
async def test_search_error(test_client: AsyncClient, app: FastAPI) -> None:
    """Test that we handle FKK API errors during search.."""
    # Force status code 48000: "The number of occurences to be returned must be
    # between 0 and 10000".
    fkk_api: FKKAPI = app.state.context["user_context"]["fkk_api"]
    with pytest.raises(LookupError, match="status_code=48000"):
        await fkk_api._search(
            since=datetime.now(tz=UTC),
            page_limit=1_000_000,
            page_offset=0,
        )
