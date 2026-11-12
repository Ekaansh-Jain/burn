# Project shortlist

## 1. Faster local LLMs in Indian languages (shortlisted)

**One line:** speed up open models in Hindi, Tamil, Bengali, Telugu and Marathi by guessing the next few tokens from a dictionary-style lookup table, so the model verifies several tokens per step. No retraining, and output quality doesn't change.

**Why it matters**
- Indian languages need about 8x more tokens than English under GPT-4's tokenizer, up to 13x for Malayalam ([arXiv 2607.24276](https://arxiv.org/abs/2607.24276)). More tokens means slower, costlier replies.

**Evidence the technique works**
- DictSpec (2026) did this for Ukrainian and Crimean Tatar: up to 1.76x faster in live vLLM serving, with gains growing as tokens per word rise ([ACL Anthology](https://aclanthology.org/2026.unlp-1.15.pdf)).
- Small draft models work poorly for low-resource languages, while n-gram drafts still give speedups ([arXiv 2605.30580](https://arxiv.org/abs/2605.30580)).

**Gap:** DictSpec is a vLLM plugin for GPU servers, tested only on Ukrainian and Crimean Tatar. No Indian-language or laptop/phone version found as of Nov 2026.

**Fits the hardware:** M3 Mac, 16 GB. Small models (3B to 8B, 4-bit) run comfortably. llama.cpp already has n-gram lookup decoding to build on ([llama.cpp discussion](https://github.com/ggml-org/llama.cpp/discussions/4235)).

**4-week plan**
1. Week 1, baseline: run 2 small open models in llama.cpp; measure tokens per word and tokens/s in Hindi vs English.
2. Week 2, first speedup: build a lookup table from Hindi Wikipedia text; measure the gain with llama.cpp's n-gram lookup.
3. Week 3, smarter guesses: word-aware drafting (finish the current word from a dictionary); tables for Tamil, Bengali, Telugu, Marathi.
4. Week 4, release: publish tables, one-command setup, per-language benchmark table; share on r/LocalLLaMA; offer upstream to llama.cpp.

**Risks:** speedup unmeasured for Indian languages (could be 1.3x or 2.5x). Week 2 answers it cheaply.

## Parked

- **Fast local runtime for diffusion LLMs (DiffusionGemma).** Real gap: standard llama.cpp server can't run it yet, and it's slow on Apple Silicon ([llama.cpp issue #24529](https://github.com/ggml-org/llama.cpp/issues/24529)). Blocked on hardware: smallest download is 16 GB, and a 16 GB Mac gives the GPU about 12 GB. Revisit with a 32 GB+ Mac or a rented GPU.
