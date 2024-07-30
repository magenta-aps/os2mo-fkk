# SPDX-FileCopyrightText: Magenta ApS <https://magenta.dk>
# SPDX-License-Identifier: MPL-2.0
import asyncio
from asyncio import CancelledError
from asyncio import Task
from datetime import UTC
from datetime import datetime
from typing import AsyncContextManager
from typing import Self

import structlog
from fastramqpi.ra_utils.asyncio_utils import gather_with_concurrency
from fastramqpi.ramqp import AMQPSystem
from sqlalchemy import DateTime
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.ext.asyncio import async_sessionmaker
from sqlalchemy.orm import Mapped
from sqlalchemy.orm import mapped_column

from os2mo_fkk.config import FKKSettings
from os2mo_fkk.database import Base
from os2mo_fkk.klassifikation.api import FKKAPI

logger = structlog.stdlib.get_logger()


class LastRun(Base):
    __tablename__ = "last_run"

    id: Mapped[int] = mapped_column(primary_key=True)
    datetime: Mapped[datetime] = mapped_column(DateTime(timezone=True))


class FKKEventGenerator(AsyncContextManager):
    def __init__(
        self,
        settings: FKKSettings,
        api: FKKAPI,
        amqp_system: AMQPSystem,
        sessionmaker: async_sessionmaker[AsyncSession],
    ) -> None:
        """Periodically poll FKK for new Klasser based on LastRun in the database."""
        self._settings = settings
        self._api = api
        self._amqp_system = amqp_system
        self._sessionmaker = sessionmaker
        self._scheduler_task: Task | None = None

    async def __aenter__(self) -> Self:
        """Start event generator."""
        self._scheduler_task = asyncio.create_task(self._scheduler())
        return self

    async def __aexit__(
        self, __exc_tpe: object, __exc_value: object, __traceback: object
    ) -> None:
        """Stop event generator."""
        assert self._scheduler_task is not None
        self._scheduler_task.cancel()

    async def _scheduler(self) -> None:
        """Async task which will run as long as the event-generator is started."""
        logger.info("Starting event-generator")
        while True:
            try:
                await self._generate()
                await asyncio.sleep(self._settings.interval)
            except CancelledError:
                logger.info("Stopping event-generator")
                break
            except Exception:  # pragma: no cover
                logger.exception("Failed to generate events")
                await asyncio.sleep(30)

    async def _generate(self) -> None:
        """One event-generation iteration. Publishes changed UUIDs since last run."""
        logger.info("Generating events")
        async with self._sessionmaker() as session, session.begin():
            # Get last run time from database
            last_run = await session.scalar(select(LastRun))
            if last_run is None:
                last_run = LastRun(datetime=datetime.min.replace(tzinfo=UTC))

            # Fetch changed UUIDs from FKK
            now = datetime.now(UTC)
            changed = await self._api.get_changed_uuids(since=last_run.datetime)
            logger.info("Changes", uuids=changed)

            # Publish changes to internal AMQP exchange
            publish_tasks = [
                self._amqp_system.publish_message(
                    routing_key="change",
                    payload=str(uuid),
                )
                for uuid in changed
            ]
            await gather_with_concurrency(100, *publish_tasks)

            # Update last run time in database
            last_run.datetime = now
            session.add(last_run)

    async def get_last_run(self) -> datetime | None:
        """External interface to retrieve last run."""
        async with self._sessionmaker() as session, session.begin():
            last_run = await session.scalar(select(LastRun))
            if last_run is None:
                return None
            return last_run.datetime
