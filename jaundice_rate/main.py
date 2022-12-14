import asyncio
from dataclasses import dataclass
from enum import Enum
from typing import Optional

import aiohttp
import anyio
import pymorphy2

from adapters import SANITIZERS
from text_tools import split_by_words, calculate_jaundice_rate
from words_tools import CHARGED_WORDS


async def fetch(session: aiohttp.ClientSession, url: str):
    async with session.get(url) as response:
        response.raise_for_status()
        return await response.text()


class ProcessingStatus(Enum):
    OK = "OK"
    FETCH_ERROR = "FETCH_ERROR"


@dataclass
class ProcessedArticle:
    url: str
    status: ProcessingStatus
    rating: Optional[float]
    words: Optional[int]


async def process_article(session: aiohttp.ClientSession, url: str, result_list: list[ProcessedArticle]):
    try:
        html = await fetch(session, url)
        sanitizer = SANITIZERS.get("inosmi_ru")
        plaintext = sanitizer(html, plaintext=True)
        morph = pymorphy2.MorphAnalyzer()
        article_words = split_by_words(morph, plaintext)
        rate = calculate_jaundice_rate(article_words, CHARGED_WORDS)
        result_list.append(ProcessedArticle(url, ProcessingStatus.OK, rate, len(article_words)))
    except aiohttp.ClientError:
        result_list.append(ProcessedArticle(url, ProcessingStatus.FETCH_ERROR, None, None))


async def main():
    TEST_ARTICLES = [
        "https://inosmi.ru/20221214/eneregetika-258837716.html",
        "https://inosmi.ru/20221214/kitay-258839981.html",
        "https://inosmi.ru/20221214/ultrapravye-258844791.html",
        "https://inosmi.ru/20221214/kitay-258839420.html",
        "https://inosmi.ru/20221214/katargeyt-258839069.html",
        "https://inosmi.ru/not/exist.html",
    ]

    async with aiohttp.ClientSession() as session:
        processed_articles: list[ProcessedArticle] = []

        async with anyio.create_task_group() as tg:
            for url in TEST_ARTICLES:
                tg.start_soon(process_article, session, url, processed_articles)

        for article in processed_articles:
            print(
                f"URL: {article.url}\n"
                f"Статус: {article.status.value}\n"
                f"Рейтинг: {article.rating}\n"
                f"Слов в статье: {article.words}\n"
            )


if __name__ == "__main__":
    asyncio.run(main())
