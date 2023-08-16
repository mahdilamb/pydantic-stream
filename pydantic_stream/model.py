"""Module containing the main functions for streaming a json file as pydantic models."""
import abc
import functools
import logging
import typing
from typing import (
    Any,
    Generic,
    Mapping,
    Optional,
    Sequence,
    TextIO,
    Tuple,
    Type,
    TypeVar,
    Union,
    cast,
)

import json_stream  # type: ignore
import json_stream.base  # type: ignore
import pydantic
import pydantic.fields
import pydantic_core

from pydantic_stream import exceptions

PydanticModel = TypeVar("PydanticModel", bound=Type[pydantic.BaseModel])
T = TypeVar("T")


class StreamedValue(abc.ABC, Generic[T]):
    """API for a streamed value."""

    @abc.abstractmethod
    def __stream_value__(self) -> T:
        """Get the value."""


def stream_model(
    cls: PydanticModel, fp: TextIO, allow_rewind: bool = True
) -> PydanticModel:
    """Stream a model as pydantic models.

    Parameters
    ----------
    cls : PydanticModel
        The pydantic model
    fp : TextIO
        The stream
    allow_rewind : bool, optional
        Whether to allow returning the file handle to the start of the stream, by default True

    Returns
    -------
    PydanticModel
        A copy of the input model, but with all the utilities for streaming.
    """

    def rewind(next_path, field_info):
        cursor = json_stream.load(fp)
        for path in next_path:
            cursor = cursor[path]
        return StreamedNode(cursor=cursor, path=next_path, field_info=field_info)

    class StreamedNode(StreamedValue):
        def __init__(
            self,
            cursor: Optional[json_stream.base.StreamingJSONBase],
            path: Tuple[Union[str, int], ...],
            field_info: Optional[pydantic.fields.FieldInfo],
        ) -> None:
            super().__init__()
            self.__cursor = cursor
            self.__path = path
            self.__field_info = field_info

        @typing.no_type_check
        def __getattr__(self, name: str):
            field_info = self.__field_info
            if field_info is None:
                if isinstance(name, int):
                    raise exceptions.NotSequenceError()
                field_info = cls.model_fields[name]
            elif isinstance(name, str):
                if isinstance(field_info.annotation, type) and issubclass(
                    field_info.annotation, pydantic.BaseModel
                ):
                    field_info = field_info.annotation.model_fields[name]
                elif hasattr(field_info.annotation, "__origin__") and issubclass(
                    field_info.annotation.__origin__, Mapping
                ):
                    field_info = pydantic.fields.FieldInfo.from_annotation(
                        field_info.annotation.__args__[1]
                    )
                else:
                    field_info = pydantic.fields.FieldInfo.from_annotation(
                        typing.get_type_hints(field_info.annotation)[name]
                    )
            else:
                if getattr(field_info.annotation, "__origin__", None) == Union:
                    field_info = field_info.from_annotation(
                        Union[
                            tuple(
                                arg_child
                                for arg in field_info.annotation.__args__
                                if hasattr(arg, "__origin__")
                                and issubclass(arg.__origin__, Sequence)
                                for arg_child in arg.__args__
                            )
                        ]
                    )
                    print(field_info)
                else:
                    if not hasattr(
                        field_info.annotation, "__origin__"
                    ) or not issubclass(field_info.annotation.__origin__, Sequence):
                        raise exceptions.NotSequenceError()
                    field_info = pydantic.fields.FieldInfo.from_annotation(
                        Union[field_info.annotation.__args__]
                    )
            if isinstance(name, str) and field_info.alias:
                name = field_info.alias
            next_path = self.__path + (name,)
            try:
                return StreamedNode(
                    cursor=self.__cursor[name], path=next_path, field_info=field_info
                )
            except json_stream.base.TransientAccessException as e:
                if allow_rewind:
                    cast(TextIO, fp).seek(0)
                    if (
                        field_info.default is not pydantic_core.PydanticUndefined
                        or field_info.default_factory is not None
                    ):
                        return StreamedNode(None, path=next_path, field_info=field_info)
                    return rewind(next_path, field_info)
                raise e

        @functools.lru_cache(1)
        def __stream_value__(self) -> Any:
            if self.__field_info is None:
                if allow_rewind:
                    cast(TextIO, fp).seek(0)
                return cls.model_validate(
                    json_stream.to_standard_types(json_stream.load(fp))
                )

            if self.__cursor is None:
                return self.__field_info.get_default(call_default_factory=True)
            return pydantic.RootModel[cast(Type, self.__field_info.annotation)](
                json_stream.to_standard_types(self.__cursor)
            ).root

        __getitem__ = __getattr__

    if allow_rewind and not fp.seekable():
        logging.getLogger().warning(
            "Attempting to allow_rewind on a stream that does not support it."
        )
        allow_rewind = False
    return cast(
        PydanticModel,
        StreamedNode(json_stream.load(fp), tuple(), field_info=None),
    )


def resolve(value: T) -> T:
    """Get the actual value from the cursor."""
    return cast(StreamedValue, value).__stream_value__()
