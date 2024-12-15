from typing import Literal

import numpy as np

from kfe.search.models import SearchResult
from kfe.utils.hybrid_search_confidence_providers import ConfidenceProvider


def combine_results_with_rescoring(all_results: list[list[SearchResult]], weights: list[float], method: Literal['sum', 'max']='max') -> list[SearchResult]:
    # meant for results from the same retriever (with scores from the same domain)
    assert len(all_results) == len(weights) and np.isclose(np.sum(weights), 1)
    score_by_id: dict[int, float] = {}
    if method == 'sum':
        for dim_results, weight in zip(all_results, weights):
            for sr in dim_results:
                score_by_id[sr.item_id] = score_by_id.get(sr.item_id, 0.) + sr.score * weight
    else:
        max_weighted_score_with_original_by_id: dict[int, tuple[float, float]] = {}
        for dim_results, weight in zip(all_results, weights):
            for sr in dim_results:
                current_results = max_weighted_score_with_original_by_id.get(sr.item_id)
                weighted_score = sr.score * weight
                if current_results is None or current_results[0] < weighted_score:
                    max_weighted_score_with_original_by_id[sr.item_id] = (weighted_score, sr.score)
        for item_id, (_, original_score) in max_weighted_score_with_original_by_id.items():
            score_by_id[item_id] = original_score
                
    res = [SearchResult(item_id=item_id, score=score) for item_id, score in score_by_id.items()]
    res.sort(key=lambda x: x.score, reverse=True)
    return res

def reciprocal_rank_fusion(all_results: list[list[SearchResult]], weights: list[float]=None, rrf_k_constant: float=60.) -> list[SearchResult]:
    # each list in all_results must be sorted according to the score assigned by a retriever, with most relevant item first
    # https://plg.uwaterloo.ca/~gvcormac/cormacksigir09-rrf.pdf
    if len(all_results) == 1:
        return all_results[0]
    if weights is None:
        weights = [1.] * len(all_results)
    assert len(all_results) == len(weights)
    score_by_id: dict[int, float] = {}
    for retriever_results, weight in zip(all_results, weights):
        for rank, sr in enumerate(retriever_results, start=1):
            partial_rrf_score = weight / (rrf_k_constant + rank)
            score_by_id[sr.item_id] = score_by_id.get(sr.item_id, 0.) + partial_rrf_score
    res = [SearchResult(item_id=item_id, score=score) for item_id, score in score_by_id.items()]
    res.sort(key=lambda x: x.score, reverse=True)
    return res

def confidence_accounting_rrf(all_results: list[list[SearchResult]], confidence_providers: list[ConfidenceProvider], 
        weights: list[float]=None, rrf_k_constant: float=60.) -> list[SearchResult]:
    # the problem with this multimedia use case is that different retrievers may consider different types of information
    # e.g. clip ignores audio altogether, and lex/semantic ignore visual aspects. Thus if clip gives a very high score for some file
    # but both lex and semantic assign a low score the file will be lost at the end of the rank, even though it's very relevant.
    # This function tries to account for these problems by considering retriever-specific scores. The role of confidence provider
    # is to return a number between (0, 1) that describes how confident a given retriever is about the relevance of an item.
    if len(all_results) == 1:
        return all_results[0]
    if weights is None:
        weights = [1.] * len(all_results)
    assert len(all_results) == len(weights)
    score_by_id: dict[int, float] = {}
    for retriever_results, confidence_provider, weight in zip(all_results, confidence_providers, weights):
        for rank, sr in enumerate(retriever_results, start=1):
            partial_rrf_score = confidence_provider(sr) * weight / (rrf_k_constant + rank)
            score_by_id[sr.item_id] = score_by_id.get(sr.item_id, 0.) + partial_rrf_score
    res = [SearchResult(item_id=item_id, score=score) for item_id, score in score_by_id.items()]
    res.sort(key=lambda x: x.score, reverse=True)
    return res
