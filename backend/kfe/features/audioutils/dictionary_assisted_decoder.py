import numpy as np
import torch

from kfe.huggingsound.decoder import Decoder
from kfe.huggingsound.token_set import TokenSet
from kfe.utils.datastructures.bktree import BKTree
from kfe.utils.datastructures.trie import Trie


class DictionaryAssistedDecoder(Decoder):
    def __init__(self, token_set: TokenSet, dictionary: Trie, edit_distance_search_tree: BKTree, disctionary_token_id_lut: dict[str, int],
                 average_word_length=8, max_correction_alternatives_with_dist_above_1=20):
        super().__init__(token_set)
        self.dictionary = dictionary
        self.edit_distance_search_tree = edit_distance_search_tree
        self.disctionary_token_id_lut = disctionary_token_id_lut
        self.max_correction_alternatives_with_dist_above_1 = max_correction_alternatives_with_dist_above_1
        self.best_configuration_compute_buff = np.zeros((4 * average_word_length + 1, average_word_length*20), dtype=np.float32)

    def _get_predictions(self, logits: torch.Tensor):
        assert logits.shape[0] == 1
        logits = logits[0, ...]
        predicted_ids = []
        N = logits.shape[0]
        probs = torch.nn.functional.softmax(logits, dim=-1)
        log_probs = torch.log(probs).detach().cpu().numpy()
        tokens_sorted_by_prob = probs.argsort(dim=-1, descending=True).detach().cpu().numpy()
        probs = probs.detach().cpu().numpy()
        word_start = 0
        previous_word = None
        while word_start < N:
            i = word_start
            word_decoding_state: list[int] = []
            while i < N:
                most_likely_token = tokens_sorted_by_prob[i, 0]
                prob = probs[i, most_likely_token]
                if len(word_decoding_state) == 0 and (most_likely_token == self.token_set.blank_token_id or
                                                      most_likely_token == self.token_set.silence_token_id):
                    word_start += 1
                    break
                if most_likely_token == self.token_set.blank_token_id and i < N - 1:
                    i += 1
                    continue
                if most_likely_token == self.token_set.silence_token_id or i == N - 1:
                    word = self._join_word(word_decoding_state)
                    word_exists, existing_prefix_size, last_node = self.dictionary.search(self._convert_to_dictionary_tokens(word_decoding_state))
                    if word_exists:
                        # greedily accept word
                        word_start, previous_word = self._accept(predicted_ids, word_decoding_state, i)
                        break
                    elif previous_word is not None:
                        combined_word = previous_word + word_decoding_state
                        if self.dictionary.has(self._convert_to_dictionary_tokens(combined_word)):
                            predicted_ids.pop()
                            word_start, previous_word = self._accept(predicted_ids, word_decoding_state, i)
                            break
                    if i < N - 1 and prob < 0.6 and existing_prefix_size == len(word): 
                        # maybe this isn't the end of word, lookup trie if we have some options and check if after this blank there is likely some letter
                        should_continue_with_word = False
                        if possible_next_tokens := self._convert_from_dictionary_tokens(self.dictionary.get_possible_next_tokens(last_node)):
                            LOOK_AHEAD = 20
                            for k in range(i, min(i+LOOK_AHEAD, N)):
                                most_probable_existing_token = possible_next_tokens[0]
                                for token in possible_next_tokens[1:]:
                                    if probs[k, token] > probs[k, most_probable_existing_token]:
                                        most_probable_existing_token = token
                                if probs[k, most_probable_existing_token] > 0.25:
                                    word_decoding_state.append(most_probable_existing_token)
                                    i = k + 1
                                    should_continue_with_word = True
                                    break
                        if should_continue_with_word:
                            continue

                    # try splitting into two words and correct them separately                        
                    best_split, split_best_log_prob = self._split_word_and_attempt_correcting(
                        word_decoding_state, log_probs, word_start, i-1)

                    # find existing word with small levenshtein distance and highest probability
                    whole_best_alternative_tokens, whole_best_log_prob = self._correct_word(
                        log_probs, word, word_start, i-1, max_dist=1 if len(word) <= 3 else 2)
                    
                    if whole_best_alternative_tokens is None and best_split is None:
                        self._accept(predicted_ids, word_decoding_state, i)
                        word_start, previous_word = self._accept(predicted_ids, whole_best_alternative_tokens, i)
                    else:
                        if split_best_log_prob is not None and (whole_best_log_prob is None or split_best_log_prob > whole_best_log_prob):
                            self._accept(predicted_ids, best_split[0], i)
                            word_start, previous_word = self._accept(predicted_ids, best_split[1], i)
                        else:
                            word_start, previous_word = self._accept(predicted_ids, whole_best_alternative_tokens, i)
                    break
                            
                if len(word_decoding_state) == 0 or most_likely_token != tokens_sorted_by_prob[i-1, 0]:
                    word_decoding_state.append(most_likely_token)
                i += 1

        predictions = self._ctc_decode([predicted_ids])

        return predictions
    
    def _split_word_and_attempt_correcting(self, word_decoding_state: list[int],
            log_probs: np.ndarray, word_start: int, word_end: int) -> tuple[tuple[list[int], list[int]] | None, float]:
        if len(word_decoding_state) < 3:
            return None, -np.inf

        best_split, best_log_prob = None, None

        for split_pos in range(2, len(word_decoding_state) - 2):
            first_tokens, second_tokens = word_decoding_state[:split_pos], word_decoding_state[split_pos:]
            first_needs_correction, second_needs_correction = False, False
            if not self.dictionary.has(self._convert_to_dictionary_tokens(first_tokens)):
                first_needs_correction = True
            if not self.dictionary.has(self._convert_to_dictionary_tokens(second_tokens)):
                second_needs_correction = True

            partial_log_prob = 0.
            if first_needs_correction:
                first_tokens, lp = self._correct_word(log_probs, self._join_word(first_tokens), word_start, word_start + split_pos - 1, max_dist=1) 
                if lp is None:
                    continue
                partial_log_prob += lp
            else:
                partial_log_prob += self._get_log_probability_of_best_configuration(log_probs, first_tokens, word_start, word_start + split_pos - 1)
            
            if second_needs_correction:
                second_tokens, lp = self._correct_word(log_probs, self._join_word(second_tokens), word_start + split_pos, word_end, max_dist=1) 
                if lp is None:
                    continue
                partial_log_prob += lp
            else:
                partial_log_prob += self._get_log_probability_of_best_configuration(log_probs, first_tokens, word_start + split_pos, word_end)
            
            if best_log_prob is None or partial_log_prob > best_log_prob:
                best_split, best_log_prob = (first_tokens, second_tokens), partial_log_prob

        return best_split, best_log_prob
    
    def _correct_word(self, log_probs: np.ndarray, word: str, start_idx: int, end_idx: int, max_dist: int) -> tuple[list[int] | None, float | None]:
        best_alternative_tokens, best_log_prob = None, None
        for dist in range(1, max_dist + 1):
            search_limit = None if dist == 1 else self.max_correction_alternatives_with_dist_above_1
            evaluated = 0
            for alternative in self.edit_distance_search_tree.search(word, max_distance=dist):
                if alternative[1] != dist:
                    continue
                evaluated += 1
                if search_limit is not None and evaluated >= search_limit:
                    break
                
                alternative_tokens = self._tokenize_word(alternative[0])
                lp = self._get_log_probability_of_best_configuration(log_probs, alternative_tokens, start_idx, end_idx)
                if best_log_prob is None or lp > best_log_prob:
                    best_alternative_tokens, best_log_prob = alternative_tokens, lp

        return best_alternative_tokens, best_log_prob

    def _get_log_probability_of_best_configuration(self, log_probs: np.ndarray, tokens: list[int], start_idx: int, end_idx: int) -> float:
        N = end_idx - start_idx + 1
        if len(tokens) > N:
            return -np.inf

        if self.best_configuration_compute_buff.shape[0] >= len(tokens) + 1 and self.best_configuration_compute_buff.shape[1] >= N + 1:
            F = self.best_configuration_compute_buff
        else:
            F = np.zeros((len(tokens) + 1, N + 1), dtype=np.float32)

        for i in range(1, N+1):
            F[0, i] = F[0, i-1] + log_probs[start_idx + i - 1, self.token_set.blank_token_id]

        for i in range(1, len(tokens) + 1):
            for j in range(i, N + 1):
                take_cur_lp = log_probs[start_idx + j - 1, tokens[i - 1]]
                blank_lp = log_probs[start_idx + j - 1, self.token_set.blank_token_id]
                if i == j:
                    F[i, j] = F[i-1, j-1] + take_cur_lp
                else:
                    F[i, j] = max(F[i, j-1] + blank_lp, F[i-1, j-1] + take_cur_lp)
        
        return F[len(tokens), N]
    
    def _accept(self, predicted_ids: list[int], token_ids: list[int], i: int) -> tuple[int, list[int]]:
        if token_ids:
            edited_token_ids = [token_ids[0]]
            for token in token_ids[1:]:
                if token == edited_token_ids[-1]:
                    # ctc decoding filters same consecutive tokens that are not separated by blank
                    edited_token_ids.append(self.token_set.blank_token_id)
                edited_token_ids.append(token)
            predicted_ids.extend(edited_token_ids)
        predicted_ids.append(self.token_set.silence_token_id)
        return i + 1, token_ids
    
    def _tokenize_word(self, word: str) -> list[int]:
        return [self.token_set.id_by_token[x] for x in word]
    
    def _convert_to_dictionary_tokens(self, token_ids: list[int]) -> list[int]:
        return [x - len(self.token_set.special_tokens) for x in token_ids]
    
    def _convert_from_dictionary_tokens(self, token_ids: list[int]) -> list[int]:
        return [x + len(self.token_set.special_tokens) for x in token_ids]
    
    def _join_word(self, token_ids: list[int]) -> str:
        return ''.join([self.token_set.tokens[x] for x in token_ids])
