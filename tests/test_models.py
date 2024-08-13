# SPDX-FileCopyrightText: Magenta ApS <https://magenta.dk>
# SPDX-License-Identifier: MPL-2.0
from datetime import datetime
from datetime import timedelta
from datetime import timezone
from uuid import UUID
from uuid import uuid4

from lxml import etree

from os2mo_fkk.klassifikation.models import Egenskab
from os2mo_fkk.klassifikation.models import Klasse
from os2mo_fkk.klassifikation.models import OverordnetRelation
from os2mo_fkk.klassifikation.models import PubliceretTilstand
from os2mo_fkk.klassifikation.models import Virkning
from os2mo_fkk.klassifikation.models import parse_klasse
from os2mo_fkk.models import ClassValidity
from os2mo_fkk.models import Validity
from os2mo_fkk.models import fkk_klasse_to_class_validities
from os2mo_fkk.util import POSITIVE_INFINITY

TZ = timezone(timedelta(hours=1))

# This Klasse has been modified with more history to properly test our parser
FKK_KLASSE = """
<ns4:LaesOutput xmlns:ns2="http://kombit.dk/xml/schemas/RequestHeader/1/" xmlns:ns3="urn:oio:sagdok:3.0.0" xmlns:ns4="http://stoettesystemerne.dk/klassifikation/klasse/7/" xmlns:ns5="http://stoettesystemerne.dk/klassifikation/facet/7/" xmlns:ns6="urn:oio:sts:7" xmlns:wsu="http://docs.oasis-open.org/wss/2004/01/oasis-200401-wss-wssecurity-utility-1.0.xsd" xmlns:soap="http://www.w3.org/2003/05/soap-envelope">
    <ns3:StandardRetur>
        <ns3:StatusKode>20</ns3:StatusKode>
        <ns3:FejlbeskedTekst>OK</ns3:FejlbeskedTekst>
    </ns3:StandardRetur>
    <ns4:FiltreretOejebliksbillede>
        <ns4:ObjektID>
            <ns3:UUIDIdentifikator>
                0095665f-3685-498b-8ba7-2339d05a5bda
            </ns3:UUIDIdentifikator>
        </ns4:ObjektID>
        <ns4:DataEjer>
            <ns3:CVR>19435075</ns3:CVR>
        </ns4:DataEjer>
        <ns4:Registrering>
            <ns3:Tidspunkt>2024-06-06T11:57:42.000+02:00</ns3:Tidspunkt>
            <ns3:LivscyklusKode>Importeret</ns3:LivscyklusKode>
            <ns3:BrugerRef>
                <ns3:URNIdentifikator>
                    SERIALNUMBER=CVR:19435075-FID:47797575+CN=Klassifikation_P (funktionscertifikat),O=KOMBIT
                    A/S // CVR:19435075,C=DK
                </ns3:URNIdentifikator>
            </ns3:BrugerRef>
            <ns4:AttributListe>
                <ns4:Egenskab>
                    <ns3:Virkning>
                        <ns3:FraTidspunkt>
                            <ns3:TidsstempelDatoTid>
                                1988-01-01T00:00:00.000+01:00
                            </ns3:TidsstempelDatoTid>
                        </ns3:FraTidspunkt>
                        <ns3:TilTidspunkt>
                            <ns3:TidsstempelDatoTid>
                                2001-09-11T00:00:00.000+01:00
                            </ns3:TidsstempelDatoTid>
                        </ns3:TilTidspunkt>
                        <ns3:AktoerRef>
                            <ns3:UUIDIdentifikator>
                                0a424171-4dc1-4c1b-b59d-220ac0d4ce11
                            </ns3:UUIDIdentifikator>
                        </ns3:AktoerRef>
                        <ns3:AktoerTypeKode>Organisation</ns3:AktoerTypeKode>
                        <ns3:NoteTekst>Rettet: 2016-02-01</ns3:NoteTekst>
                    </ns3:Virkning>
                    <ns3:BrugervendtNoegleTekst>
                        85.15.02
                    </ns3:BrugervendtNoegleTekst>
                    <ns3:BeskrivelseTekst>
                        Emnet d&#230;kker bl.a. sager om:
                        Sikkerhedsforanstaltninger ift. it-systemer
                        Sikkerhedskontrol ift. it-systemer
                        IT-sikkerhed, fx regulativer, sikkerhedsregler
                        Tilslutning til Center for Cybersikkerheds
                        netsikkerhedstjeneste
                        Henvisning til andre emner:
                        Sager om it-kriminalitet, se emnenr. 85.15.05
                    </ns3:BeskrivelseTekst>
                    <ns3:TitelTekst>
                        IT-sikkerhed og sikkerhedsforanstaltninger
                    </ns3:TitelTekst>
                    <ns3:RetskildeTekst>
                        BEK om tilslutning til Center for Cybersikkerheds
                        netsikkerhedstjeneste / B20190089605
                        CFCS-Loven / &#167; 3 / A20190083629#P3
                    </ns3:RetskildeTekst>
                    <ns4:Soegeord>
                        <ns3:SoegeordIdentifikator>
                            Center for Cybersikkerhed
                        </ns3:SoegeordIdentifikator>
                        <ns3:SoegeordKategoriTekst>1</ns3:SoegeordKategoriTekst>
                    </ns4:Soegeord>
                    <ns4:Soegeord>
                        <ns3:SoegeordIdentifikator>
                            Cyber, sikkerhed
                        </ns3:SoegeordIdentifikator>
                        <ns3:SoegeordKategoriTekst>1</ns3:SoegeordKategoriTekst>
                    </ns4:Soegeord>
                    <ns4:Soegeord>
                        <ns3:SoegeordIdentifikator>
                            Cyberangreb, IT-sikkerhed
                        </ns3:SoegeordIdentifikator>
                        <ns3:SoegeordKategoriTekst>1</ns3:SoegeordKategoriTekst>
                    </ns4:Soegeord>
                    <ns4:Soegeord>
                        <ns3:SoegeordIdentifikator>
                            Virusangreb, IT-systemers sikkerhed
                        </ns3:SoegeordIdentifikator>
                        <ns3:SoegeordKategoriTekst>1</ns3:SoegeordKategoriTekst>
                    </ns4:Soegeord>
                </ns4:Egenskab>
                <ns4:Egenskab>
                    <ns3:Virkning>
                        <ns3:FraTidspunkt>
                            <ns3:TidsstempelDatoTid>
                                2001-09-11T00:00:00.000+01:00
                            </ns3:TidsstempelDatoTid>
                        </ns3:FraTidspunkt>
                        <ns3:TilTidspunkt>
                            <ns3:GraenseIndikator>true</ns3:GraenseIndikator>
                        </ns3:TilTidspunkt>
                        <ns3:AktoerRef>
                            <ns3:UUIDIdentifikator>
                                394a19fd-dd27-4db1-8218-bd422fc234e1
                            </ns3:UUIDIdentifikator>
                        </ns3:AktoerRef>
                        <ns3:AktoerTypeKode>Organisation</ns3:AktoerTypeKode>
                        <ns3:NoteTekst>Rettet: 2027-07-07</ns3:NoteTekst>
                    </ns3:Virkning>
                    <ns3:BrugervendtNoegleTekst>
                        85.15.1984
                    </ns3:BrugervendtNoegleTekst>
                    <ns3:BeskrivelseTekst>
                        Emnet d&#230;kker bl.a. sager om:
                        Sikkerhedsforanstaltninger ift. it-systemer
                        Sikkerhedskontrol ift. it-systemer
                        IT-sikkerhed, fx regulativer, sikkerhedsregler
                        Tilslutning til Center for Cybersikkerheds
                        netsikkerhedstjeneste
                        Henvisning til andre emner:
                        Sager om it-kriminalitet, se emnenr. 85.15.05
                    </ns3:BeskrivelseTekst>
                    <ns3:TitelTekst>
                        IT-sikkerhed og sikkerhedsforanstaltninger (ulovlig telelogning)
                    </ns3:TitelTekst>
                    <ns3:RetskildeTekst>
                        UKENDT
                    </ns3:RetskildeTekst>
                    <ns4:Soegeord>
                        <ns3:SoegeordIdentifikator>
                            Center for Cybersikkerhed
                        </ns3:SoegeordIdentifikator>
                        <ns3:SoegeordKategoriTekst>1</ns3:SoegeordKategoriTekst>
                    </ns4:Soegeord>
                    <ns4:Soegeord>
                        <ns3:SoegeordIdentifikator>
                            Cyber, sikkerhed
                        </ns3:SoegeordIdentifikator>
                        <ns3:SoegeordKategoriTekst>1</ns3:SoegeordKategoriTekst>
                    </ns4:Soegeord>
                    <ns4:Soegeord>
                        <ns3:SoegeordIdentifikator>
                            Cyberangreb, IT-sikkerhed
                        </ns3:SoegeordIdentifikator>
                        <ns3:SoegeordKategoriTekst>1</ns3:SoegeordKategoriTekst>
                    </ns4:Soegeord>
                    <ns4:Soegeord>
                        <ns3:SoegeordIdentifikator>
                            Virusangreb, IT-systemers sikkerhed
                        </ns3:SoegeordIdentifikator>
                        <ns3:SoegeordKategoriTekst>1</ns3:SoegeordKategoriTekst>
                    </ns4:Soegeord>
                </ns4:Egenskab>
            </ns4:AttributListe>
            <ns4:TilstandListe>
                <ns4:PubliceretStatus>
                    <ns3:Virkning>
                        <ns3:FraTidspunkt>
                            <ns3:TidsstempelDatoTid>
                                1988-01-01T00:00:00.000+01:00
                            </ns3:TidsstempelDatoTid>
                        </ns3:FraTidspunkt>
                        <ns3:TilTidspunkt>
                            <ns3:TidsstempelDatoTid>
                                2037-03-03T00:00:00.000+01:00
                            </ns3:TidsstempelDatoTid>
                        </ns3:TilTidspunkt>
                        <ns3:AktoerRef>
                            <ns3:UUIDIdentifikator>
                                0a424171-4dc1-4c1b-b59d-220ac0d4ce11
                            </ns3:UUIDIdentifikator>
                        </ns3:AktoerRef>
                        <ns3:AktoerTypeKode>Organisation</ns3:AktoerTypeKode>
                        <ns3:NoteTekst>Rettet: 2016-02-01</ns3:NoteTekst>
                    </ns3:Virkning>
                    <ns3:ErPubliceretIndikator>true</ns3:ErPubliceretIndikator>
                </ns4:PubliceretStatus>
                <ns4:PubliceretStatus>
                    <ns3:Virkning>
                        <ns3:FraTidspunkt>
                            <ns3:TidsstempelDatoTid>
                                2037-03-03T00:00:00.000+01:00
                            </ns3:TidsstempelDatoTid>
                        </ns3:FraTidspunkt>
                        <ns3:TilTidspunkt>
                            <ns3:TidsstempelDatoTid>
                                2047-04-04T00:00:00.000+01:00
                            </ns3:TidsstempelDatoTid>
                        </ns3:TilTidspunkt>
                        <ns3:AktoerRef>
                            <ns3:UUIDIdentifikator>
                                12de446a-de0f-40e7-82c9-3c870ddcb947
                            </ns3:UUIDIdentifikator>
                        </ns3:AktoerRef>
                        <ns3:AktoerTypeKode>Organisation</ns3:AktoerTypeKode>
                        <ns3:NoteTekst>Rettet: 2020-02-02</ns3:NoteTekst>
                    </ns3:Virkning>
                    <ns3:ErPubliceretIndikator>false</ns3:ErPubliceretIndikator>
                </ns4:PubliceretStatus>
                <ns4:PubliceretStatus>
                    <ns3:Virkning>
                        <ns3:FraTidspunkt>
                            <ns3:TidsstempelDatoTid>
                                2047-04-04T00:00:00.000+01:00
                            </ns3:TidsstempelDatoTid>
                        </ns3:FraTidspunkt>
                        <ns3:TilTidspunkt>
                            <ns3:GraenseIndikator>true</ns3:GraenseIndikator>
                        </ns3:TilTidspunkt>
                        <ns3:AktoerRef>
                            <ns3:UUIDIdentifikator>
                                94bb476b-e139-4a10-9389-2ddeebe259cf
                            </ns3:UUIDIdentifikator>
                        </ns3:AktoerRef>
                        <ns3:AktoerTypeKode>Organisation</ns3:AktoerTypeKode>
                        <ns3:NoteTekst>Rettet: 2020-02-02</ns3:NoteTekst>
                    </ns3:Virkning>
                    <ns3:ErPubliceretIndikator>true</ns3:ErPubliceretIndikator>
                </ns4:PubliceretStatus>
            </ns4:TilstandListe>
            <ns4:RelationListe>
                <ns3:Ansvarlig>
                    <ns3:Virkning>
                        <ns3:FraTidspunkt>
                            <ns3:TidsstempelDatoTid>
                                1988-01-01T00:00:00.000+01:00
                            </ns3:TidsstempelDatoTid>
                        </ns3:FraTidspunkt>
                        <ns3:TilTidspunkt>
                            <ns3:GraenseIndikator>true</ns3:GraenseIndikator>
                        </ns3:TilTidspunkt>
                        <ns3:AktoerRef>
                            <ns3:UUIDIdentifikator>
                                0a424171-4dc1-4c1b-b59d-220ac0d4ce11
                            </ns3:UUIDIdentifikator>
                        </ns3:AktoerRef>
                        <ns3:AktoerTypeKode>Organisation</ns3:AktoerTypeKode>
                        <ns3:NoteTekst>Rettet: 2016-02-01</ns3:NoteTekst>
                    </ns3:Virkning>
                    <ns3:ReferenceID>
                        <ns3:UUIDIdentifikator>
                            2cc5ef32-69a2-4694-95dd-c74ed9ebf111
                        </ns3:UUIDIdentifikator>
                    </ns3:ReferenceID>
                </ns3:Ansvarlig>
                <ns3:Ejer>
                    <ns3:Virkning>
                        <ns3:FraTidspunkt>
                            <ns3:TidsstempelDatoTid>
                                1988-01-01T00:00:00.000+01:00
                            </ns3:TidsstempelDatoTid>
                        </ns3:FraTidspunkt>
                        <ns3:TilTidspunkt>
                            <ns3:GraenseIndikator>true</ns3:GraenseIndikator>
                        </ns3:TilTidspunkt>
                        <ns3:AktoerRef>
                            <ns3:UUIDIdentifikator>
                                0a424171-4dc1-4c1b-b59d-220ac0d4ce11
                            </ns3:UUIDIdentifikator>
                        </ns3:AktoerRef>
                        <ns3:AktoerTypeKode>Organisation</ns3:AktoerTypeKode>
                        <ns3:NoteTekst>Rettet: 2016-02-01</ns3:NoteTekst>
                    </ns3:Virkning>
                    <ns3:ReferenceID>
                        <ns3:UUIDIdentifikator>
                            0a424171-4dc1-4c1b-b59d-220ac0d4ce11
                        </ns3:UUIDIdentifikator>
                    </ns3:ReferenceID>
                </ns3:Ejer>
                <ns3:Facet>
                    <ns3:Virkning>
                        <ns3:FraTidspunkt>
                            <ns3:TidsstempelDatoTid>
                                1988-01-01T00:00:00.000+01:00
                            </ns3:TidsstempelDatoTid>
                        </ns3:FraTidspunkt>
                        <ns3:TilTidspunkt>
                            <ns3:GraenseIndikator>true</ns3:GraenseIndikator>
                        </ns3:TilTidspunkt>
                        <ns3:AktoerRef>
                            <ns3:UUIDIdentifikator>
                                0a424171-4dc1-4c1b-b59d-220ac0d4ce11
                            </ns3:UUIDIdentifikator>
                        </ns3:AktoerRef>
                        <ns3:AktoerTypeKode>Organisation</ns3:AktoerTypeKode>
                        <ns3:NoteTekst>Rettet: 2016-02-01</ns3:NoteTekst>
                    </ns3:Virkning>
                    <ns3:ReferenceID>
                        <ns3:UUIDIdentifikator>
                            00000c7e-face-4001-8000-000000000000
                        </ns3:UUIDIdentifikator>
                    </ns3:ReferenceID>
                </ns3:Facet>
                <ns3:Mapninger>
                    <ns3:Virkning>
                        <ns3:FraTidspunkt>
                            <ns3:TidsstempelDatoTid>
                                1988-01-01T00:00:00.000+01:00
                            </ns3:TidsstempelDatoTid>
                        </ns3:FraTidspunkt>
                        <ns3:TilTidspunkt>
                            <ns3:GraenseIndikator>true</ns3:GraenseIndikator>
                        </ns3:TilTidspunkt>
                        <ns3:AktoerRef>
                            <ns3:UUIDIdentifikator>
                                0a424171-4dc1-4c1b-b59d-220ac0d4ce11
                            </ns3:UUIDIdentifikator>
                        </ns3:AktoerRef>
                        <ns3:AktoerTypeKode>Organisation</ns3:AktoerTypeKode>
                        <ns3:NoteTekst>Rettet: 2016-02-01</ns3:NoteTekst>
                    </ns3:Virkning>
                    <ns3:ReferenceID>
                        <ns3:UUIDIdentifikator>
                            9759224d-76bd-4cec-9cc3-0d9451ab1cf9
                        </ns3:UUIDIdentifikator>
                        <ns3:Label>K</ns3:Label>
                    </ns3:ReferenceID>
                    <ns3:Rolle>
                        <ns3:UUIDIdentifikator>
                            9ef341c6-251b-4820-a077-9071a9070644
                        </ns3:UUIDIdentifikator>
                        <ns3:Label>Mapning</ns3:Label>
                    </ns3:Rolle>
                    <ns3:Type>
                        <ns3:UUIDIdentifikator>
                            9870b51e-3bc0-4f98-8827-eba991dd89a9
                        </ns3:UUIDIdentifikator>
                        <ns3:Label>Klasse</ns3:Label>
                    </ns3:Type>
                    <ns3:Indeks>
                        <ns3:UUIDIdentifikator>
                            f7d96b02-a5d5-4ac1-a92a-e290544d2546
                        </ns3:UUIDIdentifikator>
                    </ns3:Indeks>
                </ns3:Mapninger>
                <ns3:Mapninger>
                    <ns3:Virkning>
                        <ns3:FraTidspunkt>
                            <ns3:TidsstempelDatoTid>
                                1988-01-01T00:00:00.000+01:00
                            </ns3:TidsstempelDatoTid>
                        </ns3:FraTidspunkt>
                        <ns3:TilTidspunkt>
                            <ns3:GraenseIndikator>true</ns3:GraenseIndikator>
                        </ns3:TilTidspunkt>
                        <ns3:AktoerRef>
                            <ns3:UUIDIdentifikator>
                                0a424171-4dc1-4c1b-b59d-220ac0d4ce11
                            </ns3:UUIDIdentifikator>
                        </ns3:AktoerRef>
                        <ns3:AktoerTypeKode>Organisation</ns3:AktoerTypeKode>
                        <ns3:NoteTekst>Rettet: 2016-02-01</ns3:NoteTekst>
                    </ns3:Virkning>
                    <ns3:ReferenceID>
                        <ns3:UUIDIdentifikator>
                            afe1dbad-326e-4110-a4d8-5a6d8e027d75
                        </ns3:UUIDIdentifikator>
                        <ns3:Label>A21</ns3:Label>
                    </ns3:ReferenceID>
                    <ns3:Rolle>
                        <ns3:UUIDIdentifikator>
                            9ef341c6-251b-4820-a077-9071a9070644
                        </ns3:UUIDIdentifikator>
                        <ns3:Label>Mapning</ns3:Label>
                    </ns3:Rolle>
                    <ns3:Type>
                        <ns3:UUIDIdentifikator>
                            9870b51e-3bc0-4f98-8827-eba991dd89a9
                        </ns3:UUIDIdentifikator>
                        <ns3:Label>Klasse</ns3:Label>
                    </ns3:Type>
                    <ns3:Indeks>
                        <ns3:UUIDIdentifikator>
                            3d183300-51e2-4308-bf5b-e93c24f99d84
                        </ns3:UUIDIdentifikator>
                    </ns3:Indeks>
                </ns3:Mapninger>
                <ns3:OverordnetKlasse>
                    <ns3:Virkning>
                        <ns3:FraTidspunkt>
                            <ns3:TidsstempelDatoTid>
                                1988-01-01T00:00:00.000+01:00
                            </ns3:TidsstempelDatoTid>
                        </ns3:FraTidspunkt>
                        <ns3:TilTidspunkt>
                            <ns3:TidsstempelDatoTid>
                                1996-07-29T00:00:00.000+01:00
                            </ns3:TidsstempelDatoTid>
                        </ns3:TilTidspunkt>
                        <ns3:AktoerRef>
                            <ns3:UUIDIdentifikator>
                                0a424171-4dc1-4c1b-b59d-220ac0d4ce11
                            </ns3:UUIDIdentifikator>
                        </ns3:AktoerRef>
                        <ns3:AktoerTypeKode>Organisation</ns3:AktoerTypeKode>
                        <ns3:NoteTekst>Rettet: 2016-02-01</ns3:NoteTekst>
                    </ns3:Virkning>
                    <ns3:ReferenceID>
                        <ns3:UUIDIdentifikator>
                            8f847ae9-cc68-414a-81b3-6444b46d8480
                        </ns3:UUIDIdentifikator>
                    </ns3:ReferenceID>
                </ns3:OverordnetKlasse>
                <ns3:OverordnetKlasse>
                    <ns3:Virkning>
                        <ns3:FraTidspunkt>
                            <ns3:TidsstempelDatoTid>
                                1996-07-29T00:00:00.000+01:00
                            </ns3:TidsstempelDatoTid>
                        </ns3:FraTidspunkt>
                        <ns3:TilTidspunkt>
                            <ns3:GraenseIndikator>true</ns3:GraenseIndikator>
                        </ns3:TilTidspunkt>
                        <ns3:AktoerRef>
                            <ns3:UUIDIdentifikator>
                                f86aa398-a992-4a03-9ce1-639063b7f9c6
                            </ns3:UUIDIdentifikator>
                        </ns3:AktoerRef>
                        <ns3:AktoerTypeKode>Organisation</ns3:AktoerTypeKode>
                        <ns3:NoteTekst>Rettet: 2024-02-01</ns3:NoteTekst>
                    </ns3:Virkning>
                    <ns3:ReferenceID>
                        <ns3:UUIDIdentifikator>
                            00d7f055-790f-4c2a-a79f-9373d242dd2f
                        </ns3:UUIDIdentifikator>
                    </ns3:ReferenceID>
                </ns3:OverordnetKlasse>
            </ns4:RelationListe>
        </ns4:Registrering>
    </ns4:FiltreretOejebliksbillede>
</ns4:LaesOutput>
"""


