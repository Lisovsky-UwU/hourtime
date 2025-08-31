import json

from fastapi import Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse, Response
from fastapi.routing import APIRoute
from loguru import logger
from sqlalchemy.exc import OperationalError

from src.dto.api.error import ErrorResponse
from src.exceptions import BaseHourtimeException, NotFoundError


def get_request_string(request: Request, request_op: str = "->") -> str:
    if request.client is not None:
        remote_addr = f"{request.client.host}:{request.client.port}"
    else:
        remote_addr = "NO ADDR"

    return (
        f"{remote_addr} [{request.method}] {request_op} {request.url.path}?{request.query_params}"
    )


class LoggingRoute(APIRoute):
    """
    The router class for logging incoming requests and responses to them.
    """

    def get_route_handler(self):  # noqa: ANN201
        original_route_handler = super().get_route_handler()

        async def custom_route_handler(request: Request) -> Response:
            try:
                body = json.dumps(await request.json(), ensure_ascii=False)
            except json.JSONDecodeError:
                body = "NO JSON"

            request_pref = get_request_string(request)

            logger.info("{pref}: {body}", pref=request_pref, body=body)
            logger.debug(
                "{pref} headers: {headers}",
                pref=request_pref,
                headers=json.dumps(dict(request.headers), ensure_ascii=False),
            )

            try:
                response: Response = await original_route_handler(request)

            except BaseHourtimeException as exc:
                logger.error(
                    "Request processing error {pref}: {exc}",
                    pref=request_pref,
                    exc=exc,
                )
                raise

            except RequestValidationError as exc:
                logger.error(
                    f"Request validation error {request_pref}: " + \
                        json.dumps(exc.args[0], ensure_ascii=False)
                        if len(exc.args) > 0 else str(exc),
                )
                raise

            except Exception as exc:
                logger.exception(
                    "Unexpected exception {pref}: {exc}",
                    pref=request_pref,
                    exc=exc,
                )
                raise

            request_pref = get_request_string(request, request_op="<-")
            logger.info(
                "{pref}: {body}",
                pref=request_pref,
                body=response.body.decode() if isinstance(response.body, bytes) else response.body,
            )
            logger.debug(
                "{pref} headers: {headers}",
                pref=request_pref,
                headers=json.dumps(dict(response.headers), ensure_ascii=False),
            )

            return response

        return custom_route_handler

def handle_uncatch_exception(request: Request, exc: Exception) -> Response:
    content = ErrorResponse(
        error_type="UnexpectedException",
        error_code=500,
        user_message="Unknown error inside",
        detail=str(exc),
    ).model_dump_json()
    logger.error(
        "{pref} (ERROR): {body}",
        pref=get_request_string(request, request_op="<-"),
        body=content,
    )
    return Response(
        content=content,
        media_type="application/json",
        status_code=500,
    )

def handle_app_exception(request: Request, exc: BaseHourtimeException) -> Response:
    content = exc.model.model_dump_json()
    logger.info(
        "{pref} (ERROR): {body}",
        pref=get_request_string(request, request_op="<-"),
        body=content,
    )
    return Response(
        content=content,
        media_type="application/json",
        status_code=exc.api_status_code,
    )

def handle_database_error(request: Request, exc: OperationalError) -> Response:
    content = ErrorResponse(
        error_type="DataBaseError",
        error_code=503,
        user_message="Error request to database",
        detail=str(exc),
    ).model_dump_json()
    logger.error(
        "{pref} (ERROR): {body}",
        pref=get_request_string(request, request_op="<-"),
        body=content,
    )
    return Response(
        content=content,
        media_type="application/json",
        status_code=503,
    )

def handle_404_error(request: Request, exc: Exception) -> Response:
    if isinstance(exc, NotFoundError):
        return handle_app_exception(request, exc)
    content = ErrorResponse(
        error_type="RouteNotFound",
        error_code=404,
        user_message="Couldn't find the path",
        detail=None,
    ).model_dump_json()
    logger.error(
        "{pref} (ERROR): {body}",
        pref=get_request_string(request, request_op="<-"),
        body=content,
    )
    return Response(
        content=content,
        media_type="application/json",
        status_code=404,
    )

