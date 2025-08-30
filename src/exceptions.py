from fastapi.responses import JSONResponse, Response


class BaseHourtimeException(Exception):
    api_status_code = 500

    def __init__(self, error_code: int, message: str, detail: str) -> None:
        self.error_code = error_code
        self.message = message
        self.detail = detail
        super().__init__(detail)

    def to_fastapi_response(self) -> Response:
        return JSONResponse(
            content={
                "type": self.__class__.__name__,
                "error_code": self.error_code,
                "user_message": self.message,
                "detail": self.detail,
            },
            status_code=self.api_status_code,
        )

    @classmethod
    def get_response_model(
        cls,
        error_code: int = 999,
        message: str | None = None,
        detail: str = "-",
        api_description: str | None = None,
    ) -> dict:
        result: dict = {
            cls.api_status_code: {
                "content": {
                    "application/json": {
                        "example": {
                            "type": cls.__name__,
                            "error_code": error_code,
                            "user_message": message,
                            "detail": detail,
                        },
                    },
                },
            },
        }
        if api_description:
            result[cls.api_status_code]["description"] = api_description

        return result


class ConfigurationError(BaseHourtimeException):
    api_status_code = 500

