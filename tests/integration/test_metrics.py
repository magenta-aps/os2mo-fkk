# SPDX-FileCopyrightText: Magenta ApS <https://magenta.dk>
# SPDX-License-Identifier: MPL-2.0
# mypy: disable-error-code="no-redef"
import re
from datetime import UTC
from datetime import datetime

import pytest
from fastramqpi.pytest_util import retry
from httpx import AsyncClient
from tenacity import stop_after_delay


@pytest.mark.integration_test
async def test_dipex_last_success_timestamp_metric(test_client: AsyncClient) -> None:
    """Test that the event-generator updates the last run metric."""

    async def get_last_run() -> float:
        response = await test_client.get("/metrics")
        assert response.is_success
        match = re.search(
            r"^dipex_last_success_timestamp_seconds (\S+)",
            response.text,
            flags=re.MULTILINE,
        )
        assert match is not None
        return float(match.group(1))

    begin = datetime.now(UTC)

    # Before event-generator runs for the first time
    @retry()
    async def verify() -> None:
        assert await get_last_run() == 0

    await verify()

    # After a while it should finish and update
    @retry(stop=stop_after_delay(120))
    async def verify() -> None:
        assert await get_last_run() > begin.timestamp()

    await verify()
