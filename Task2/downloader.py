import asyncio
import re
from dataclasses import dataclass, field

import aiofiles
from aiohttp import ClientSession, TCPConnector, ClientTimeout
from aiohttp.web_exceptions import HTTPClientError, HTTPRequestTimeout
from bs4 import BeautifulSoup
from tenacity import (
    retry,
    retry_if_exception_type,
    retry_if_result,
    stop_after_attempt,
    wait_fixed,
)

from dto import HttpResponse
from html_parser import HtmlParser
from logger import logger
from settings import get_settings, AppSettings
from utils import is_retryable_status_code

@dataclass(slots=True)
class Downloader:
    settings: AppSettings = field(default_factory=get_settings)
    session: ClientSession = field(init=False)
    loop: asyncio.AbstractEventLoop = field(init=False)
    queue: asyncio.Queue = field(init=False)
    html_parser: HtmlParser = field(init=False)


    def __post_init__(self):
        self.loop = asyncio.get_event_loop()
        self.html_parser = HtmlParser()
        self.queue = asyncio.Queue()
        self.session = ClientSession(
            timeout=ClientTimeout(total=self.settings.downloader.http_timeout),
            loop=self.loop,
            connector=TCPConnector(limit=self.settings.downloader.concurrent_workers),
            headers={
                "User-Agent": self.settings.downloader.http_headers.user_agent,
            },
        )

    async def __aenter__(self):
        logger.info("Start downloading...")
        return self

    async def __aexit__(self, *_):
        logger.info("Shutting down")
        await self.session.close()


    async def download(self):
        async with asyncio.TaskGroup() as tg:
            tg.create_task(self.producer())
            tg.create_task(self.consumer())


    async def producer(self):
        batch = []

        async with aiofiles.open(self.settings.downloader.links_file_path) as f:
            async for line in f:
                batch.append(line.strip())

                if len(batch) >= self.settings.downloader.concurrent_workers:
                    await self.queue.put(batch)
                    batch = []

        if batch:
            await self.queue.put(batch)

        await self.queue.put(None)

    @retry(
        retry=(
            retry_if_exception_type((HTTPRequestTimeout, HTTPClientError, asyncio.TimeoutError))
            | retry_if_result(is_retryable_status_code)
        ),
        stop=stop_after_attempt(3),
        wait=wait_fixed(1),
        reraise=True,
    )
    async def request(self, url) -> HttpResponse:
        logger.info("Downloading article from url %s", url)
        async with self.session.get(url) as response:
            content = await response.text()
            status_code = response.status
        await asyncio.sleep(0.1)
        return HttpResponse(status_code=status_code, content=content)

    async def save_content_into_file(self, file_name: str, content: str):
        logger.info("Save article content into %s/%s.txt", self.settings.downloader.database_folder_path, file_name)
        parsed_content = self.html_parser.parse(content)
        async with aiofiles.open(f"{self.settings.downloader.database_folder_path}/{file_name}.txt", "w") as f:
            await f.write(parsed_content)

    def get_article_name_from_url(self, url: str) -> str:
        return url.replace(self.settings.downloader.url_prefix, "").replace(self.settings.downloader.url_suffix, "")

    async def consumer(self):
        while True:
            urls_batch = await self.queue.get()

            if urls_batch is None:
                break

            article_contents = await asyncio.gather(*[self.request(url) for url in urls_batch])
            await asyncio.gather(
                *[
                    self.save_content_into_file(
                        self.get_article_name_from_url(url),
                        article_contents[i].content,
                    )
                    for i, url in enumerate(urls_batch)
                ]
            )

    @classmethod
    async def run(cls):
        async with cls() as ctx:
            await ctx.download()



if __name__ == '__main__':
    asyncio.run(Downloader.run())

