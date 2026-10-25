"""Character-level stand-in tokenizer with the GPT-2 call/decode interface (for offline tests only)."""
import torch


class ToyTok:
    eos_token_id = 0

    def __init__(self):
        self.vocab = {}

    def _id(self, ch):
        if ch not in self.vocab:
            self.vocab[ch] = len(self.vocab) + 1
        return self.vocab[ch]

    def __call__(self, text, add_special_tokens=False, return_tensors=None):
        ids = [self._id(c) for c in text]
        return {"input_ids": torch.tensor([ids]) if return_tensors == "pt" else ids}

    def decode(self, ids):
        inv = {v: k for k, v in self.vocab.items()}
        return "".join(inv.get(int(i), "?") for i in ids)
