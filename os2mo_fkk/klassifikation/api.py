# SPDX-FileCopyrightText: Magenta ApS <https://magenta.dk>
# SPDX-License-Identifier: MPL-2.0
from itertools import count

import base64
import structlog
from OpenSSL.crypto import X509
from cryptography import x509
from cryptography.hazmat.primitives.asymmetric.dsa import DSAPrivateKey
from cryptography.hazmat.primitives.asymmetric.ec import EllipticCurvePrivateKey
from cryptography.hazmat.primitives.asymmetric.rsa import RSAPrivateKey
from cryptography.hazmat.primitives.serialization import load_pem_private_key
from datetime import UTC
from datetime import datetime, timedelta
from cryptography.hazmat.primitives.serialization import Encoding
import httpx
import signxml
from copy import deepcopy
from lxml import etree
from signxml import SignatureConstructionMethod
from signxml import XMLSigner
from typing import AsyncContextManager

from typing import Self
from uuid import UUID
from uuid import uuid4

# https://stackoverflow.com/questions/72226485/mypy-function-lxml-etree-elementtree-is-not-valid-as-a-type-but-why
from lxml.etree import _Element as Element

from os2mo_fkk.config import FKKSettings
from os2mo_fkk.klassifikation.models import Klasse
from os2mo_fkk.klassifikation.models import _find
from os2mo_fkk.klassifikation.models import _findtext
from os2mo_fkk.klassifikation.models import parse_klasse

logger = structlog.stdlib.get_logger()

TOKEN_REQUEST_XML = """\
<s:Envelope
  xmlns:s="http://www.w3.org/2003/05/soap-envelope"
  xmlns:a="http://www.w3.org/2005/08/addressing"
  xmlns:u="http://docs.oasis-open.org/wss/2004/01/oasis-200401-wss-wssecurity-utility-1.0.xsd">
  <s:Header>
    <a:Action u:Id="action" s:mustUnderstand="1">http://docs.oasis-open.org/ws-sx/ws-trust/200512/RST/Issue</a:Action>
    <a:MessageID u:Id="message-id"></a:MessageID>
    <a:To u:Id="to" s:mustUnderstand="1"></a:To>
    <o:Security xmlns:o="http://docs.oasis-open.org/wss/2004/01/oasis-200401-wss-wssecurity-secext-1.0.xsd" s:mustUnderstand="1">
      <u:Timestamp u:Id="timestamp">
        <u:Created></u:Created>
        <u:Expires></u:Expires>
      </u:Timestamp>
      <o:BinarySecurityToken u:Id="security-binary-security-token" ValueType="http://docs.oasis-open.org/wss/2004/01/oasis-200401-wss-x509-token-profile-1.0#X509v3" EncodingType="http://docs.oasis-open.org/wss/2004/01/oasis-200401-wss-soap-message-security-1.0#Base64Binary"></o:BinarySecurityToken>
    </o:Security>
  </s:Header>
  <s:Body u:Id="body">
    <trust:RequestSecurityToken xmlns:trust="http://docs.oasis-open.org/ws-sx/ws-trust/200512">
      <wsp:AppliesTo xmlns:wsp="http://schemas.xmlsoap.org/ws/2004/09/policy">
        <wsa:EndpointReference xmlns:wsa="http://www.w3.org/2005/08/addressing">
          <wsa:Address>http://entityid.kombit.dk/service/klassifikation/7</wsa:Address>
        </wsa:EndpointReference>
      </wsp:AppliesTo>
      <trust:Claims xmlns:auth="http://docs.oasis-open.org/wsfed/authorization/200706" Dialect="http://docs.oasis-open.org/wsfed/authorization/200706/authclaims">
        <auth:ClaimType Uri="dk:gov:saml:attribute:CvrNumberIdentifier" Optional="false">
          <auth:Value></auth:Value>
        </auth:ClaimType>
      </trust:Claims>
      <trust:KeyType>http://docs.oasis-open.org/ws-sx/ws-trust/200512/PublicKey</trust:KeyType>
      <trust:RequestType>http://docs.oasis-open.org/ws-sx/ws-trust/200512/Issue</trust:RequestType>
      <trust:TokenType>http://docs.oasis-open.org/wss/oasis-wss-saml-token-profile-1.1#SAMLV2.0</trust:TokenType>
      <trust:UseKey>
        <BinarySecurityToken xmlns="http://docs.oasis-open.org/wss/2004/01/oasis-200401-wss-wssecurity-secext-1.0.xsd" u:Id="usekey-binary-security-token" ValueType="http://docs.oasis-open.org/wss/2004/01/oasis-200401-wss-x509-token-profile-1.0#X509v3" EncodingType="http://docs.oasis-open.org/wss/2004/01/oasis-200401-wss-soap-message-security-1.0#Base64Binary"></BinarySecurityToken>
      </trust:UseKey>
    </trust:RequestSecurityToken>
  </s:Body>
</s:Envelope>
"""
TOKEN_REQUEST = etree.fromstring(TOKEN_REQUEST_XML)
TOKEN_KEY_INFO = etree.fromstring(
    '<KeyInfo xmlns:o="http://docs.oasis-open.org/wss/2004/01/oasis-200401-wss-wssecurity-secext-1.0.xsd"><o:SecurityTokenReference><o:Reference ValueType="http://docs.oasis-open.org/wss/2004/01/oasis-200401-wss-x509-token-profile-1.0#X509v3" URI="#security-binary-security-token"/></o:SecurityTokenReference></KeyInfo>'
)

