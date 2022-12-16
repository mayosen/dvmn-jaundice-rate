import asyncio

import aiohttp
import pymorphy2
import pytest

from jaundice_rate.analyzer import ProcessedArticle, ProcessingStatus, fetch, analyze_article, process_article


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


async def test_process_article_fetch_error(morph, session):
    result_list: list[ProcessedArticle] = []
    await process_article(morph, session, "https://inosmi.ru/not/exist.html", result_list)
    assert result_list[0].status == ProcessingStatus.FETCH_ERROR


async def test_process_article_parsing_error(morph, session):
    result_list: list[ProcessedArticle] = []
    await process_article(morph, session, "https://lenta.ru/brief/2021/08/26/afg_terror/", result_list)
    assert result_list[0].status == ProcessingStatus.PARSING_ERROR


async def test_fetch_timeout(session):
    with pytest.raises(asyncio.TimeoutError):
        await fetch(
            session,
            "https://inosmi.ru/20221214/kitay-258839981.html",
            aiohttp.ClientTimeout(0.1),
        )


async def test_analyze_article_timeout(morph, session):
    response = await session.get("https://dvmn.org/media/filer_public/51/83/51830f54-7ec7-4702-847b-c5790ed3724c/gogol_nikolay_taras_bulba_-_bookscafenet.txt")
    big_text = await response.text()
    with pytest.raises(asyncio.TimeoutError):
        await analyze_article(morph, big_text)
