from typing import Annotated
from pydantic import Field

from typing import Annotated, Union
from pydantic import Field
from fastapi import UploadFile

ContextUrlType = Annotated[
    Union[str, UploadFile],
    Field(
        title='Context URLs',
        description='URLs to analyze. Can be: single URL, comma-separated URLs, CSV file, or TXT file',
        examples=[
            "https://example.com",
            "https://example1.com, https://example2.com",
            "example.csv",
            "example.txt",
        ]
    )
]
