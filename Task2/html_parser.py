import re
from dataclasses import dataclass, field

from bs4 import BeautifulSoup

from settings import get_settings, AppSettings


@dataclass(slots=True)
class HtmlParser:
    settings: AppSettings = field(default_factory=get_settings)

    def parse(self, html: str):
        soup = BeautifulSoup(html, "html.parser")
        content_div = soup.find("div", {"class": "mw-parser-output"})

        for element in content_div.find_all(self.settings.html_parser.tags_to_clean):
            element.decompose()

        for css_class in self.settings.html_parser.css_classes_to_clean:
            for element in content_div.find_all(class_=css_class):
                element.decompose()

        for element in content_div.find_all(self.settings.html_parser.title_tags_to_clean):
            element_text = element.get_text(strip=True)
            element_text = re.sub(r'\[\]$', '', element_text)

            if element_text in self.settings.html_parser.article_chapter_to_clean:
                to_remove = element

                while to_remove:
                    next_element = to_remove.next_sibling
                    to_remove.decompose()
                    to_remove = next_element

                    if isinstance(to_remove, str) and not to_remove.strip():
                        to_remove = to_remove.next_sibling
                        continue

                    if getattr(to_remove, "name", None) in self.settings.html_parser.title_tags_to_clean:
                        break

        for link in content_div.find_all('a', href=True):
            if bool(re.match(r'^\[\d+\]$', link.get_text(strip=True))):
                link.decompose()
            else:
                link.replace_with(link.get_text())

        ret = content_div.get_text()
        ret = re.sub(r"\(англ\.\s*[^)]+\)", "", ret)
        ret = re.sub(r"\n+", "\n", ret)
        return ret.replace(r" —", "").lower()
