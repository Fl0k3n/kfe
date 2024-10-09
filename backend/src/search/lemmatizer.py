import spacy


class Lemmatizer:
    def __init__(self, model='pl_core_news_lg') -> None:
        self.nlp = spacy.load(model, disable=['morphologizer', 'parser', 'senter', 'attribute_ruler', 'ner'])

    def lemmatize(self, text: str) -> list[str]:
        lemmatized = self.nlp(text)
        res = []
        for token_group in lemmatized:
            res.extend(token_group.lemma_.split())
        return res
