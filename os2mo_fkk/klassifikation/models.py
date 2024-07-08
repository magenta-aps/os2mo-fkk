# SPDX-FileCopyrightText: Magenta ApS <https://magenta.dk>
# SPDX-License-Identifier: MPL-2.0
from datetime import datetime
from typing import TypeVar
from uuid import UUID

# https://stackoverflow.com/questions/72226485/mypy-function-lxml-etree-elementtree-is-not-valid-as-a-type-but-why
from lxml.etree import _Element as Element

from os2mo_fkk.util import NEGATIVE_INFINITY
from os2mo_fkk.util import POSITIVE_INFINITY
from os2mo_fkk.util import StrictBaseModel


def _find(element: Element, path: str) -> Element:
    """lxml find() but cannot return None."""
    subelement = element.find(path)
    assert subelement is not None
    return subelement


def _findtext(element: Element, path: str) -> str:
    """lxml findtext() but cannot return None."""
    text = _find(element, path).text
    assert text is not None
    # Remove leading and trailing whitespace
    return text.strip()


BOOLEANS = {
    "false": False,
    "true": True,
}


class Virkning(StrictBaseModel):
    fra: datetime
    til: datetime


class VirkningMixin(StrictBaseModel):
    virkning: Virkning


HasVirking = TypeVar("HasVirking", bound=VirkningMixin)


class Egenskab(VirkningMixin):
    brugervendtnoegle: str
    titel: str


class PubliceretTilstand(VirkningMixin):
    er_publiceret: bool


class OverordnetRelation(VirkningMixin):
    uuid: UUID


class Klasse(StrictBaseModel):
    uuid: UUID
    attribut_egenskab: list[Egenskab]
    tilstand_publiceret: list[PubliceretTilstand]
    relation_overordnet: list[OverordnetRelation]


def _parse_tidspunkt(tidspunkt: Element, limit: datetime) -> datetime:
    limit_indicator = tidspunkt.find("{*}GraenseIndikator")
    if limit_indicator is None:
        return datetime.fromisoformat(_findtext(tidspunkt, "{*}TidsstempelDatoTid"))
    if limit_indicator.text is None or not BOOLEANS[limit_indicator.text]:
        raise ValueError("Unknown GraenseIndikator")  # pragma: no cover
    return limit


def _parse_virkning(virkning: Element) -> Virkning:
    return Virkning(
        fra=_parse_tidspunkt(
            _find(virkning, "{*}FraTidspunkt"), limit=NEGATIVE_INFINITY
        ),
        til=_parse_tidspunkt(
            _find(virkning, "{*}TilTidspunkt"), limit=POSITIVE_INFINITY
        ),
    )


def parse_klasse(element: Element) -> Klasse:
    # UUID
    uuid = _findtext(
        element, "{*}FiltreretOejebliksbillede/{*}ObjektID/{*}UUIDIdentifikator"
    )

    registrering = _find(element, "{*}FiltreretOejebliksbillede/{*}Registrering")

    # AttributListe/Egenskab
    def parse_egenskab(egenskab: Element) -> Egenskab:
        return Egenskab(
            virkning=_parse_virkning(_find(egenskab, "{*}Virkning")),
            brugervendtnoegle=_findtext(egenskab, "{*}BrugervendtNoegleTekst"),
            titel=_findtext(egenskab, "{*}TitelTekst"),
        )

    attribut_egenskab = [
        parse_egenskab(egenskab)
        for egenskab in registrering.findall("{*}AttributListe/{*}Egenskab")
    ]

    # TilstandListe/PubliceretStatus
    def parse_publiceret(publiceret: Element) -> PubliceretTilstand:
        return PubliceretTilstand(
            virkning=_parse_virkning(_find(publiceret, "{*}Virkning")),
            er_publiceret=BOOLEANS[_findtext(publiceret, "{*}ErPubliceretIndikator")],
        )

    tilstand_publiceret = [
        parse_publiceret(publiceret)
        for publiceret in registrering.findall("{*}TilstandListe/{*}PubliceretStatus")
    ]

    # RelationListe/OverordnetKlasse
    def parse_overordnet(overordnet: Element) -> OverordnetRelation:
        return OverordnetRelation(
            virkning=_parse_virkning(_find(overordnet, "{*}Virkning")),
            uuid=_findtext(overordnet, "{*}ReferenceID/{*}UUIDIdentifikator"),
        )

    relation_overordnet = [
        parse_overordnet(overordnet)
        for overordnet in registrering.findall("{*}RelationListe/{*}OverordnetKlasse")
    ]

    return Klasse(
        uuid=uuid,
        attribut_egenskab=attribut_egenskab,
        tilstand_publiceret=tilstand_publiceret,
        relation_overordnet=relation_overordnet,
    )
