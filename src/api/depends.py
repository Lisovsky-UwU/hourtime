from fastapi import Depends, FastAPI
from fastapi.security import APIKeyHeader

app = FastAPI()
header_scheme = APIKeyHeader(name="Secret-Token")


async def check_authorization_token(token: str = Depends(header_scheme)) -> str:
    ...

