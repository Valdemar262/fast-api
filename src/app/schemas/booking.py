from datetime import datetime
from typing import Self

from pydantic import model_validator

from app.schemas.base import BaseSchema


class BookingCreate(BaseSchema):
    resource_id: int
    start_time: datetime
    end_time: datetime

    @model_validator(mode="after")
    def check_time_range(self) -> Self:
        if self.start_time >= self.end_time:
            raise ValueError("start_time must be earlier than end_time")
        return self


class BookingRead(BaseSchema):
    id: int
    user_id: int
    resource_id: int
    start_time: datetime
    end_time: datetime
    created_at: datetime
    updated_at: datetime
