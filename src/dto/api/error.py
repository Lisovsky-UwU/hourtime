from pydantic import BaseModel


class ErrorResponse(BaseModel):
    error_type: str
    error_code: int
    user_message: str
    detail: str | None

