from pydantic import BaseModel


class UserModel(BaseModel):
    id: int
    username: str
    display_name: str
    pass_hash: str

