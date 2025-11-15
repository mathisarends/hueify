from pathlib import Path
from typing import Protocol


class PromptFileReader(Protocol):
    def read_prompt_file(self) -> str: ...


class FileSystemPromptReader:
    def __init__(self, file_path: str) -> None:
        self._file_path = Path(file_path)

    def read_prompt_file(self) -> str:
        return self._file_path.read_text(encoding="utf-8")
