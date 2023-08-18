import urllib.request
from typing import Dict, List, Optional

import pydantic

import pydantic_stream


def sample_json_test():
    """Test loading json from a url."""

    class Question(pydantic.BaseModel):
        question: str
        options: List[str]
        answer: str

    class Questions(pydantic.BaseModel):
        q1: Question
        q2: Optional[Question] = None

    class Model(pydantic.BaseModel):
        quiz: Dict[str, Questions]

    url = "https://support.oneskyapp.com/hc/en-us/article_attachments/202761727/example_2.json"
    with urllib.request.urlopen(url) as response:
        model = pydantic_stream.stream_model(Model, response, allow_rewind=False)
        assert isinstance(pydantic_stream.resolve(model.quiz["sport"].q1), Question)


if __name__ == "__main__":
    import sys

    import pytest

    sys.exit(pytest.main(["-v", "-s"] + sys.argv))
