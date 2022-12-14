__all__ = ['CHARGED_WORDS']


def _read_words(filename: str):
    with open(filename, "r") as file:
        lines = file.readlines()
        return [line.rstrip("\n") for line in lines]


CHARGED_WORDS = [
    *_read_words("charged_words/negative_words.txt"),
    *_read_words("charged_words/positive_words.txt"),
]
