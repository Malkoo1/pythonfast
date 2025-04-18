class InvalidFileTypeError(Exception):
    """Raised when an unsupported file type is provided"""

    pass


class AudioExtractionError(Exception):
    """Raised when audio extraction fails"""

    pass


class InvalidVideoURLError(Exception):
    """Raised when an invalid video URL is provided"""

    pass
