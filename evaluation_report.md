# Evaluation Report

## Data Split

| metric | value |
|---|---|
| `train_files` | 30 |
| `test_files` | 16 |
| `train_block_signatures` | 293 |
| `test_block_cases` | 72 |
| `token_cases` | 24 |

## Block Prediction

### Model Signature Accuracy

| metric | value |
|---|---|
| `top_1` | 0.375 |
| `top_2` | 0.5139 |
| `top_3` | 0.5278 |
| `top_4` | 0.5417 |
| `top_5` | 0.5556 |

### Model Exact Text Accuracy

| metric | value |
|---|---|
| `top_1` | 0.1806 |
| `top_2` | 0.2361 |
| `top_3` | 0.25 |
| `top_4` | 0.2778 |
| `top_5` | 0.2778 |

### Template Baseline Signature Accuracy

| metric | value |
|---|---|
| `top_1` | 0.3056 |
| `top_2` | 0.3056 |
| `top_3` | 0.3056 |
| `top_4` | 0.3056 |
| `top_5` | 0.3056 |

## Token Completion

### Model Accuracy

| metric | value |
|---|---|
| `top_1` | 0.9583 |
| `top_2` | 1.0 |
| `top_3` | 1.0 |
| `top_4` | 1.0 |
| `top_5` | 1.0 |

### Prefix Baseline Accuracy

| metric | value |
|---|---|
| `top_1` | 0.5417 |
| `top_2` | 0.5417 |
| `top_3` | 0.5417 |
| `top_4` | 0.5417 |
| `top_5` | 0.5417 |

## Comments

- The model is competitive with the configured baselines on the evaluated sample.

## Limitations

- The system uses a lightweight heuristic/statistical approach rather than training a large language model.
- Embeddings are hashed TF-IDF vectors, not neural embeddings.
- The current implementation focuses on Python.
- Web integration is an IDE/autocomplete simulation, not a full IDE extension.
- Results depend on the size and relevance of the training corpus.
