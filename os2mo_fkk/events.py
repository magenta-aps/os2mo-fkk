# SPDX-FileCopyrightText: Magenta ApS <https://magenta.dk>
# SPDX-License-Identifier: MPL-2.0
import structlog
from fastramqpi.ramqp.mo import MORouter

from os2mo_fkk import depends

router = MORouter()
logger = structlog.get_logger(__name__)


@router.register("class")
async def handler(mo: depends.GraphQLClient) -> None:
    version = await mo.get_version()
    print(version)
