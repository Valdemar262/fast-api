from pydantic import BaseModel, ConfigDict


class Page[T](BaseModel):
    items: list[T]
    total: int
    limit: int
    offset: int


class BaseSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)
