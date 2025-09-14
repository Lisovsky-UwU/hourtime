from fastapi.responses import Response

from src.dto.api.error import ErrorResponse


class BaseHourtimeException(Exception):
    _api_status_code = 500

    def __init__(self, error_code: int, message: str, detail: str) -> None:
        self.error_code = error_code
        self.message = message
        self.detail = detail
        super().__init__(detail)

    @property
    def model(self) -> ErrorResponse:
        return ErrorResponse(
            error_type=self.__class__.__name__,
            error_code=self.error_code,
            user_message=self.message,
            detail=self.detail,
        )

    @property
    def api_status_code(self) -> int:
        return self._api_status_code

    def to_fastapi_response(self) -> Response:
        return Response(
            content=self.model,
            status_code=self.api_status_code,
        )

    @classmethod
    def get_response_model(
        cls,
        error_code: int = 999,
        message: str = "No message",
        detail: str | None = None,
        api_description: str | None = None,
    ) -> dict:
        result: dict = {
            cls.api_status_code: {
                "content": {
                    "application/json": {
                        "example": ErrorResponse(
                            error_type=cls.__name__,
                            error_code=error_code,
                            user_message=message,
                            detail=detail,
                        ).model_dump(),
                    },
                },
            },
        }
        if api_description:
            result[cls.api_status_code]["description"] = api_description

        return result


class LogicalError(BaseHourtimeException):
    _api_status_code = 500


class ConfigurationError(BaseHourtimeException):
    _api_status_code = 500


class NotFoundError(BaseHourtimeException):
    _api_status_code = 404


class DataUniqueError(BaseHourtimeException):
    _api_status_code = 409


class AuthentificationError(BaseHourtimeException):
    _api_status_code = 401


class AccessError(BaseHourtimeException):
    _api_status_code = 403

