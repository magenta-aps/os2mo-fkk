# SPDX-FileCopyrightText: Magenta ApS <https://magenta.dk>
# SPDX-License-Identifier: MPL-2.0

from typing import Any

from fastapi import FastAPI
from fastramqpi.main import FastRAMQPI
from fastramqpi.metrics import dipex_last_success_timestamp
from fastramqpi.ramqp import AMQPSystem

from os2mo_fkk import api
from os2mo_fkk import events
from os2mo_fkk.autogenerated_graphql_client import GraphQLClient
from os2mo_fkk.config import Settings
from os2mo_fkk.database import Base
from os2mo_fkk.events import fkk_router
from os2mo_fkk.klassifikation.api import FKKAPI
from os2mo_fkk.klassifikation.event_generator import FKKEventGenerator


def create_app() -> FastAPI:
    settings = Settings()
    fastramqpi = FastRAMQPI(
        application_name="fkk",
        settings=settings.fastramqpi,
        graphql_version=22,
        graphql_client_cls=GraphQLClient,
        database_metadata=Base.metadata,
    )
    fastramqpi.add_context(settings=settings)

    # FKK AMQP system
    fkk_amqp_system = AMQPSystem(
        settings=settings.fkk.amqp,
        router=fkk_router,
        context=fastramqpi.get_context(),
    )

    # FKK API
    fkk_api = FKKAPI(settings=settings.fkk)
    fastramqpi.add_context(fkk_api=fkk_api)

    # FKK event generator
    fkk_event_generator = FKKEventGenerator(
        settings=settings.fkk,
        api=fkk_api,
        amqp_system=fkk_amqp_system,
        sessionmaker=fastramqpi.get_context()["sessionmaker"],
    )

    # The event generator controls the dipex_last_success_timestamp metric
    async def update_dipex_last_success_timestamp(_: Any) -> None:
        last_run = await fkk_event_generator.get_last_run()
        if last_run is None:
            timestamp = 0.0
        else:
            timestamp = last_run.timestamp()
        dipex_last_success_timestamp.set(timestamp)

    fastramqpi.get_context()["instrumentator"].add(update_dipex_last_success_timestamp)

    # Before MO AMQP system
    fastramqpi.add_lifespan_manager(fkk_api, priority=500)
    # After MO AMQP system
    fastramqpi.add_lifespan_manager(fkk_amqp_system, priority=1100)
    fastramqpi.add_lifespan_manager(fkk_event_generator, priority=1200)

    # FastAPI router
    app = fastramqpi.get_app()
    app.include_router(api.router)

    # MO AMQP
    mo_amqp_system = fastramqpi.get_amqpsystem()
    mo_amqp_system.router.registry.update(events.mo_router.registry)

    return app
