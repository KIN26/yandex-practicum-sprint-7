import asyncio
import json
import re
from typing import KeysView, Pattern
from dataclasses import dataclass, field
from pathlib import Path

import aiofiles

from settings import get_settings, AppSettings
from logger import logger


@dataclass(slots=True)
class Replacer:
    settings: AppSettings = field(default_factory=get_settings)

    async def get_map(self) -> dict[str, str]:
        async with aiofiles.open(self.settings.replacer.replace_map_file_path, mode="r", encoding="utf-8") as file:
            json_data = json.loads(await file.read())
        return json_data

    async def get_pattern(self, map_keys: KeysView[str]) -> Pattern[str]:
        patterns = sorted(map_keys, key=len, reverse=True)
        return re.compile('|'.join(map(re.escape, patterns)), re.IGNORECASE)

    async def run(self):
        json_map = await self.get_map()
        pattern = await self.get_pattern(json_map.keys())

        tasks = []
        folder = Path(self.settings.replacer.original_database_folder_path)
        for file in folder.rglob("*.txt"):
            tasks.append(self.fetch_file(json_map, pattern, file))

            if len(tasks) >= self.settings.replacer.concurrent_workers:
                await asyncio.gather(*tasks)
                tasks = []

        if tasks:
            await asyncio.gather(*tasks)

    async def fetch_file(self, replace_map: dict, pattern: Pattern[str], file_path: Path):
        logger.info("Start fetching file %s", file_path)
        def replacer(match):
            matched_text = match.group(0)
            if matched_text.lower() in replace_map:
                return replace_map[matched_text.lower()]
            return matched_text

        async with aiofiles.open(file_path, mode="r", encoding="utf-8") as file_to_read:
            text = await file_to_read.read()


        if file_path.stem in replace_map:
            file_name = replace_map[replace_map].replace(" ", "")
        else:
            file_name = "_".join([replace_map.get(w, w) for w in file_path.stem.lower().split("_")])

        new_file_path = Path(f"{self.settings.replacer.replaced_database_folder_path}/{file_name}.txt")
        result = pattern.sub(replacer, text)
        result = re.sub(r'\s+', ' ', result)
        result = re.sub(r'[^\w\sа-яА-ЯёЁ\-_.,!?;:]', ' ', result)

        logger.info("Create new replaced file %s", new_file_path)
        async with aiofiles.open(new_file_path, mode="w", encoding="utf-8") as file_to_write:
            await file_to_write.write(result.strip())


if __name__ == '__main__':
    asyncio.run(Replacer().run())