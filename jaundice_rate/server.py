import asyncio
import logging

from aiohttp import web, web_request

logger = logging.getLogger(__name__)


async def url_handler(request: web_request.Request):
    url_string = request.query.get("urls")
    urls = url_string.split(",")
    data = {
        "urls": urls
    }
    return web.json_response(data)


def main():
    logging.basicConfig(
        format=u"%(asctime)s [%(levelname)s] %(name)s - %(message)s",
        level=logging.DEBUG,
        datefmt="%H:%M:%S",
    )

    app = web.Application()
    app.add_routes([
        web.get("/", url_handler),
    ])

    web.run_app(app)


if __name__ == "__main__":
    main()
