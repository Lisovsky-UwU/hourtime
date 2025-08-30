from pydantic import BaseModel


class CreateUserPayload(BaseModel):
    username: str
    display_name: str
    pass_hash: str


class UpdateUserPayload(BaseModel):
    user_id: int
    username: str
    display_name: str


class CreateUserTokenPayload(BaseModel):
    user_id: int
    token: str

