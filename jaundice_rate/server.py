import logging
from functools import partial
from typing import Callable, Awaitable, Any

import aiohttp
import anyio
import jsons
from aiohttp import web
from aiohttp.web_request import Request
from pymorphy2 import MorphAnalyzer

from jaundice_rate.analyzer import process_article

logger = logging.getLogger("jaundice_rate.server")


async def url_handler(request: Request, morph: MorphAnalyzer):
    query = request.query
    if "urls" not in query:
        raise web.HTTPNotFound()

    urls = query.get("urls").split(",")

    if len(urls) > 10:
        raise web.HTTPBadRequest(reason="Too many urls in request, should be 10 or less")

    processed_articles = []

    async with aiohttp.ClientSession() as session:
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


def main():
    logging.basicConfig(
        format=u"%(asctime)s [%(levelname)s] %(name)s - %(message)s",
        level=logging.DEBUG,
        datefmt="%H:%M:%S",
    )

    morph = MorphAnalyzer()
    url_handler_partial = partial(url_handler, morph=morph)

    app = web.Application(middlewares=[error_middleware])
    app.add_routes([
        web.get("/", url_handler_partial),
    ])

    web.run_app(app)


if __name__ == "__main__":
    main()
