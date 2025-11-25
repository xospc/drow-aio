from decimal import Decimal
from typing import Optional, Any, Generic, TypeVar, ParamSpec, Concatenate
from collections.abc import Callable, Awaitable

from httpx import AsyncClient

from drow.query import (
    RequestArg,
    build_arg_for_query,
    build_arg_for_query_range,
)
from drow.converter import Converter
from drow.parser import (
    QueryResponse,
    QueryRangeResponse,
    BaseParser,
    make_parser,
)

DEFAULT_USER_AGENT = "drow http client"
DEFAULT_TIMEOUT = 10

T = TypeVar("T")
P = ParamSpec("P")
DataType = TypeVar("DataType")
ModelType = TypeVar("ModelType")


class ApiClient:
    def __init__(
        self,
        base_url: str,
        user_agent: str = DEFAULT_USER_AGENT,
        timeout: int = DEFAULT_TIMEOUT,
    ):
        self.base_url = base_url
        self.timeout = timeout

        self._conn = AsyncClient(headers={"User-Agent": user_agent})

    async def _request(  # type: ignore[explicit-any]
        self, arg: RequestArg,
    ) -> Any:
        resp = await self._conn.get(
            url=arg.url,
            params=arg.params,
            timeout=self.timeout,
        )
        return resp.json()  # type: ignore[misc]

    async def query(
        self, metric: str, time: Optional[float] = None,
    ) -> QueryResponse:
        arg = build_arg_for_query(self.base_url, metric, time)
        data: QueryResponse = await self._request(arg)  # type: ignore[misc]
        return data

    async def query_range(
        self, metric: str, start: float, end: float,
        step: Optional[float] = None, step_count: int = 60
    ) -> QueryRangeResponse:
        arg = build_arg_for_query_range(
            self.base_url, metric,
            start=start, end=end,
            step=step, step_count=step_count,
        )
        data: QueryRangeResponse = await self._request(
            arg
        )  # type: ignore[misc]
        return data


def _wrap_parser(
    parse: Callable[[BaseParser[T], DataType], ModelType],
    fetch: Callable[Concatenate[ApiClient, P], Awaitable[DataType]]
) -> Callable[Concatenate["PrometheusClient[T]", P], Awaitable[ModelType]]:
    async def inner(
        self: "PrometheusClient[T]", /, *args: P.args, **kwargs: P.kwargs,
    ) -> ModelType:
        return parse(self.parser, await fetch(self.client, *args, **kwargs))

    return inner


def _wrap_creator(
    converter: Converter[T],
    client_creator: Callable[P, ApiClient],
) -> Callable[P, "PrometheusClient[T]"]:
    def inner(
        *args: P.args, **kwargs: P.kwargs,
    ) -> PrometheusClient[T]:
        api_client = client_creator(*args, **kwargs)
        parser = make_parser(converter)
        return PrometheusClient(api_client, parser)

    return inner


class PrometheusClient(Generic[T]):
    def __init__(self, client: ApiClient, parser: BaseParser[T]):
        self.client = client
        self.parser = parser

    query = _wrap_parser(
        BaseParser.parse_query_response,
        ApiClient.query,
    )
    query_range = _wrap_parser(
        BaseParser.parse_query_range_response,
        ApiClient.query_range,
    )
    query_as_vector = _wrap_parser(
        BaseParser.parse_query_response_as_vector,
        ApiClient.query,
    )
    query_as_value = _wrap_parser(
        BaseParser.parse_query_response_as_value,
        ApiClient.query,
    )
    query_as_value_point = _wrap_parser(
        BaseParser.parse_query_response_as_value_point,
        ApiClient.query,
    )


get_client = _wrap_creator(Decimal, ApiClient)
