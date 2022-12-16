import pymorphy2
import pytest

from jaundice_rate.text_tools import split_by_words, calculate_jaundice_rate


@pytest.fixture(scope="session")
def morph():
    return pymorphy2.MorphAnalyzer()


async def test_split_by_words(morph):
    assert await split_by_words(morph, 'Во-первых, он хочет, чтобы') == ['во-первых', 'хотеть', 'чтобы']
    assert await split_by_words(morph, '«Удивительно, но это стало началом!»') == ['удивительно', 'это', 'стать', 'начало']


def test_calculate_jaundice_rate():
    assert -0.01 < calculate_jaundice_rate([], []) < 0.01
    assert 33.0 < calculate_jaundice_rate(['все', 'аутсайдер', 'побег'], ['аутсайдер', 'банкротство']) < 34.0
