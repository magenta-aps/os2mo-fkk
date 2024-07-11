# SPDX-FileCopyrightText: Magenta ApS <https://magenta.dk>
# SPDX-License-Identifier: MPL-2.0
import structlog
from cryptography import x509
from datetime import UTC
from datetime import datetime
from fastramqpi.config import Settings as _FastRAMQPISettings
from pathlib import Path
from pydantic.v1 import BaseModel
from pydantic.v1 import BaseSettings
from pydantic.v1 import FilePath
from pydantic.v1 import validator
from typing import Literal
from fastramqpi.ramqp.config import AMQPConnectionSettings

logger = structlog.stdlib.get_logger()


class MOAMQPConnectionSettings(AMQPConnectionSettings):
    exchange = "os2mo_fkk"
    queue_prefix = "os2mo_fkk"
    upstream_exchange = "os2mo"


class FKKAMQPConnectionSettings(AMQPConnectionSettings):
    exchange = "fkk"
    queue_prefix = "fkk"


class FastRAMQPISettings(_FastRAMQPISettings):
    amqp: MOAMQPConnectionSettings


class FKKSettings(BaseModel):
    amqp: FKKAMQPConnectionSettings

    # Use FKK exttest or production environment
    environment: Literal["production", "test"] = "production"

    # See the README for how the certificate should be obtained
    certificate: FilePath = Path("/config/cert.pem")
    certificate_cvr: str = "25052943"  # Magenta Aps

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
