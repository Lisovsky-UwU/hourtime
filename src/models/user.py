import uuid
from datetime import datetime

from pydantic import BaseModel, Field


class UserModel(BaseModel):
    id: int
    username: str
    display_name: str
    pass_hash: str = Field(exclude=True)


class UserTokenModel(BaseModel):
    id: uuid.UUID
    user_id: int
    token: str
    created_at: datetime

