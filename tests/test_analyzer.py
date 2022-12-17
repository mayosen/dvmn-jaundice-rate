import asyncio
from unittest.mock import patch

import aiohttp
import anyio
import pymorphy2
import pytest
from aiohttp import web

from jaundice_rate.analyzer import ProcessedArticle, ProcessingStatus, fetch, process_article


@pytest.fixture(scope="session")
def morph():
    return pymorphy2.MorphAnalyzer()


@pytest.fixture
async def session():
    session = aiohttp.ClientSession()
    try:
        yield session
    finally:
        await session.close()


async def test_fetch_timeout(aiohttp_client):
    async def timeout_handler(_):
        await anyio.sleep(10)
        return web.Response()

    app = web.Application()
    app.router.add_route("GET", "/", timeout_handler)
    client = await aiohttp_client(app)

    with pytest.raises(asyncio.TimeoutError):
        await fetch(client, "/")


async def test_process_article_timeout(morph, session, aiohttp_client):
    big_text_response = await session.get("https://dvmn.org/media/filer_public/51/83/51830f54-7ec7-4702-847b-c5790ed3724c/gogol_nikolay_taras_bulba_-_bookscafenet.txt")
    big_text = await big_text_response.text()

    async def handler(_):
        return web.Response()

    app = web.Application()
    app.router.add_route("GET", "/", handler)
    client = await aiohttp_client(app)

    def sanitize(*args, **kwargs):
        return big_text

    result_list: list[ProcessedArticle] = []

    with patch.dict("jaundice_rate.adapters.SANITIZERS", {"inosmi_ru": sanitize}):
        await process_article(morph, client, "/", result_list)

    assert result_list[0].status == ProcessingStatus.TIMEOUT


async def test_process_article_fetch_error(morph, session):
    result_list: list[ProcessedArticle] = []
    await process_article(morph, session, "https://inosmi.ru/not/exist.html", result_list)
    assert result_list[0].status == ProcessingStatus.FETCH_ERROR


async def test_process_article_parsing_error(morph, session):
    result_list: list[ProcessedArticle] = []
    await process_article(morph, session, "https://lenta.ru/brief/2021/08/26/afg_terror/", result_list)
    assert result_list[0].status == ProcessingStatus.PARSING_ERROR
