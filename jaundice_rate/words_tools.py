__all__ = ['CHARGED_WORDS']

import pathlib


def _read_words(path: pathlib.Path):
    with open(path, "r") as file:
        lines = file.readlines()
        return [line.rstrip("\n") for line in lines]


_path = pathlib.Path(__file__).parent

CHARGED_WORDS = [
    *_read_words(_path / "charged_words/negative_words.txt"),
    *_read_words(_path / "charged_words/positive_words.txt"),
]
