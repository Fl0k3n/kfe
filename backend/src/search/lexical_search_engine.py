from collections import defaultdict
from typing import NamedTuple

from features.lemmatizer import Lemmatizer
from search.models import SearchResult
from search.reverse_index import ReverseIndex
from search.token_stat_counter import TokenStatCounter


class OkapiBM25Config(NamedTuple):
    k1: float = 1.5
    b: float = 0.75

class LexicalSearchEngine:
    def __init__(self, lemmatizer: Lemmatizer, reverse_index: ReverseIndex, token_stat_counter: TokenStatCounter, bm25_config: OkapiBM25Config=None) -> None:
        self.lemmatizer = lemmatizer
        self.reverse_index = reverse_index
        self.token_stat_counter = token_stat_counter
        self.bm25_config = bm25_config if bm25_config is not None else OkapiBM25Config()

    async def search(self, query: str) -> list[SearchResult]:
        ''' 
        Returns scores for each item that contained at least one of tokens from the query.
        Scores are sorted in decreasing order. Score function is BM25: https://en.wikipedia.org/wiki/Okapi_BM25
        '''
        if len(self.reverse_index) == 0:
            return []
        async with self.lemmatizer.run() as engine:
            lemmatized_tokens = await engine.lemmatize(query)
        item_scores = defaultdict(lambda: 0.)
        k1, b = self.bm25_config
        num_items = self.token_stat_counter.get_number_of_items()
        avgdl = self.token_stat_counter.get_avg_item_length()

        for token in set(lemmatized_tokens):
            items_with_token = self.reverse_index.lookup(token)
            if not items_with_token:
                continue
            idf = self.token_stat_counter.idf(token)
            for item in items_with_token:
                freq = self.token_stat_counter.get_number_of_token_occurances_in_item(item)[token]
                item_scores[item] += idf * (freq * (k1 + 1) / (freq + k1 * (1 - b + b * num_items / avgdl)))
        
        all_scores = [SearchResult(item_id=item_idx, score=score) for item_idx, score in item_scores.items()]
        all_scores.sort(key=lambda x: x.score, reverse=True)
        return all_scores
