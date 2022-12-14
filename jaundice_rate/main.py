import asyncio
from dataclasses import dataclass

import aiohttp
import anyio
import pymorphy2

from adapters import SANITIZERS
from text_tools import split_by_words, calculate_jaundice_rate


def read_words(filename: str):
    with open(filename, "r") as file:
        lines = file.readlines()
        return [line.rstrip("\n") for line in lines]


CHARGED_WORDS = read_words("negative_words.txt") + read_words("positive_words.txt")


async def fetch(session, url):
    async with session.get(url) as response:
        response.raise_for_status()
        return await response.text()


@dataclass
class ProcessedArticle:
    url: str
    rating: float
    words: int


async def process_article(session, url, result_list: list[ProcessedArticle]):
    html = await fetch(session, url)
    sanitizer = SANITIZERS.get("inosmi_ru")
    plaintext = sanitizer(html, plaintext=True)
    morph = pymorphy2.MorphAnalyzer()
    article_words = split_by_words(morph, plaintext)
    rate = calculate_jaundice_rate(article_words, CHARGED_WORDS)
    result_list.append(ProcessedArticle(url, rate, len(article_words)))


async def main():
    TEST_ARTICLES = [
        "https://inosmi.ru/20221214/eneregetika-258837716.html",
        "https://inosmi.ru/20221214/kitay-258839981.html",
        "https://inosmi.ru/20221214/ultrapravye-258844791.html",
        "https://inosmi.ru/20221214/kitay-258839420.html",
        "https://inosmi.ru/20221214/katargeyt-258839069.html"
    ]

    async with aiohttp.ClientSession() as session:
        processed_articles: list[ProcessedArticle] = []

        async with anyio.create_task_group() as tg:
            for url in TEST_ARTICLES:
                tg.start_soon(process_article, session, url, processed_articles)

        for article in processed_articles:
            print(f"URL: {article.url}\nРейтинг: {article.rating}%\nСлов в статье: {article.words}\n")


if __name__ == "__main__":
    asyncio.run(main())
