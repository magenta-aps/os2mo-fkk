# SPDX-FileCopyrightText: Magenta ApS <https://magenta.dk>
# SPDX-License-Identifier: MPL-2.0
from datetime import UTC
from datetime import datetime
from pathlib import Path
from typing import Literal

import structlog
from cryptography import x509
from fastramqpi.config import Settings as _FastRAMQPISettings
from fastramqpi.ramqp.config import AMQPConnectionSettings
from pydantic import BaseModel
from pydantic import BaseSettings
from pydantic import FilePath
from pydantic import validator

logger = structlog.stdlib.get_logger()


class MOAMQPConnectionSettings(AMQPConnectionSettings):
    exchange = "os2mo_fkk"
    queue_prefix = "os2mo_fkk"
    upstream_exchange = "os2mo"
    # The FKK API seems to be hosted on a spare Raspberry Pi Zero they also
    # use to mine bitcoins.
    prefetch_count = 1


class FKKAMQPConnectionSettings(AMQPConnectionSettings):
    exchange = "fkk"
    queue_prefix = "fkk"
    # The FKK API seems to be hosted on a spare Raspberry Pi Zero they also
    # use to mine bitcoins.
    prefetch_count = 1


class FastRAMQPISettings(_FastRAMQPISettings):
    amqp: MOAMQPConnectionSettings


class FKKSettings(BaseModel):
    amqp: FKKAMQPConnectionSettings

    # Use FKK exttest or production environment
    environment: Literal["production", "test"] = "production"

    # The certificate is used to obtain tokens, sign XML, and mutual TLS. See the
    # README for further information.
    certificate: FilePath = Path("/config/cert.pem")

    # The authority context determines which authority (myndighed) we are receiving
    # data for, i.e. which service agreement (serviceaftale) to use. See the README for
    # further information.
    authority_context_cvr: str

    # How often should we check FKK for new klasser?
    interval: int = 1800  # seconds

    # Apply additional `BrugervendtNoegleTekst` filter to the event generator. Set in
    # compose and CI to speed up testing, as starting the event generator from scratch
    # otherwise takes a very long time. Supports wildcards such as `85*`.
    changed_uuids_user_key_filter: str | None

    @validator("certificate", always=True)
    def validate_certificate(cls, cert_path: FilePath) -> FilePath:
        cert = x509.load_pem_x509_certificate(cert_path.read_bytes())
        logger.info(
            "Loaded certificate",
            subject=cert.subject,
            issuer=cert.issuer,
            not_valid_before_utc=cert.not_valid_before_utc,
            not_valid_after_utc=cert.not_valid_after_utc,
        )
        now = datetime.now(tz=UTC)
        if cert.not_valid_before_utc >= now:
            raise ValueError(
                f"Certificate not valid before {cert.not_valid_before_utc}"
            )
        if cert.not_valid_after_utc <= now:
            raise ValueError(f"Certificate not valid after {cert.not_valid_after_utc}")
        return cert_path

    @property
    def base_url(self) -> str:
        match self.environment:
            case "production":  # pragma: no cover
                return "https://klassifikation.stoettesystemerne.dk"
            case "test":
                return "https://klassifikation.eksterntest-stoettesystemerne.dk"

    @property
    def token_url(self) -> str:
        match self.environment:
            case "production":  # pragma: no cover
                return "https://adgangsstyring.stoettesystemerne.dk/runtime/services/kombittrust/14/certificatemixed"
            case "test":
                return "https://adgangsstyring.eksterntest-stoettesystemerne.dk/runtime/services/kombittrust/14/certificatemixed"


class Settings(BaseSettings):
    class Config:
        frozen = True
        env_nested_delimiter = "__"

    fastramqpi: FastRAMQPISettings
    fkk: FKKSettings
