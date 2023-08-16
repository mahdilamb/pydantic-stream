"""Exceptions for pydantic-streamer."""


class NotSequenceError(IndexError):
    """Exception when accessing the index of a model that is not a sequence."""
