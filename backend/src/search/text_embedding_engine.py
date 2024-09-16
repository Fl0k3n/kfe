import numpy as np
import torch
from sentence_transformers import SentenceTransformer


class TextEmbeddingEngine:
    '''Returns normalized embeddings'''

    def __init__(self) -> None:
        device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        if not torch.cuda.is_available():
            print('cuda unavailable')
        self.model = SentenceTransformer('ipipan/silver-retriever-base-v1.1').to(device)
        self.query_prefix, self.passage_prefix = 'Pytanie: ', '</s>'

    def generate_query_embedding(self, text: str):
        return self.generate_query_embeddings([text])[0]

    def generate_query_embeddings(self, texts: list[str]):
        return self._generate([self.query_prefix + x for x in texts])

    def generate_passage_embedding(self, text: str) -> np.ndarray:
        return self.generate_passage_embeddings([text])[0]

    def generate_passage_embeddings(self, texts: list[str]):
        return self._generate([self.passage_prefix + x for x in texts])

    def _generate(self, texts: list[str]) -> list[np.ndarray]:
        embeddings = self.model.encode(texts)
        normalized = embeddings / np.linalg.norm(embeddings, axis=1, keepdims=True)
        return list(normalized)
