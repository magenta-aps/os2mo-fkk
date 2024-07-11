# SPDX-FileCopyrightText: Magenta ApS <https://magenta.dk>
# SPDX-License-Identifier: MPL-2.0
import structlog
from fastapi import APIRouter
from lxml import etree
from more_itertools import one
from uuid import UUID

from os2mo_fkk import depends
from os2mo_fkk.events import sync
from os2mo_fkk.klassifikation.models import Klasse as FKKKlasse
from os2mo_fkk.models import ClassValidity
from os2mo_fkk.models import fkk_klasse_to_class_validities
from fastapi import Response

router = APIRouter()
logger = structlog.stdlib.get_logger()


@router.get("/read/{uuid}/raw")
async def read_raw(uuid: UUID, fkk: depends.FKKAPI) -> Response:
    """Read raw Klasse from FKK."""
    raw = await fkk.read_raw(uuid)
    if raw is None:
        return Response(status_code=404)
    return Response(
        content=etree.tostring(raw, pretty_print=True),
        media_type="application/xml",
    )


@router.get("/read/{uuid}/parsed")
async def read_parsed(uuid: UUID, fkk: depends.FKKAPI) -> FKKKlasse | None:
    """Read Klasse from FKK and parse it."""
    return await fkk.read(uuid)


@router.get("/read/{uuid}/mo")
async def read_mo(
    uuid: UUID, mo: depends.GraphQLClient, fkk: depends.FKKAPI
) -> list[ClassValidity] | None:
    """Read klassifikation from FKK and convert it to MO validity states."""
    parsed = await fkk.read(uuid)
    if parsed is None:
        return None
    kle_number_facet = one((await mo.get_facet("kle_number")).objects).uuid
    return list(fkk_klasse_to_class_validities(parsed, facet=kle_number_facet))


@router.post("/sync/{uuid}")
async def sync_uuid(uuid: UUID, mo: depends.GraphQLClient, fkk: depends.FKKAPI) -> None:
    """Synchronise klassifikation from FKK to OS2mo."""
    await sync(uuid, mo, fkk)
