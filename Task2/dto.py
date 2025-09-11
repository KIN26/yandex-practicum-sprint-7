from dataclasses import dataclass

@dataclass(slots=True)
class HttpResponse:
    status_code: int
    content: str
