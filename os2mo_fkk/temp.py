# SPDX-FileCopyrightText: Magenta ApS <https://magenta.dk>
# SPDX-License-Identifier: MPL-2.0
import asyncio

import httpx


# Du skal have en godkendt serviceaftale for at benytte servicen. Serviceaftaler oprettes i Fælles- kommunalt
# Administrationsmodul.
# https://exttestwww.serviceplatformen.dk/administration/
# Det kræver roller
# - KOMBIT STS Administrationsmodulet (test) Aftaleadministrator
# - KOMBIT STS Administrationsmodulet (test) Leverandøradministrator
# - KOMBIT STS Administrationsmodulet Leverandøradministrator
# på din bruger på https://erhvervsadministration.nemlog-in.dk

# Bestil certifikat på:
# https://erhvervsadministration.nemlog-in.dk/
# Convert to httpx:
# openssl pkcs12 -in test_os2mo_moratest.p12 -out test_os2mo_moratest.pem -noenc

# For at tilgå brugergrænsefladen (under "adgang til brugergrænseflade" på https://digitaliseringskataloget.dk/l%C3%B8sninger/klassifikation/bliv-klar-til-at-kode)
# skal du tildeles rettigheder til 'Fælleskommunalt Klassifikationssystem' på https://erhvervsadministration.nemlog-in.dk.

# WSDL-filer kan hentes på
# https://klassifikation.eksterntest-stoettesystemerne.dk/klassifikationlistehent/2?WSDL

# For at vise typer og operationer:
# python -m zeep 'https://klassifikation.eksterntest-stoettesystemerne.dk/klassifikationlistehent/2?WSDL'

r = httpx.post(
    url="https://n2adgangsstyring.eksterntest-stoettesystemerne.dk/runtime/api/rest/oauth/v1/issue",
    params={
        "grant_type": "client_credentials",
        "client_id": "http://entityid.kombit.dk/service/klassifikationlistehent/2",  # TODO
        # Scope (EntityId) findes på Administrationsmodul > Serviceaftaler > Services > (i)nformation
        "scope": "entityid:http://entityid.kombit.dk/service/klassifikationlistehent/2,anvenderkontekst:25052943",  # TODO
    },
    # https://www.python-httpx.org/advanced/ssl/#client-side-certificates
    cert="/home/caspervk/Downloads/test_os2mo_moratest.pem",
)
print(r.text)
token = r.json()
print(" ".join((token["token_type"], token["access_token"])))
headers = {
    "content-type": "text/xml",
    "Authorization": " ".join((token["token_type"], token["access_token"])),
}

# https://redmine.magenta.dk/attachments/download/26430/Servicebeskrivelse%20til%20KlassifikationListeHent_2.pdf



# from zeep import Client, Settings
#
# settings = Settings(
#     strict=False,
#     xml_huge_tree=True,
#     forbid_entities=False,
#     forbid_external=False,
# )
# client = Client(
#     wsdl="https://klassifikation.eksterntest-stoettesystemerne.dk/klassifikationlistehent/2?wsdl",
#     settings=settings,
# )
# service2 = client.bind(
#     service_name="KlassifikationListeHentService",
#     port_name="KlassifikationListeHentServicePortType",
# )
#
#
# async def main():
#     response = (
#         await service2.KlassifikationListeHent()
#     )  # https://docs.python-zeep.org/en/master/datastructures.html#creating-objects
#     print(response)
#
#
# asyncio.run(main())

body = """<soap:Envelope xmlns:soap="http://www.w3.org/2003/05/soap-envelope" xmlns:ns="http://www.kombit.dk/int/2017/01/01/" xmlns:ns1="http://kombit.dk/xml/schemas/kontekst/2017/01/01/">
   <soap:Header/>
   <soap:Body>
      <ns:KlassifikationListeHent_I revision="1">
         <ns1:HovedOplysninger>
            <ns1:TransaktionsId>abc123</ns1:TransaktionsId>
            <ns1:TransaktionsTid>2002-05-30T09:00:00</ns1:TransaktionsTid>
         </ns1:HovedOplysninger>
         <ns:KlassifikationKriterieListe>
            <ns:IdentifikationKriterie>
               <ns:BrugervendtNoegleKriterie>
                  <ns:KlassifikationBrugervendtNoegle>KLE</ns:KlassifikationBrugervendtNoegle>
               </ns:BrugervendtNoegleKriterie>
            </ns:IdentifikationKriterie>
         </ns:KlassifikationKriterieListe>
      </ns:KlassifikationListeHent_I>
   </soap:Body>
</soap:Envelope>"""

r = httpx.post(
    url="https://klassifikation.eksterntest-stoettesystemerne.dk/klassifikationlistehent/2",
    headers=headers,
    data=body,
)
print(r.text)

# response = requests.post(url,data=body,headers=headers)
# print response.content
