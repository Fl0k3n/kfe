import re

_TOKENIZE_RE = re.compile(r"[\w'-]+")

def tokenize_text(text: str) -> list[str]:
    # this deliberately uses very simple tokenization method to be as close to 
    # input text as possible, more advanced tokenization with lemmatization is done separately
    return _TOKENIZE_RE.findall(text.lower())
