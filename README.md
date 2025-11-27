# Drow Aio

Prometheus http query client for Python asyncio.

Implemented prometheus http api:
https://prometheus.io/docs/prometheus/latest/querying/api/

[![PyPI Version][pypi-badge]][pypi]
[![Build Status][qaci-badge]][qaci]

## install

    pip install drow-aio

## usage

get client:

    from drow_aio import get_client

    client = get_client("http://127.0.0.1:9090")

query as vector:

    result = await client.query_as_vector("http_requests_total")
    for s in result.series:
        print(s.metric, s.value.timestamp, s.value.value)

query range:

    import time

    end = time.time()
    start = end - 60 * 60

    result = await client.query_range("http_requests_total", start=start, end=end)
    for s in result.series:
        print(s.metric)
        for p in s.values:
            print(p.timestamp, p.value)

[pypi-badge]: https://img.shields.io/pypi/v/drow-aio "PyPI Version"
[pypi]: https://pypi.org/project/drow-aio "PyPI Version"
[qaci-badge]: https://img.shields.io/github/check-runs/xospc/drow-aio/main "Build Status"
[qaci]: https://github.com/xospc/drow-aio/actions "Build Status"