def test_parsing() -> None:
    """Test parsing from raw XML, through FKK-Klasse, to ClassValidity."""
    xml = etree.fromstring(FKK_KLASSE)
    fkk_klasse = parse_klasse(xml)
    assert fkk_klasse == Klasse(
        uuid=UUID("0095665f-3685-498b-8ba7-2339d05a5bda"),
        attribut_egenskab=[
            Egenskab(
                virkning=Virkning(
                    fra=datetime(1988, 1, 1, 0, 0, tzinfo=TZ),
                    til=datetime(2001, 9, 11, 0, 0, tzinfo=TZ),
                ),
                brugervendtnoegle="85.15.02",
                titel="IT-sikkerhed og sikkerhedsforanstaltninger",
            ),
            Egenskab(
                virkning=Virkning(
                    fra=datetime(2001, 9, 11, 0, 0, tzinfo=TZ),
                    til=POSITIVE_INFINITY,
                ),
                brugervendtnoegle="85.15.1984",
                titel="IT-sikkerhed og sikkerhedsforanstaltninger (ulovlig telelogning)",
            ),
        ],
        tilstand_publiceret=[
            PubliceretTilstand(
                virkning=Virkning(
                    fra=datetime(1988, 1, 1, 0, 0, tzinfo=TZ),
                    til=datetime(2037, 3, 3, 0, 0, tzinfo=TZ),
                ),
                er_publiceret=True,
            ),
            PubliceretTilstand(
                virkning=Virkning(
                    fra=datetime(2037, 3, 3, 0, 0, tzinfo=TZ),
                    til=datetime(2047, 4, 4, 0, 0, tzinfo=TZ),
                ),
                er_publiceret=False,
            ),
            PubliceretTilstand(
                virkning=Virkning(
                    fra=datetime(2047, 4, 4, 0, 0, tzinfo=TZ),
                    til=POSITIVE_INFINITY,
                ),
                er_publiceret=True,
            ),
        ],
        relation_overordnet=[
            OverordnetRelation(
                virkning=Virkning(
                    fra=datetime(1988, 1, 1, 0, 0, tzinfo=TZ),
                    til=datetime(1996, 7, 29, 0, 0, tzinfo=TZ),
                ),
                uuid=UUID("8f847ae9-cc68-414a-81b3-6444b46d8480"),
            ),
            OverordnetRelation(
                virkning=Virkning(
                    fra=datetime(1996, 7, 29, 0, 0, tzinfo=TZ),
                    til=POSITIVE_INFINITY,
                ),
                uuid=UUID("00d7f055-790f-4c2a-a79f-9373d242dd2f"),
            ),
        ],
    )

    facet_uuid = uuid4()
    class_validities = list(
        fkk_klasse_to_class_validities(fkk_klasse, facet=facet_uuid)
    )
    assert class_validities == [
        ClassValidity(
            facet=facet_uuid,
            validity=Validity(
                start=datetime(1988, 1, 1, 0, 0, tzinfo=TZ),
                end=datetime(1996, 7, 29, 0, 0, tzinfo=TZ),
            ),
            uuid=UUID("0095665f-3685-498b-8ba7-2339d05a5bda"),
            user_key="85.15.02",
            name="IT-sikkerhed og sikkerhedsforanstaltninger",
            parent=UUID("8f847ae9-cc68-414a-81b3-6444b46d8480"),
        ),
        ClassValidity(
            facet=facet_uuid,
            validity=Validity(
                start=datetime(1996, 7, 29, 0, 0, tzinfo=TZ),
                end=datetime(2001, 9, 11, 0, 0, tzinfo=TZ),
            ),
            uuid=UUID("0095665f-3685-498b-8ba7-2339d05a5bda"),
            user_key="85.15.02",
            name="IT-sikkerhed og sikkerhedsforanstaltninger",
            parent=UUID("00d7f055-790f-4c2a-a79f-9373d242dd2f"),
        ),
        ClassValidity(
            facet=facet_uuid,
            validity=Validity(
                start=datetime(2001, 9, 11, 0, 0, tzinfo=TZ),
                end=datetime(2037, 3, 3, 0, 0, tzinfo=TZ),
            ),
            uuid=UUID("0095665f-3685-498b-8ba7-2339d05a5bda"),
            user_key="85.15.1984",
            name="IT-sikkerhed og sikkerhedsforanstaltninger (ulovlig telelogning)",
            parent=UUID("00d7f055-790f-4c2a-a79f-9373d242dd2f"),
        ),
        ClassValidity(
            facet=facet_uuid,
            validity=Validity(
                start=datetime(2047, 4, 4, 0, 0, tzinfo=TZ),
                end=POSITIVE_INFINITY,
            ),
            uuid=UUID("0095665f-3685-498b-8ba7-2339d05a5bda"),
            user_key="85.15.1984",
            name="IT-sikkerhed og sikkerhedsforanstaltninger (ulovlig telelogning)",
            parent=UUID("00d7f055-790f-4c2a-a79f-9373d242dd2f"),
        ),
    ]


def test_nothing() -> None:
    """CI requires at least two unittests due to pytest-split."""
    assert True
