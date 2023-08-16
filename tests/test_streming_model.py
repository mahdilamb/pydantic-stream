from typing import List, Union

import pydantic
import pytest

import pydantic_stream
from pydantic_stream import exceptions


def simple_model_test(json_file):
    """Test that attrs can be accessed from a flat model."""

    class Model(pydantic.BaseModel):
        count: int
        results: List[str]

    model = pydantic_stream.stream_model(
        Model, json_file({"count": 3, "results": ["a", "b", "c"]})
    )

    assert (
        pydantic_stream.resolve(model.count) == 3
    ), "Expected to be able to resolve an int."
    assert (
        pydantic_stream.resolve(model.count) == 3
    ), "Expected to be able to resolve the same location, twice."
    assert pydantic_stream.resolve(model.results) == list(
        "abc"
    ), "Expected to be able to access `.results`."
    assert pydantic_stream.resolve(model).model_dump() == {
        "count": 3,
        "results": ["a", "b", "c"],
    }, "Expected to be able to decode the root."
    with pytest.raises(exceptions.NotSequenceError):
        model[0]


def nested_model_test(json_file):
    """Test that attrs can be accessed from a nested model."""

    class Results(pydantic.BaseModel):
        values: List[str]

    class NestedModel(pydantic.BaseModel):
        count: int
        results: Results

    model = pydantic_stream.stream_model(
        NestedModel, json_file({"count": 3, "results": {"values": ["a", "b", "c"]}})
    )
    assert pydantic_stream.resolve(model.count) == 3
    assert isinstance(pydantic_stream.resolve(model.results), Results)
    assert pydantic_stream.resolve(model.results.values) == list("abc")
    assert pydantic_stream.resolve(model.results.values[0]) == "a"
    with pytest.raises(exceptions.NotSequenceError):
        model.results[0]


def simple_alias_model_test(json_file):
    """Test that attrs can be accessed via aliases."""

    class AliasedModel(pydantic.BaseModel):
        count: int = pydantic.Field(alias="$count")
        results: List[str] = pydantic.Field(alias="$results")

    data = {"$count": 3, "$results": ["a", "b", "c"]}
    # Ensure the non-streamed version works
    AliasedModel.model_validate(data)
    model = pydantic_stream.stream_model(AliasedModel, json_file(data))
    assert pydantic_stream.resolve(model.count) == 3
    assert pydantic_stream.resolve(model.results) == list("abc")


def default_types_model_test(json_file):
    """Test that attrs can be accessed via aliases."""

    class AliasedModel(pydantic.BaseModel):
        count: int = pydantic.Field(alias="$count")
        results: List[str] = pydantic.Field(
            alias="$results", default_factory=lambda: list("abc")
        )

    data = {"$count": 3}
    # Ensure the non-streamed version works
    AliasedModel.model_validate(data)
    model = pydantic_stream.stream_model(AliasedModel, json_file(data))
    assert pydantic_stream.resolve(model.count) == 3
    assert pydantic_stream.resolve(model.results) == list("abc")


def multiple_cursors_work_test(json_file):
    """Test that cursors created in one sequence can be resolved in another."""

    class Model(pydantic.BaseModel):
        count: int
        results: List[str]

    model = pydantic_stream.stream_model(
        Model, json_file({"count": 3, "results": ["a", "b", "c"]})
    )
    a = model.count
    b = model.results
    assert pydantic_stream.resolve(b) == list("abc")
    assert pydantic_stream.resolve(a) == 3


def multiple_cursors_work_reversed_test(json_file):
    """Test that cursors created in one sequence can be resolved in another."""

    class Model(pydantic.BaseModel):
        count: int
        results: List[str]

    model = pydantic_stream.stream_model(
        Model, json_file({"count": 3, "results": ["a", "b", "c"]})
    )
    a = model.count
    b = model.results
    assert pydantic_stream.resolve(a) == 3
    assert pydantic_stream.resolve(b) == list("abc")


def union_types_test(json_file):
    """Test that union types are parsed correctly."""

    class A(pydantic.BaseModel):
        a: str

    class B(pydantic.BaseModel):
        b: int

    class Model(pydantic.BaseModel):
        values: List[Union[A, B]]

    model = pydantic_stream.stream_model(
        Model,
        json_file(
            {
                "values": [
                    {
                        "a": "hi",
                    },
                    {"b": 256},
                    {
                        "a": "bye",
                    },
                    {"b": 512},
                ]
            }
        ),
    )
    values = pydantic_stream.resolve(model.values)
    assert isinstance(values[0], A)
    assert isinstance(values[1], B)
    assert isinstance(values[2], A)


def union_types_list_test(json_file):
    class Model(pydantic.BaseModel):
        a: Union[List[str], int]

    model = pydantic_stream.stream_model(Model, json_file({"a": list("xyz")}))
    assert pydantic_stream.resolve(model.a[1]) == "y"


def nested_aliases_test(json_file):
    class A(pydantic.BaseModel):
        a: str = pydantic.Field(alias="$a")

    class B(pydantic.BaseModel):
        b: A = pydantic.Field(alias="$b")

    class C(pydantic.BaseModel):
        c: B = pydantic.Field(alias="$c")

    class Model(pydantic.BaseModel):
        root: C = pydantic.Field(alias="$root")

    model = pydantic_stream.stream_model(
        Model, json_file({"$root": {"$c": {"$b": {"$a": "heeeey"}}}})
    )
    assert pydantic_stream.resolve(model.root.c.b.a) == "heeeey"


if __name__ == "__main__":
    import sys

    sys.exit(pytest.main(["-v", "-s"] + sys.argv))
