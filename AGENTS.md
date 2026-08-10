<!--
SPDX-FileCopyrightText: Magenta ApS <https://magenta.dk>
SPDX-License-Identifier: MPL-2.0
-->
# Project: OS2mo FKK

## Context
- This is an integration for the OS2mo application (https://github.com/OS2mo/os2mo) that runs as a separate docker-compose service.
- This integration synchronises Klasser from Fælleskommunalt Klassifikationssystem (FKK) into OS2mo as classes under the `kle_number` facet.
- This integration is event-driven:
  - It periodically polls FKK for changed Klasser and emits FKK `change` events on its own AMQP system (`fkk_router`), which trigger synchronisation.
  - It listens to `class` events from OS2mo via the GraphQL event system (`/events/mo/class`) so classes are re-synchronised whenever they change in MO.

## Running Tests
- Unit tests are in `tests/`, except for any sub-directories, like `tests/integration/`, which is for integration tests.
- Integration tests are in `tests/integration/` and are marked with `@pytest.mark.integration_test`.
- Integration tests require the MO stack to be running. Clone and start it first:
  - `git clone https://github.com/OS2mo/os2mo.git`
  - `cd os2mo && docker compose up -d --build`
  - This provides the external `os2mo_default` docker network that this project's `docker-compose.yml` attaches to.
- Tests are run inside the `fkk` service container using Docker Compose:
  - Build and start the supporting services:
    - `docker compose up -d --build`
    - `docker compose stop fkk`  # stop the long-running app so we can run pytest in a one-off container
  - Run all tests:
    - `docker compose run --rm fkk pytest`
  - Run only integration tests:
    - `docker compose run --rm fkk pytest tests/integration`
  - Run only unit tests (skip integration tests):
    - `docker compose run --rm fkk pytest -m 'not integration_test'`
  - Tear everything down when done:
    - `docker compose down`

## Boundaries
- If there are uncommitted changes, do not add them to commits you make. Either commit your changes separately, or if it isn't possible, ask me for permission to commit the existing changes.
