__all__ = ['CHARGED_WORDS']

from pathlib import Path


def _read_words(path: Path):
    with open(path, "r") as file:
        words = file.readlines()
        return [word.rstrip("\n") for word in words]


_module_path = Path(__file__).parent

CHARGED_WORDS = [
    *_read_words(_module_path / "charged_words/negative_words.txt"),
    *_read_words(_module_path / "charged_words/positive_words.txt"),
]
