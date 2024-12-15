from typing import Optional

import torch
from tqdm import tqdm
from transformers import AutoModelForCTC, Wav2Vec2Processor

from kfe.huggingsound.decoder import Decoder, GreedyDecoder
from kfe.huggingsound.token_set import TokenSet
from kfe.huggingsound.utils import get_chunks, get_waveforms


class SpeechRecognitionModel():
    """
    Speech Recognition Model.

    Parameters
    ----------
    letter_case: Optional[str] = None
        Case mode to be applied to the model's transcriptions. Can be 'lowercase', 'uppercase' 
        or None (None == keep the original letter case). Default is None.
    """

    def __init__(self, model: AutoModelForCTC, processor: Wav2Vec2Processor, device: torch.device, letter_case: Optional[str] = None):
        self.model = model 
        self.processor = processor
        self.device = str(device)
        self.letter_case = letter_case
        
        self.token_set = TokenSet.from_processor(self.processor, letter_case=self.letter_case)

        # changing the processor's tokens maps to match the token set
        # this is necessary to prevent letter case issues on fine-tuning
        self.processor.tokenizer.encoder = self.token_set.id_by_token
        self.processor.tokenizer.decoder = self.token_set.token_by_id

    def get_sampling_rate(self) -> int:
        return self.processor.feature_extractor.sampling_rate

    def transcribe(self, paths: list[str], batch_size: Optional[int] = 1, decoder: Optional[Decoder] = None) -> list[dict]:
        """ 
        Transcribe audio files.

        Parameters:
        ----------
            paths: list[str]
                List of paths to audio files to transcribe

            batch_size: Optional[int] = 1
                Batch size to use for inference

            decoder: Optional[Decoder] = None
                Decoder to use for transcription. If you don't specify this, the engine will use the GreedyDecoder.

        Returns:
        ----------
            list[dict]:
                A list of dictionaries containing the transcription for each audio file:

                [{
                    "transcription": str,
                    "start_timesteps": list[int],
                    "end_timesteps": list[int],
                    "probabilities": list[float]
                }, ...]
        """

        if decoder is None:
            decoder = GreedyDecoder(self.token_set)

        sampling_rate = self.get_sampling_rate()
        result = []

        for paths_batch in tqdm(list(get_chunks(paths, batch_size))):

            waveforms = get_waveforms(paths_batch, sampling_rate)

            inputs = self.processor(waveforms, sampling_rate=sampling_rate, return_tensors="pt", padding=True, do_normalize=True)

            with torch.no_grad():
                if hasattr(inputs, "attention_mask"):
                    logits = self.model(inputs.input_values.to(self.device),attention_mask=inputs.attention_mask.to(self.device)).logits
                else:
                    logits = self.model(inputs.input_values.to(self.device)).logits

            result += decoder(logits)

        return result 
