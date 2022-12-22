import logging
from argparse import ArgumentParser
from functools import partial
from os import environ
from typing import Callable, Awaitable, Any

import anyio
import jsons
from aiohttp import web, ClientSession
from aiohttp.web_request import Request
from pymorphy2 import MorphAnalyzer

from jaundice_rate.analyzer import process_article

DEFAULT_URLS_LIMIT = 10
logger = logging.getLogger("jaundice_rate.server")


async def url_handler(request: Request, morph: MorphAnalyzer, urls_limit: int):
    query = request.query
    if "urls" not in query:
        raise web.HTTPNotFound()

    urls = query.get("urls").split(",")

    if len(urls) > urls_limit:
        raise web.HTTPBadRequest(reason=f"Too many urls in request, should be {urls_limit} or less")

    processed_articles = []

    async with ClientSession() as session:
        async with anyio.create_task_group() as tg:
            for url in urls:
                tg.start_soon(process_article, morph, session, url, processed_articles)

    return web.json_response(data=processed_articles, dumps=jsons.dumps)


@web.middleware
async def error_middleware(request: Request, handler: Callable[[Request], Awaitable[Any]]):
    try:
        return await handler(request)
    except web.HTTPClientError as e:
        return web.json_response(data={"error": e.reason}, status=e.status)


def parse_config() -> int:
    parser = ArgumentParser()
    parser.add_argument("--urls-limit", type=int, help="Limit of the URLs number per request", dest="limit")
    args = parser.parse_args()
    limit = args.limit or environ.get("URLS_LIMIT")
    if limit:
        limit = int(limit)
        assert limit > 0
        logging.debug("Using URLs limit: %d", limit)
    else:
        limit = DEFAULT_URLS_LIMIT
        logging.debug("Using default URLs limit: %d", limit)

    return limit


def main():
    logging.basicConfig(
        format=u"%(asctime)s [%(levelname)s] %(name)s - %(message)s",
        level=logging.DEBUG,
        datefmt="%H:%M:%S",
    )
    morph = MorphAnalyzer()
    urls_limit = parse_config()

    app = web.Application(middlewares=[error_middleware])
    app.add_routes([
        web.get("/", partial(url_handler, morph=morph, urls_limit=urls_limit)),
    ])

    web.run_app(app)


if __name__ == "__main__":
    main()
