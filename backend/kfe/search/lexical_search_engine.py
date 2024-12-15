from collections import defaultdict
from typing import NamedTuple

from kfe.search.models import SearchResult
from kfe.search.reverse_index import ReverseIndex
from kfe.search.token_stat_counter import TokenStatCounter


class OkapiBM25Config(NamedTuple):
    k1: float = 1.5
    b: float = 0.75

class LexicalSearchEngine:
    def __init__(self, reverse_index: ReverseIndex, token_stat_counter: TokenStatCounter, bm25_config: OkapiBM25Config=None) -> None:
        self.reverse_index = reverse_index
        self.token_stat_counter = token_stat_counter
        self.bm25_config = bm25_config if bm25_config is not None else OkapiBM25Config()

    def search(self, lemmatized_tokens: list[str]) -> list[SearchResult]:
        ''' 
        Returns scores for each item that contained at least one of tokens from the query.
        Scores are sorted in decreasing order. Score function is BM25: https://en.wikipedia.org/wiki/Okapi_BM25
        '''
        if len(self.reverse_index) == 0 or not lemmatized_tokens:
            return []
        item_scores = defaultdict(lambda: 0.)
        k1, b = self.bm25_config
        avgdl = self.token_stat_counter.get_avg_item_length()

        for token in set(lemmatized_tokens):
            items_with_token = self.reverse_index.lookup(token)
            if not items_with_token:
                continue
            idf = self.token_stat_counter.idf(token)
            for item in items_with_token:
                freq = self.token_stat_counter.get_number_of_token_occurances_in_item(item)[token]
                dl = self.token_stat_counter.get_item_length(item)
                item_scores[item] += idf * (freq * (k1 + 1) / (freq + k1 * (1 - b + b *  dl / avgdl)))
        
        all_scores = [SearchResult(item_id=item_idx, score=score) for item_idx, score in item_scores.items()]
        all_scores.sort(key=lambda x: x.score, reverse=True)
        return all_scores
    
    def get_exact_match_score(self, lemmatized_tokens: list[str], num_additional_document_tokens: int=10,
            non_existent_token_contribution: float=1.) -> float:
        # imagine we had a single document with text exactly the same as query and also k additional tokens
        # this function is supposed to compute a score that such (query, document) pair would obtain
        score = 0.
        k1, b = self.bm25_config
        avgdl = self.token_stat_counter.get_avg_item_length()
        lemmatized_tokens = set(lemmatized_tokens)
        for token in lemmatized_tokens:
            items_with_token = self.reverse_index.lookup(token)
            if not items_with_token:
                score += non_existent_token_contribution
                continue
            idf = self.token_stat_counter.idf(token)
            freq = 1
            dl = len(lemmatized_tokens) + num_additional_document_tokens
            score += idf * (freq * (k1 + 1) / (freq + k1 * (1 - b + b *  dl / avgdl)))
        return score
