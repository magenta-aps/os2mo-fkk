# SPDX-FileCopyrightText: Magenta ApS <https://magenta.dk>
# SPDX-License-Identifier: MPL-2.0
import pytest
from cryptography import x509
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from datetime import datetime
from datetime import timedelta
from pathlib import Path
from pydantic.v1 import ValidationError
from pytest import MonkeyPatch

from os2mo_fkk.config import Settings


@pytest.mark.integration_test
async def test_validation_certificate_expired(
    tmp_path: Path, monkeypatch: MonkeyPatch
) -> None:
    """Test that an error is thrown if using an expired certificate."""
    cert_path = tmp_path.joinpath("cert.pem")

    key = rsa.generate_private_key(public_exponent=65537, key_size=512)
    cert = x509.CertificateBuilder(
        subject_name=x509.Name([]),
        issuer_name=x509.Name([]),
        public_key=key.public_key(),
        serial_number=x509.random_serial_number(),
        not_valid_before=datetime.now() - timedelta(days=200),
        not_valid_after=datetime.now() - timedelta(days=100),
    ).sign(key, hashes.SHA256())
    cert_path.write_bytes(cert.public_bytes(serialization.Encoding.PEM))

    monkeypatch.setenv("FKK__CERTIFICATE", str(cert_path))
    with pytest.raises(ValidationError, match="Certificate not valid after"):
        Settings()


@pytest.mark.integration_test
async def test_validation_certificate_not_valid_yet(
    tmp_path: Path, monkeypatch: MonkeyPatch
) -> None:
    """Test that an error is thrown if using a certificate which isn't yet valid."""
    cert_path = tmp_path.joinpath("cert.pem")

    key = rsa.generate_private_key(public_exponent=65537, key_size=512)
    cert = x509.CertificateBuilder(
        subject_name=x509.Name([]),
        issuer_name=x509.Name([]),
        public_key=key.public_key(),
        serial_number=x509.random_serial_number(),
        not_valid_before=datetime.now() + timedelta(days=200),
        not_valid_after=datetime.now() + timedelta(days=100),
    ).sign(key, hashes.SHA256())
    cert_path.write_bytes(cert.public_bytes(serialization.Encoding.PEM))

    monkeypatch.setenv("FKK__CERTIFICATE", str(cert_path))
    with pytest.raises(ValidationError, match="Certificate not valid before"):
        Settings()
