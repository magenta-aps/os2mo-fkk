<!--
SPDX-FileCopyrightText: Magenta ApS <https://magenta.dk>
SPDX-License-Identifier: MPL-2.0
-->

# OS2mo: Fælleskommunalt Klassifikationssystem (FKK)
OS2mo integration for [FKK](https://digitaliseringskataloget.dk/l%C3%B8sninger/klassifikation).


## Usage
```
docker-compose up -d
```
Configuration is done through environment variables. Available options can be
seen in [os2mo_fkk/config.py]. Complex variables such as dict or lists can
be given as JSON strings, as specified by Pydantic's settings parser.


## Fælleskommunalt Klassifikationssystem (FKK)
Most of the documentation for Fælleskommunalt Klassifikationssystem (FKK) and
its supporting services can only be found by downloading zip-files with PDFs.
The main upstream documentation is at
https://digitaliseringskataloget.dk/l%C3%B8sninger/klassifikation/bliv-klar-til-at-kode,
from where most of the required reading is linked.

### MitID Erhverv: Authorization
Access to the FKK SOAP endpoints requires 2-way TLS with client certificates.
These certificates are issued on MitID Erhverv:
https://erhvervsadministration.nemlog-in.dk/.

To issue certificates for Magenta Aps, you must be granted the
`Brugeradministrator` role by another user with the
`Organisationsadministrator` role.

In addition to roles, your user also has a set of rights assigned. A MitID
Erhverv user with the `Rettighedsadministrator` role can grant these. To access
the administration module, used to manage service agreements, you need the
following rights:
  - `KOMBIT STS Administrationsmodulet (test) Aftaleadministrator`.
  - `KOMBIT STS Administrationsmodulet (test) Leverandøradministrator`.
  - `KOMBIT STS Administrationsmodulet Leverandøradministrator`.

We additionally grant the `Aftaleadministrator` on test since we act as a
government agency to approve our own service agreements (which are managed by
the `Leverandøradministrator`).

To access the FKK web interface, you need the following rights:
  - `Fælleskommunalt Klassifikationssystem (test) – Læs`.
  - `Fælleskommunalt Klassifikationssystem - Læs`.

The FKK web interface is available at:
  - https://klassifikation.eksterntest-stoettesystemerne.dk/sts-rest-klassifikation
  - https://klassifikation.stoettesystemerne.dk/sts-rest-klassifikation

### MitID Erhverv: Certificates
NOTE: According to https://digitaliseringskataloget.dk/teknik/certifikater, the
same certificate MUST NOT be used to connect to both the test and production
environment - we must order dedicated certificates for each (environment,
integration)-tuple.

Go to https://erhvervsadministration.nemlog-in.dk/certificates and configure
the new certificate as follows:
  - SE number: `25052943`.
  - Certificate name: `<prod|test>_os2mo_<customer>_fkk`, e.g. `prod_os2mo_viborg_fkk`.
  - Certificate type: `OCES system certificate`.
  - Identification method: `User login`.
  - Select if you want to go directly to issuing the new certificate: `[X]`.
  - Issuing methods: `Internet browser`.

Download the generated certificate and convert it to a proper format without
password protection (we will encrypt it in git):
```sh
openssl pkcs12 -in prod_os2mo_viborg_fkk.p12 -out prod_os2mo_viborg_fkk.pem -noenc
```
Additionally, the public key will need to be uploaded to the Administration
Module. The certificate can be saved without the private key using:
```sh
openssl x509 -in prod_os2mo_viborg_fkk.pem -out prod_os2mo_viborg_fkk.crt -clcerts -nokeys
```

### Administration Module
To call FKK, we must first create and it-system and set up a service agreement
between Magenta and the government authority (e.g. municipality) we wish to
fetch data for. This is done in "Fælleskommunalt Administrationsmodul",
documented here:
https://digitaliseringskataloget.dk/l%C3%B8sninger/administrationsmodul.

The administration module can be accessed on:
  - https://exttestwww.serviceplatformen.dk/administration/
  - https://www.serviceplatformen.dk/administration/

First, create the it-system under "It-systemer":
  - Navn: `prod_os2mo_viborg_fkk`.
  - Type: `Anvendersystem`.

Go to the "Anvendersystem" tab and upload the public certificate from MitID
Erhvervsadministration (`prod_os2mo_viborg_fkk.crt` in the example). Note that this
may require Chromium and/or a desktop environment to drag-and-drop the
certificate.

Go to "Serviceaftaler" and request a new service agreement:
  - Serviceaftaletype: `Uden videregivelse af data`.
  - Navn: `prod_os2mo_viborg_fkk`.
  - Begrundelse: `Synkronisering fra FKK til OS2mo`.
  - System: <the OS2mo system for the customer>.
  - Myndigheder: The customer government authority. Use `MAGENTA ApS` in
    testing to allow approving the agreement yourself.
  - Services:
    - `Klassifikation 7`.
  - Parametre:
    - `Klassifikation 7`: `udstil`.
  - Godkend:
    - Datamodtager(e): **NOTE THIS CVR NUMBER**, it is needed for
      `FKK__AUTHORITY_CONTEXT_CVR`.

Service agreements CANNOT be edited once they have been approved by the
customer, so adding a new service to the agreement requires copying it (using
the button in the interface).

Magenta is registered as a "Testmyndighed" in the TEST system, allowing us to
request and approve a service agreement with ourselves, which we can approve as
if we were a government authority. Otherwise, you need to send an email to the
customer to get the service agreement accepted.

### SOAP
WSDLs are available at:
  - https://klassifikation.eksterntest-stoettesystemerne.dk/klassifikation/7?wsdl

These can be imported into programs such as [SoapUI](https://en.wikipedia.org/wiki/SoapUI).

## Development
The development environment contains a certificate for FKK. This certificate is
intentionally public to allow for CI tests and ease of development.
```bash
docker compose up -d --build
```


## Versioning
This project uses [Semantic Versioning](https://semver.org/) with the following
strategy:
- MAJOR: Incompatible API changes.
- MINOR: Backwards-compatible updates and functionality.
- PATCH: Backwards-compatible bug fixes.


## Authors
Magenta ApS <https://magenta.dk>


## License
- This project: [MPL-2.0](LICENSES/MPL-2.0.txt)

This project uses [REUSE](https://reuse.software) for licensing. All licenses can be found in the [LICENSES folder](LICENSES/) of the project.
