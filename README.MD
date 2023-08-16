# Pydantic stream

[![CI](https://github.com/mahdilamb/pydantic-stream/actions/workflows/code-quality-and-tests.yaml/badge.svg)](https://github.com/mahdilamb/pydantic-stream/actions/workflows/code-quality-and-tests.yaml)

Python package designed to enable lazy loading fo json files into pydantic modules. 


## Installation

You can either install for development using:
```shell
python -m pip install -e .[test]
```

Add to `pyproject.toml`:
```toml
...
dependencies = [
    "pydantic_stream@git+https://github.com/mahdilamb/pydantic-stream"
]
```
# Usage

To stream a json file do something like the follow:

```python
import pydantic

import pydantic_stream


class Model(pydantic.BaseModel):
    value: int


if __name__ == "__main__":
    with open("json_file.json", "r") as fp:
        model = pydantic_stream.stream_model(Model, fp)
        print(pydantic_stream.resolve(model))


```