SOAP_REQUEST_XML = """\
<s:Envelope xmlns:s="http://www.w3.org/2003/05/soap-envelope" xmlns:a="http://www.w3.org/2005/08/addressing" xmlns:u="http://docs.oasis-open.org/wss/2004/01/oasis-200401-wss-wssecurity-utility-1.0.xsd">
  <s:Header>
    <a:Action u:Id="action" s:mustUnderstand="1"></a:Action>
    <h:RequestHeader xmlns:h="http://kombit.dk/xml/schemas/RequestHeader/1/" xmlns="http://kombit.dk/xml/schemas/RequestHeader/1/" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xmlns:xsd="http://www.w3.org/2001/XMLSchema">
      <TransactionUUID></TransactionUUID>
    </h:RequestHeader>
    <a:MessageID u:Id="message-id"></a:MessageID>
    <a:To u:Id="to" s:mustUnderstand="1"></a:To>
    <o:Security s:mustUnderstand="1" xmlns:o="http://docs.oasis-open.org/wss/2004/01/oasis-200401-wss-wssecurity-secext-1.0.xsd">
      <u:Timestamp u:Id="timestamp">
        <u:Created></u:Created>
        <u:Expires></u:Expires>
      </u:Timestamp>
    </o:Security>
  </s:Header>
  <s:Body u:Id="body"></s:Body>
</s:Envelope>
"""
SOAP_REQUEST = etree.fromstring(SOAP_REQUEST_XML)


SIGNER = XMLSigner(
    method=SignatureConstructionMethod.detached,
    c14n_algorithm=signxml.CanonicalizationMethod.EXCLUSIVE_XML_CANONICALIZATION_1_0,
)
# Assume `http://www.w3.org/2000/09/xmldsig#` namespace instead of explicit `ds:`
# https://xml-security.github.io/signxml/index.html#xml-representation-details-configuring-namespace-prefixes-and-whitespace
SIGNER.namespaces = {None: signxml.namespaces.ds}  # type: ignore[dict-item]


def _format_time(dt: datetime) -> str:
    """Format datetime to be serviceplatformen-compatible."""
    # The date MUST be formated like `2024-07-10T14:59:44.190Z` (UTC). The timestamp
    # MUST be exactly milliseconds precision, and it MUST use `Z` instead of `+00:00`.
    # We ensure dt is UTC, and replace the timezone with None to avoid `+00:00` in the
    # resulting ISO timestamp, then manually append the `Z` for UTC.
    assert dt.utcoffset() == timedelta(0)
    return dt.replace(tzinfo=None).isoformat(timespec="milliseconds") + "Z"


def _is_token_valid(token: Element) -> bool:
    """Get SAML token expiration time."""
    expires = _find(
        token,
        "{*}Body/{*}RequestSecurityTokenResponseCollection/{*}RequestSecurityTokenResponse/{*}Lifetime/{*}Expires",
    ).text
    assert expires is not None
    return datetime.fromisoformat(expires) > datetime.now(tz=UTC)


