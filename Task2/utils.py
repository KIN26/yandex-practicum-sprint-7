from dto import HttpResponse

def is_retryable_status_code(response: HttpResponse):
    return response.status_code in [429, 500, 502, 503, 504]
