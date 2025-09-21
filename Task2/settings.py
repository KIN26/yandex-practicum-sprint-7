from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import BaseModel


class HttpHeaders(BaseModel):
    user_agent: str = ("Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, "
                       "like Gecko) Version/18.4 Safari/605.1.15")


class Downloader(BaseModel):
    links_file_path: str = "./source.txt"
    database_folder_path: str = "./original_database"
    concurrent_workers: int = 3
    http_timeout: float = 5.0
    url_prefix: str = "https://starwars.fandom.com/ru/wiki/"
    url_suffix: str = "/Канон"
    http_headers: HttpHeaders = HttpHeaders()


class HtmlParser(BaseModel):
    content_class: str = "mw-parser-output"
    tags_to_clean: tuple[str] = (
        "script",
        "style",
        "nav",
        "footer",
        "aside",
        "header",
        "form",
        "iframe",
        "figure",
        "img",
        "figcaption",
        "dl",
        "dd",
    )
    css_classes_to_clean: tuple[str] = (
        "thumb",
        "image",
        "gallery",
        "mw-halign",
        "show-info-icon",
        "thumbcaption",
        "caption",
        "mw-file-description",
        "thumbimage",
        "lazyload",
        "mw-editsection",
        "toc",
        "quote",
        "BlockSpoiler2",
        "BlockStub",
    )
    article_chapter_to_clean: tuple[str] = (
        "Содержание",
        "Оглавление",
        "Примечания и сноски",
        "Источники", "Появления",
        "Появления в неканоничных медиа",
        "На других языках",
        "За кулисами",
        "Ссылки на внешние источники",
        "Ссылки и примечания",
        "Примечания",
        "Примечания и сноски",
        "Воплощение",
        "Исходная версия",
        "Имя",
        "Стили обращений",
        "Это статья-заготовка",
    )
    title_tags_to_clean: tuple[str] = ("h2", "h3", "h4", "h5", "h6")


class Replacer(BaseModel):
    replaced_database_folder_path: str = "./replaced_database"
    original_database_folder_path: str = "./original_database"
    replace_map_file_path: str = "./replace_map.json"
    concurrent_workers: int = 5


class AppSettings(BaseSettings):
    downloader: Downloader = Downloader()
    html_parser: HtmlParser = HtmlParser()
    replacer: Replacer = Replacer()

    model_config = SettingsConfigDict(env_nested_delimiter="__", env_file=".env", frozen=True, extra="ignore")


@lru_cache
def get_settings() -> AppSettings:
    return AppSettings()
