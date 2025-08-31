from pydantic import BaseModel

from src.models.user import UserModel


class UserLoginRequest(BaseModel):
    username: str
    password: str


class UserRegisteringRequest(BaseModel):
    username: str
    display_name: str
    password: str


class UserAuthentificationResponse(BaseModel):
    token: str
    user_data: UserModel

