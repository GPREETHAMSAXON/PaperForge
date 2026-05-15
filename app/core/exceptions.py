from fastapi import HTTPException, status


class PaperForgeError(Exception):
    pass

class PaperFetchError(PaperForgeError):
    pass

class PaperParseError(PaperForgeError):
    pass

class PaperTooLargeError(PaperForgeError):
    pass

class InvalidArxivIdError(PaperForgeError):
    pass

class AnalysisError(PaperForgeError):
    pass

class ClaudeAPIError(PaperForgeError):
    pass


def http_not_found(detail: str) -> HTTPException:
    return HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=detail)

def http_bad_request(detail: str) -> HTTPException:
    return HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=detail)

def http_unprocessable(detail: str) -> HTTPException:
    return HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=detail)

def http_service_unavailable(detail: str) -> HTTPException:
    return HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=detail)

def http_payload_too_large(detail: str) -> HTTPException:
    return HTTPException(status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE, detail=detail)