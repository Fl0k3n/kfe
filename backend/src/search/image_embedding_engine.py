import numpy as np
import torch
from PIL.Image import Image
from transformers import AutoImageProcessor, AutoModel


class ImageEmbeddingEngine:
    '''Returns normalized embeddings'''

    def __init__(self) -> None:
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        if not torch.cuda.is_available():
            print('cuda unavailable')
            
        self.processor = AutoImageProcessor.from_pretrained("google/vit-base-patch16-224")
        self.model = AutoModel.from_pretrained("google/vit-base-patch16-224").to(self.device)

    def generate_image_embedding(self, image: Image) -> np.ndarray:
        try:
            inputs = self.processor(image, return_tensors='pt').to(self.device)
            embedding: torch.Tensor = self.model(**inputs).pooler_output
            embedding = embedding / torch.linalg.norm(embedding)
            return embedding.detach().cpu().numpy().ravel()
        except Exception as e:
            print(e)
            raise e


    def generate_image_embeddings(self, images: list[Image]) -> list[np.ndarray]:
        return [self.generate_image_embedding(img) for img in images]
