from spacy import Vocab
from spacy.tokenizer import Tokenizer


class Tokenizer:
    def __init__(self, vocab: Vocab) -> None:
        self.tokenizer = Tokenizer(vocab)

    def tokenize(self, text: str) -> list[str]:
        return [str(x).lower() for x in self.tokenizer(text)]
