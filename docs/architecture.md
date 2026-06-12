# Architecture

## System Overview

```mermaid
flowchart TD
    A["Source code with <CURSOR>"] --> B["ContextAnalyzer"]
    B --> C["TokenPredictor"]
    B --> D["CodeBlockPredictor"]
    D --> E["Transition statistics"]
    D --> F["Lightweight vector embeddings"]
    D --> G["Template fallback"]
    C --> H["Token suggestions"]
    E --> I["Ranker"]
    F --> I
    G --> I
    I --> J["Block predictions"]
    H --> K["IDE integration simulation"]
    J --> K
```

## Prediction Pipeline

```mermaid
sequenceDiagram
    participant User
    participant Web as Web Demo
    participant API as Local API
    participant Analyzer as ContextAnalyzer
    participant Token as TokenPredictor
    participant Block as CodeBlockPredictor

    User->>Web: Insert code with <CURSOR>
    Web->>API: POST /predict
    API->>Analyzer: analyze(prefix)
    Analyzer-->>API: context features
    API->>Token: predict_from_context(context)
    Token-->>API: token suggestions
    API->>Block: predict_from_context(context)
    Block-->>API: ranked block predictions
    API-->>Web: context + token + block results
    Web-->>User: Show suggestions and reasons
```

## Evaluation Pipeline

```mermaid
flowchart LR
    A["examples/train"] --> B["Train model"]
    B --> C["model.json"]
    D["examples/test"] --> E["Collect held-out cases"]
    C --> F["Evaluate block prediction"]
    E --> F
    G["token_cases.json"] --> H["Evaluate token completion"]
    F --> I["evaluation_report.json"]
    H --> I
    I --> J["evaluation_report.md"]
```

## Main Signals Used By The Ranker

| Signal | Purpose |
|---|---|
| previous block signature | captures local code sequence |
| scope kind | separates module/function/class/loop contexts |
| token overlap | boosts candidates using same identifiers |
| lightweight embeddings | compares semantic similarity of code fragments |
| special context variables | boosts `result`, `total`, `count`, `self.*` cases |
| template fallback | handles incomplete IDE-style code |

## Notes

The project uses lightweight hashed TF-IDF vector embeddings. The architecture keeps this module isolated, so it can later be replaced with CodeBERT, CodeT5, or another HuggingFace model.
