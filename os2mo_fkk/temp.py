# SPDX-FileCopyrightText: Magenta ApS <https://magenta.dk>
# SPDX-License-Identifier: MPL-2.0
import httpx

# Du skal have en godkendt serviceaftale for at benytte servicen. Serviceaftaler oprettes i Fælles- kommunalt
# Administrationsmodul.
# https://exttestwww.serviceplatformen.dk/administration/
# Bestil certifikat på:
# https://erhvervsadministration.nemlog-in.dk/
# Convert to httpx:
# openssl pkcs12 -in test_os2mo_moratest.p12 -out test_os2mo_moratest.pem -noenc

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

access_token = r.json()["access_token"]

# https://redmine.magenta.dk/attachments/download/26430/Servicebeskrivelse%20til%20KlassifikationListeHent_2.pdf
r = httpx.get(
    url="https://klassifikation.eksterntest-stoettesystemerne.dk/klassifikationlistehent/2",
)
print(r.text)
