import warnings
from typing import Iterator, Optional

import librosa
import numpy as np


def get_chunks(values: list, n: int) -> Iterator:
    """ 
    Yield successive n-sized chunks from values.

    Parameters:
    ----------
        values: list
            values to be chunked
       
        n: int
            chunk size

    Returns:
    ----------
        Iterator: A chunk iterator
    """

    for i in range(0, len(values), n):
        yield values[i:i + n]


def get_waveforms(pahts: list[str], sampling_rate: Optional[int] = 16000) -> list[np.ndarray]:
    """ 
    Get waveforms from audio files.

    Parameters:
    ----------
        pahts: list[str]
            paths to audio files
        
        sampling_rate: Optional[int] = 16000
            sampling rate of waveforms

    Returns:
    ----------
        list[np.ndarray]: waveforms from audio files
    """

    waveforms = []
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        for path in pahts:
            waveform, sr = librosa.load(path, sr=sampling_rate)
            waveforms.append(waveform)
    
    return waveforms
