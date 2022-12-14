import bs4

DEFAULT_BLACKLIST_TAGS = frozenset([
    'script',
    'time'
])

DEFAULT_UNWRAPLIST_TAGS = frozenset([
    'div',
    'p',
    'span',
    'address',
    'article',
    'header',
    'footer'
])


def remove_buzz_attrs(soup: bs4.BeautifulSoup):
    """Remove all attributes except some special tags."""
    for tag in soup.find_all(True):
        if tag.name == 'a':
            tag.attrs = {
                'href': tag.attrs.get('href'),
            }
        elif tag.name == 'img':
            tag.attrs = {
                'src': tag.attrs.get('src'),
            }
        else:
            tag.attrs = {}

    return soup


def remove_buzz_tags(
        soup: bs4.BeautifulSoup,
        blacklist: set[str] = DEFAULT_BLACKLIST_TAGS,
        unwraplist: set[str] = DEFAULT_UNWRAPLIST_TAGS
):
    """Remove most of the tags, leaves only tags significant for text analysis."""
    for tag in soup.find_all(True):
        if tag.name in blacklist:
            tag.decompose()
        elif tag.name in unwraplist:
            tag.unwrap()


def remove_all_tags(soup: bs4.BeautifulSoup):
    """Unwrap all tags."""
    for tag in soup.find_all(True):
        tag.unwrap()
