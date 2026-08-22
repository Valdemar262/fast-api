from app.models import Resource
from app.repositories.base import BaseRepository


class ResourceRepository(BaseRepository[Resource]):
    model = Resource
