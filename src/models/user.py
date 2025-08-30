import uuid
from datetime import datetime

from pydantic import BaseModel


class UserModel(BaseModel):
    id: int
    username: str
    display_name: str
    pass_hash: str


class UserTokenModel(BaseModel):
    id: uuid.UUID
    user: UserModel
    token: str
    created_at: datetime

