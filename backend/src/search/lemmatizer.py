import spacy


class Lemmatizer:
    def __init__(self, model='pl_core_news_lg') -> None:
        self.nlp = spacy.load(model, disable=['morphologizer', 'parser', 'senter', 'attribute_ruler', 'ner'])

    def lemmatize(self, text: str) -> list[str]:
        lemmatized = self.nlp(text)
        return [token.lemma_ for token in lemmatized]
