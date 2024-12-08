
from abc import ABC, abstractmethod
from typing import Callable

from search.models import SearchResult


class ConfidenceProvider(ABC):
    @abstractmethod
    def __call__(self, sr: SearchResult) -> float:
        pass

class LexicalConfidenceProvider(ConfidenceProvider):
    def __init__(self, approximate_exact_match_lexical_score: float):
        self.approximate_exact_match_lexical_score = approximate_exact_match_lexical_score

    def __call__(self, sr: SearchResult) -> float:
        return min(sr.score / self.approximate_exact_match_lexical_score, 1.)
    
class WideRangeSemanticConfidenceProvider(ConfidenceProvider):
    def __init__(self, low_relevance_threshold: float):
        self.low_relevance_threshold = low_relevance_threshold

    def __call__(self, sr: SearchResult) -> float:
        if sr.score < self.low_relevance_threshold:
            return max(0., sr.score / 2.)
        else:
            return min(1., max(0., 0.5 + (sr.score - self.low_relevance_threshold) * 2))

class NarrowRangeSemanticConfidenceProvider(ConfidenceProvider):
    def __init__(self, low_relevance_threshold: float, max_relevance: float):
        self.low_relevance_threshold = low_relevance_threshold
        self.max_relevance = max_relevance
        self.score_range = self.max_relevance - self.low_relevance_threshold

    def __call__(self, sr: SearchResult) -> float:
        if sr.score < self.low_relevance_threshold:
            return max(0., sr.score * 0.75)
        elif sr.score > self.max_relevance:
            return 1.
        else:
            return min(1., max(0., self.low_relevance_threshold + 1 - ((self.max_relevance - sr.score) / self.score_range)))

class HybridSearchConfidenceProviderFactory:
    def __init__(self, semantic_builder: Callable[[], ConfidenceProvider], clip_builder: Callable[[], ConfidenceProvider]=None):
        self.semantic_builder = semantic_builder
        self.clip_builder = clip_builder

    def get_lexical_confidence_provider(self, approximate_exact_match_lexical_score: float) -> ConfidenceProvider:
        return LexicalConfidenceProvider(approximate_exact_match_lexical_score)
    
    def get_semantic_confidence_provider(self) -> ConfidenceProvider:
        return self.semantic_builder()
    
    def get_clip_confidence_provider(self) -> ConfidenceProvider:
        return self.clip_builder()
