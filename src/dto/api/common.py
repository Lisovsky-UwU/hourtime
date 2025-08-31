from pydantic import BaseModel, Field


class ResultResponse(BaseModel):
    result: bool = Field(default=True)

