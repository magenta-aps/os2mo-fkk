# SPDX-FileCopyrightText: Magenta ApS <https://magenta.dk>
# SPDX-License-Identifier: MPL-2.0
import structlog
from fastapi import APIRouter

router = APIRouter()
logger = structlog.get_logger(__name__)


@router.get("/hello")
async def hello() -> str:
    """Greetings."""
    return "World!"
