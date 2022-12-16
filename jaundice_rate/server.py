import logging
from typing import Callable

import aiohttp
import anyio
import jsons
import pymorphy2
from aiohttp import web, web_request

from analyzer import process_article

logger = logging.getLogger(__name__)
morph = pymorphy2.MorphAnalyzer()


async def url_handler(request: web_request.Request):
    url_string = request.query.get("urls")
    urls = url_string.split(",")

    if len(urls) > 10:
        raise web.HTTPBadRequest(reason="Too many urls in request, should be 10 or less")

    processed_articles = []

    async with aiohttp.ClientSession() as session:
        async with anyio.create_task_group() as tg:
            for url in urls:
                tg.start_soon(process_article, morph, session, url, processed_articles)

    return web.json_response(data=processed_articles, dumps=jsons.dumps)


@web.middleware
async def error_middleware(request: web_request.Request, handler: Callable):
    try:
        return await handler(request)
    except web.HTTPClientError as e:
        return web.json_response({"error": e.reason})


def main():
    logging.basicConfig(
        format=u"%(asctime)s [%(levelname)s] %(name)s - %(message)s",
        level=logging.DEBUG,
        datefmt="%H:%M:%S",
    )

    app = web.Application(middlewares=[error_middleware])
    app.add_routes([
        web.get("/", url_handler),
    ])

    web.run_app(app)


if __name__ == "__main__":
    main()
