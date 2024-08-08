# SPDX-FileCopyrightText: Magenta ApS <https://magenta.dk>
# SPDX-License-Identifier: MPL-2.0
from datetime import UTC
from datetime import datetime

from pydantic import BaseModel
from pydantic import Extra

NEGATIVE_INFINITY = datetime.min.replace(tzinfo=UTC)
POSITIVE_INFINITY = datetime.max.replace(tzinfo=UTC)


class StrictBaseModel(BaseModel):
    """Pydantic BaseModel with strict(er) defaults."""

    class Config:
        extra = Extra.forbid
        frozen = True
