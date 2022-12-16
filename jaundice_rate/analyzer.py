import asyncio
import logging
from enum import Enum
from typing import Optional

import aiohttp
import anyio
import async_timeout
import pymorphy2
from aiohttp import ClientSession
from pymorphy2 import MorphAnalyzer

from jaundice_rate.adapters import SANITIZERS, ArticleNotFound
from jaundice_rate.timer import timing
from jaundice_rate.text_tools import split_by_words, calculate_jaundice_rate
from jaundice_rate.words_tools import CHARGED_WORDS

logger = logging.getLogger(__name__)


class ProcessingStatus(Enum):
    OK = "OK"
    FETCH_ERROR = "FETCH_ERROR"
    PARSING_ERROR = "PARSING_ERROR"
    TIMEOUT = "TIMEOUT"


class ProcessedArticle:
    def __init__(self, url: str, status: ProcessingStatus, rating: Optional[float] = None, words: Optional[int] = None):
        self.url = url
        self.status = status
        self.rating = rating
        self.words = words

    def format(self):
        return (
            f"URL: {self.url}\n"
            f"Статус: {self.status.value}\n"
            f"Рейтинг: {self.rating}\n"
            f"Слов в статье: {self.words}\n"
        )


async def fetch(session: aiohttp.ClientSession, url: str, timeout: aiohttp.ClientTimeout = aiohttp.ClientTimeout(2)):
    async with session.get(url, timeout=timeout) as response:
        response.raise_for_status()
        return await response.text()


async def analyze_article(morph: MorphAnalyzer, text: str):
    async with async_timeout.timeout(3):
        return await split_by_words(morph, text)


async def process_article(morph: MorphAnalyzer, session: ClientSession, url: str, result_list: list[ProcessedArticle]):
    try:
        html = await fetch(session, url)
        sanitizer = SANITIZERS.get("inosmi_ru")

        with timing() as timer:
            plaintext = sanitizer(html, plaintext=True)
            article_words = await analyze_article(morph, plaintext)
            rate = calculate_jaundice_rate(article_words, CHARGED_WORDS)

        result_list.append(ProcessedArticle(url, ProcessingStatus.OK, rate, len(article_words)))
        logger.info("Анализ %s закончен за %.2f сек", url, round(timer.elapsed, 2))

    except aiohttp.ClientError:
        result_list.append(ProcessedArticle(url, ProcessingStatus.FETCH_ERROR))
        logger.warning("Анализ %s прерван: %s", url, ProcessingStatus.FETCH_ERROR.value)

    except ArticleNotFound:
        result_list.append(ProcessedArticle(url, ProcessingStatus.PARSING_ERROR))
        logger.warning("Анализ %s прерван: %s", url, ProcessingStatus.PARSING_ERROR.value)

    except asyncio.TimeoutError:
        result_list.append(ProcessedArticle(url, ProcessingStatus.TIMEOUT))
        logger.warning("Анализ %s прерван: %s", url, ProcessingStatus.TIMEOUT.value)


async def main():
    logging.basicConfig(
        format="[%(asctime)s.%(msecs).03d] %(levelname)s [%(name)s] %(message)s",
        datefmt="%H:%M:%S",
        level=logging.DEBUG,
    )

    TEST_ARTICLES = [
        "https://inosmi.ru/20221214/eneregetika-258837716.html",
        "https://inosmi.ru/20221214/kitay-258839981.html",
        "https://inosmi.ru/20221214/ultrapravye-258844791.html",
        "https://inosmi.ru/20221214/kitay-258839420.html",
        "https://inosmi.ru/20221214/katargeyt-258839069.html",
        "https://inosmi.ru/not/exist.html",
        "https://lenta.ru/brief/2021/08/26/afg_terror/",
    ]

    morph = pymorphy2.MorphAnalyzer()

    async with aiohttp.ClientSession() as session:
        processed_articles: list[ProcessedArticle] = []

        async with anyio.create_task_group() as tg:
            for url in TEST_ARTICLES:
                tg.start_soon(process_article, morph, session, url, processed_articles)

        formatted_articles = [article.format() for article in processed_articles]
        print("\n".join(formatted_articles))


if __name__ == "__main__":
    asyncio.run(main())
