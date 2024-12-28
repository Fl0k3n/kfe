from collections import defaultdict
from typing import NamedTuple

from kfe.search.models import SearchResult
from kfe.search.reverse_index import ReverseIndex
from kfe.search.token_stat_counter import TokenStatCounter


class OkapiBM25Config(NamedTuple):
    k1: float = 1.5
    b: float = 0.75

class LexicalFieldStructures(NamedTuple):
    reverse_index: ReverseIndex
    token_stat_counter: TokenStatCounter
    field_weight: float

class LexicalFields(NamedTuple):
    original: LexicalFieldStructures
    lemmatized: LexicalFieldStructures

class LexicalTokens(NamedTuple):
    original: list[str]
    lemmatized: list[str]

    def as_token_dict(self) -> dict[str, list[str]]:
        return self._asdict()

class LexicalSearchEngine:

    def __init__(self, lexical_fields: LexicalFields, bm25_config: OkapiBM25Config=None) -> None:
        self.lexical_fields: dict[str, LexicalFieldStructures] = lexical_fields._asdict()
        self.bm25_config = bm25_config if bm25_config is not None else OkapiBM25Config()

    def search(self, lexical_tokens: LexicalTokens) -> list[SearchResult]:
        ''' 
        Returns scores for each item that contained at least one of tokens from the query.
        Scores are sorted in decreasing order. Score function is BM25: https://en.wikipedia.org/wiki/Okapi_BM25
        modified to handle multiple fields (original and lemmatized). It combines (with weighting) per-field
        bm25 scores. One of the reasons for that is lemmatization is context dependent and if word in user's query 
        gets lemmatized to something different than the same word in the document then it won't be found.
        '''
        item_scores = defaultdict(lambda: 0.)
        k1, b = self.bm25_config

        for field_name, tokens in lexical_tokens.as_token_dict().items():
            field_structures = self.lexical_fields[field_name]
            reverse_index, token_stat_counter = field_structures.reverse_index, field_structures.token_stat_counter
            field_weight = field_structures.field_weight

            if len(reverse_index) == 0 or not tokens:
                continue

            avgdl = token_stat_counter.get_avg_item_length()
            for token in set(tokens):
                items_with_token = reverse_index.lookup(token)
                if not items_with_token:
                    continue
                idf = token_stat_counter.idf(token)
                for item in items_with_token:
                    freq = token_stat_counter.get_number_of_token_occurances_in_item(item)[token]
                    dl = token_stat_counter.get_item_length(item)
                    item_scores[item] += field_weight * idf * (freq * (k1 + 1) / (freq + k1 * (1 - b + b *  dl / avgdl)))
        
        all_scores = [SearchResult(item_id=item_idx, score=score) for item_idx, score in item_scores.items()]
        all_scores.sort(key=lambda x: x.score, reverse=True)
        return all_scores
    
    def get_exact_match_score(self, lexical_tokens: LexicalTokens, num_additional_document_tokens: int=50,
            nonexistent_token_contribution: float=2.) -> float:
        # imagine we had a single document with text exactly the same as query and also k additional tokens
        # this function is supposed to compute a score that such (query, document) pair would obtain
        # additionaly, each token that was in lexical_tokens but not in any of documents should contribute
        # to score (we should penalize this type of search if there are many words that were not indexed)
        score = 0.
        k1, b = self.bm25_config

        for field_name, tokens in lexical_tokens.as_token_dict().items():
            field_structures = self.lexical_fields[field_name]
            reverse_index, token_stat_counter = field_structures.reverse_index, field_structures.token_stat_counter
            field_weight = field_structures.field_weight

            avgdl = token_stat_counter.get_avg_item_length()
            tokens = set(tokens)
            dl = len(tokens) + num_additional_document_tokens

            for token in tokens:
                items_with_token = reverse_index.lookup(token)
                if not items_with_token:
                    score += field_weight * nonexistent_token_contribution
                    continue
                idf = token_stat_counter.idf(token)
                freq = 1
                score += field_weight * idf * (freq * (k1 + 1) / (freq + k1 * (1 - b + b *  dl / avgdl)))

        return score
    
    def register_tokens(self, lexical_tokens: LexicalTokens, item_id: int):
        for field_name, tokens in lexical_tokens.as_token_dict().items():
            field_structures = self.lexical_fields[field_name]
            for token in tokens:
                field_structures.reverse_index.add_entry(token, item_id)
            field_structures.token_stat_counter.register(tokens, item_id)

    def unregister_tokens(self, lexical_tokens: LexicalTokens, item_id: int):
        for field_name, tokens in lexical_tokens.as_token_dict().items():
            field_structures = self.lexical_fields[field_name]
            for token in tokens:
                field_structures.reverse_index.remove_entry(token, item_id)
            field_structures.token_stat_counter.unregister(tokens, item_id)