class FKKAPI(AsyncContextManager):
    def __init__(self, settings: FKKSettings) -> None:
        """Facade for Fælleskommunalt Klassifikationssystem (FKK)."""
        self.settings = settings
        self._token: Element | None = None
        self.client = httpx.AsyncClient(
            # https://www.python-httpx.org/advanced/ssl/#client-side-certificates
            cert=str(self.settings.certificate),
        )
        # Load certificate
        cert_bytes = self.settings.certificate.read_bytes()
        # The cryptography library supports loading a superset of the PEM key types
        # that XMLSigner supports. Assert that the provided key is supported.
        key = load_pem_private_key(cert_bytes, password=None)
        assert isinstance(key, RSAPrivateKey | DSAPrivateKey | EllipticCurvePrivateKey)
        self.key = key
        cert = x509.load_pem_x509_certificate(cert_bytes)
        self.cert_openssl = X509.from_cryptography(cert)
        # The base64 encoding of a DER-encoded certificate is exactly the same as a regular
        # PEM-encoded certificate, but in a single line and with
        # -----BEGIN CERTIFICATE----- and -----END CERTIFICATE----- removed.
        # This needs to be passed in the token request.
        self.cert_base64 = base64.b64encode(cert.public_bytes(Encoding.DER)).decode(
            "ascii"
        )

    async def __aenter__(self) -> Self:
        await self.client.__aenter__()
        return self

    async def __aexit__(
        self, __exc_type: object, __exc_value: object, __traceback: object
    ) -> None:
        await self.client.__aexit__()

    async def _fetch_token(self) -> Element:
        """Fetch SAML token assertions."""
        # lxml works best with in-place modifications
        envelope = deepcopy(TOKEN_REQUEST)

        # Insert required data
        _find(envelope, "{*}Header/{*}MessageID").text = f"urn:uuid:{uuid4()}"
        _find(envelope, "{*}Header/{*}To").text = self.settings.token_url
        now = datetime.now(UTC)
        _find(
            envelope, "{*}Header/{*}Security/{*}Timestamp/{*}Created"
        ).text = _format_time(now)
        _find(
            envelope, "{*}Header/{*}Security/{*}Timestamp/{*}Expires"
        ).text = _format_time(now + timedelta(minutes=10))
        _find(
            envelope, "{*}Header/{*}Security/{*}BinarySecurityToken"
        ).text = self.cert_base64
        _find(
            envelope, "{*}Body/{*}RequestSecurityToken/{*}Claims/{*}ClaimType/{*}Value"
        ).text = self.settings.certificate_cvr
        _find(
            envelope, "{*}Body/{*}RequestSecurityToken/{*}UseKey/{*}BinarySecurityToken"
        ).text = self.cert_base64

        # Sign the `reference_uri` elements individually
        signed = SIGNER.sign(
            envelope,
            key=self.key,
            cert=[self.cert_openssl],
            reference_uri=[
                "action",
                "message-id",
                "to",
                "timestamp",
                "body",
            ],
            key_info=TOKEN_KEY_INFO,
        )
        # Add the signature (with the digests of each signed element) to the header
        _find(envelope, "{*}Header/{*}Security").append(signed)

        # Perform SOAP request
        content: bytes = etree.tostring(envelope)
        logger.debug("Token request", content=content)
        response = await self.client.post(
            url=self.settings.token_url,
            headers={
                "Content-Type": "application/soap+xml; charset=utf-8",
            },
            content=content,
        )
        logger.debug("Token response", text=response.text)
        response.raise_for_status()
        return etree.fromstring(response.text)

    async def _get_token(self) -> Element:
        """Return cached token or fetch a new one if expired."""
        if self._token is None or not _is_token_valid(self._token):
            self._token = await self._fetch_token()
        # lxml works best with in-place modifications; return a copy to ensure the
        # cached version of the token does not get modified.
        return deepcopy(self._token)

    async def _request(self, url: str, action: str, body: Element) -> Element:
        """Perform SOAP request."""
        # lxml works best with in-place modifications
        envelope = deepcopy(SOAP_REQUEST)

        # Insert required header data
        _find(envelope, "{*}Header/{*}MessageID").text = f"urn:uuid:{uuid4()}"
        _find(envelope, "{*}Header/{*}To").text = url
        _find(envelope, "{*}Header/{*}Action").text = action
        _find(envelope, "{*}Header/{*}RequestHeader/{*}TransactionUUID").text = str(
            uuid4()
        )
        now = datetime.now(UTC)
        _find(
            envelope, "{*}Header/{*}Security/{*}Timestamp/{*}Created"
        ).text = _format_time(now)
        _find(
            envelope, "{*}Header/{*}Security/{*}Timestamp/{*}Expires"
        ).text = _format_time(now + timedelta(minutes=10))

        # Add the supplied body
        _find(envelope, "{*}Body").append(body)

        # Add the Assertion from the token
        token = await self._get_token()
        assertion = _find(
            token,
            "{*}Body/{*}RequestSecurityTokenResponseCollection/{*}RequestSecurityTokenResponse/{*}RequestedSecurityToken/{*}Assertion",
        )
        _find(envelope, "{*}Header/{*}Security").append(assertion)

        # The SecurityTokenReference from the token is both added to the Security header
        # and used as the KeyInfo in our signature. We must add an 'Id' attribute to the
        # one in the header to be able to select it for signing.
        token_reference = _find(
            token,
            "{*}Body/{*}RequestSecurityTokenResponseCollection/{*}RequestSecurityTokenResponse/{*}RequestedAttachedReference/{*}SecurityTokenReference",
        )
        token_reference_with_id = deepcopy(token_reference)
        token_reference_with_id.set(
            "{http://docs.oasis-open.org/wss/2004/01/oasis-200401-wss-wssecurity-utility-1.0.xsd}Id",
            "token-reference",
        )
        _find(envelope, "{*}Header/{*}Security").append(token_reference_with_id)

        key_info = etree.fromstring("<KeyInfo></KeyInfo>")
        key_info.append(token_reference)

        # Sign the `reference_uri` elements individually
        signed = SIGNER.sign(
            envelope,
            key=self.key,
            cert=[self.cert_openssl],
            reference_uri=[
                "action",
                "message-id",
                "to",
                "timestamp",
                "token-reference",
                "body",
            ],
            key_info=key_info,
        )
        # Add the signature (with the digests of each signed element) to the header
        _find(envelope, "{*}Header/{*}Security").append(signed)

        # Perform SOAP request
        content: bytes = etree.tostring(envelope)
        logger.debug("Request", content=content)
        response = await self.client.post(
            url=url,
            headers={
                "Content-Type": f'application/soap+xml; charset=utf-8; action="{action}"',
            },
            content=content,
            # The FKK API seems to be hosted on a spare Raspberry Pi Zero they also
            # use to mine bitcoins.
            timeout=300,
        )
        logger.debug("Response", text=response.text)
        response.raise_for_status()
        return etree.fromstring(response.text)

    async def _search(
        self,
        since: datetime,
        page_limit: int,
        page_offset: int,
        user_key_filter: str | None,
    ) -> set[UUID]:
        body = etree.fromstring(
            """
            <SoegInput xmlns="http://stoettesystemerne.dk/klassifikation/klasse/7/" xmlns:urn="urn:oio:sagdok:3.0.0">
              <urn:FoersteResultatReference></urn:FoersteResultatReference>
              <urn:MaksimalAntalKvantitet></urn:MaksimalAntalKvantitet>
              <urn:SoegRegistrering xmlns="urn:oio:sagdok:3.0.0">
                <urn:FraTidspunkt>
                  <urn:TidsstempelDatoTid></urn:TidsstempelDatoTid>
                </urn:FraTidspunkt>
              </urn:SoegRegistrering>
              <AttributListe/>
              <TilstandListe/>
              <RelationListe>
                <urn:Facet>
                  <urn:ReferenceID>
                    <urn:UUIDIdentifikator>00000c7e-face-4001-8000-000000000000</urn:UUIDIdentifikator>
                  </urn:ReferenceID>
                </urn:Facet>
              </RelationListe>
            </SoegInput>
            """
        )
        _find(body, "{*}FoersteResultatReference").text = str(page_offset)
        _find(body, "{*}MaksimalAntalKvantitet").text = str(page_limit)
        _find(
            body, "{*}SoegRegistrering/{*}FraTidspunkt/{*}TidsstempelDatoTid"
        ).text = _format_time(since)

        if user_key_filter is not None:
            bvn_text = etree.fromstring(
                """
                <Egenskab xmlns:urn="urn:oio:sagdok:3.0.0">
                  <urn:BrugervendtNoegleTekst></urn:BrugervendtNoegleTekst>
                </Egenskab>
                """
            )
            _find(bvn_text, "{*}BrugervendtNoegleTekst").text = user_key_filter
            _find(body, "{*}AttributListe").append(bvn_text)

        # Send request
        data = await self._request(
            url=f"{self.settings.base_url}/klasse/7",
            action="http://kombit.dk/sts/klassifikation/klasse/soeg",
            body=body,
        )

        # Check response status
        status_code = int(
            _findtext(data, "{*}Body/{*}SoegOutput/{*}StandardRetur/{*}StatusKode")
        )
        # 44: Requested object not found
        if status_code == 44:
            return set()
        # 20: Success
        if status_code != 20:  # pragma: no cover
            message = _find(
                data, "{*}Body/{*}SoegOutput/{*}StandardRetur/{*}FejlbeskedTekst"
            ).text
            raise LookupError(f"{status_code=} {message}")

        # Extract UUIDs
        return {
            UUID(u.text)
            for u in data.iterfind(
                "{*}Body/{*}SoegOutput/{*}IdListe/{*}UUIDIdentifikator"
            )
        }

    async def get_changed_uuids(self, since: datetime) -> set[UUID]:
        """Get the set of UUIDs which have been changed since the provided datetime.

        We only search KLE Emneplan (00000c7e-face-4001-8000-000000000000).
        """
        # The endpoint supports a maximum of 500 results per page. Requesting fewer
        # elements does not seem to impact the response time (FKK is probably
        # implemented on top of LoRa).
        page_limit = 500
        changed = set()
        for page_offset in count(step=page_limit):
            logger.info("Getting changed UUIDs", since=since, page_offset=page_offset)
            page = await self._search(
                since=since,
                page_limit=page_limit,
                page_offset=page_offset,
                user_key_filter=self.settings.changed_uuids_user_key_filter,
            )
            if not page:
                break
            changed.update(page)
        return changed

    async def read_raw(self, uuid: UUID) -> Element | None:
        """Read a single object."""
        # Construct read body
        body = etree.fromstring(
            """
            <LaesInput xmlns="http://stoettesystemerne.dk/klassifikation/klasse/7/" xmlns:urn="urn:oio:sagdok:3.0.0">
              <urn:UUIDIdentifikator></urn:UUIDIdentifikator>
              <urn:VirkningFraFilter>
                <urn:GraenseIndikator>true</urn:GraenseIndikator>
              </urn:VirkningFraFilter>
              <urn:VirkningTilFilter>
                <urn:GraenseIndikator>true</urn:GraenseIndikator>
              </urn:VirkningTilFilter>
            </LaesInput>
            """
        )
        _find(body, "{*}UUIDIdentifikator").text = str(uuid)

        # Send request
        data = await self._request(
            url=f"{self.settings.base_url}/klasse/7",
            action="http://kombit.dk/sts/klassifikation/klasse/laes",
            body=body,
        )

        # Check response status
        status_code = int(
            _findtext(data, "{*}Body/{*}LaesOutput/{*}StandardRetur/{*}StatusKode")
        )
        # 44: Requested object not found
        if status_code == 44:
            return None
        # 20: Success
        if status_code != 20:  # pragma: no cover
            message = _find(
                data, "{*}Body/{*}SoegOutput/{*}StandardRetur/{*}FejlbeskedTekst"
            ).text
            raise LookupError(f"{status_code=} {message}")

        return _find(data, "{*}Body/{*}LaesOutput")

    async def read(self, uuid: UUID) -> Klasse | None:
        """Read and parse a single object."""
        raw = await self.read_raw(uuid)
        if raw is None:
            return None
        return parse_klasse(raw)
