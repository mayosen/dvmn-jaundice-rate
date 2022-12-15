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

from adapters import SANITIZERS, ArticleNotFound
from timer import timing
from text_tools import split_by_words, calculate_jaundice_rate
from words_tools import CHARGED_WORDS

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


async def fetch(session: aiohttp.ClientSession, url: str):
    async with session.get(url, timeout=aiohttp.ClientTimeout(2), raise_for_status=True) as response:
        return await response.text()


async def process_article(morph: MorphAnalyzer, session: ClientSession, url: str, result_list: list[ProcessedArticle]):
    try:
        html = await fetch(session, url)

        with timing() as timer:
            sanitizer = SANITIZERS.get("inosmi_ru")
            plaintext = sanitizer(html, plaintext=True)
            # plaintext = await fetch(session, "https://dvmn.org/media/filer_public/51/83/51830f54-7ec7-4702-847b-c5790ed3724c/gogol_nikolay_taras_bulba_-_bookscafenet.txt")

            async with async_timeout.timeout(3):
                article_words = await split_by_words(morph, plaintext)

            rate = calculate_jaundice_rate(article_words, CHARGED_WORDS)

        logger.info("Анализ %s закончен за %.2f сек", url, round(timer.elapsed, 2))
        result_list.append(ProcessedArticle(url, ProcessingStatus.OK, rate, len(article_words)))

    except aiohttp.ClientError:
        result_list.append(ProcessedArticle(url, ProcessingStatus.FETCH_ERROR))

    except ArticleNotFound:
        result_list.append(ProcessedArticle(url, ProcessingStatus.PARSING_ERROR))
        # TODO: Логичнее выбрасывать ошибку по отсутствию нужного санитайзера в SANITIZERS

    except asyncio.TimeoutError:
        result_list.append(ProcessedArticle(url, ProcessingStatus.TIMEOUT))
        # TODO: Тесты на все исключения


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
