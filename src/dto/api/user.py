from pydantic import BaseModel


class UserLoginDTO(BaseModel):
    username: str
    password: str


class UserRegisteringDTO(BaseModel):
    username: str
    display_name: str
    password: str

