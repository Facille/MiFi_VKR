# Code Context Predictor

Проект для ВКР по теме:

> Методика анализа контекста программного кода и предсказания следующего блока для интеллектуальных систем автодополнения.

Это не чат-бот и не обертка над GPT. Проект имитирует модуль автодополнения IDE: анализирует код перед курсором `<CURSOR>` и предлагает продолжение на двух уровнях.

## Два уровня автодополнения

**Token-level autocomplete** предсказывает текущий недописанный токен:

```text
pri -> print
ret -> return
imp -> import
num -> numbers
cal -> calculate_sum
```

**Block-level prediction** предсказывает следующий блок кода на основе контекста:

```python
def clean_names(names):
    result = []
    for name in names:
        result.append(name.strip().lower())
    <CURSOR>
```

Ожидаемый вариант:

```python
return result
```

## Архитектура

```text
code_context_predictor/
  context_analyzer.py  -> публичный модуль анализа контекста
  analyzer.py          -> AST, tokens, scope, indentation, incomplete code
  tokenizer.py         -> token utilities
  token_predictor.py   -> token-level autocomplete
  block_predictor.py   -> публичный модуль block prediction
  model.py             -> обучаемая статистическая block model
  embeddings.py        -> lightweight vector embeddings, hashed TF-IDF
  baselines.py         -> prefix/template baselines
  evaluation.py        -> train/test evaluation
  evaluator.py         -> публичный evaluator API
  reports.py           -> Markdown report generation
  api.py               -> local API and web demo
  web/index.html       -> IDE integration simulation
```

## Что извлекает анализатор контекста

- imports;
- функции;
- классы;
- переменные;
- аргументы функций;
- последнюю активную конструкцию;
- глубину вложенности;
- текущий префикс токена;
- ближайший родительский блок;
- область видимости;
- последние сигнатуры блоков;
- отступ и признак открытого блока.

Незавершенный код обрабатывается best-effort способом: `def`, `if`, `for`, `while`, `try` и частично введенные токены не должны ломать анализатор.

## Запуск в cmd через `py`

```bat
cd /d E:\Intel_ai_project
set "PYTHONPATH=%cd%\src"
```

Тесты:

```bat
py -m unittest discover -s tests
```

Демо:

```bat
py -m code_context_predictor.cli demo
```

Обучение:

```bat
py -m code_context_predictor.cli train --input examples\train --model model.json
```

Token autocomplete:

```bat
py -m code_context_predictor.cli complete-token --file examples\token_snippet.py --top-k 5
```

Block prediction:

```bat
py -m code_context_predictor.cli predict --model model.json --file examples\incomplete_snippet.py --top-k 5
```

Evaluation с честным train/test split:

```bat
py -m code_context_predictor.cli evaluate --train examples\train --test examples\test --model model.json --top-k 5 --token-cases examples\token_cases.json --report evaluation_report.json --markdown-report evaluation_report.md
```

Web demo:

```bat
py -m code_context_predictor.cli serve --model model.json --port 8765
```

Открыть:

```text
http://127.0.0.1:8765
```

## Evaluation

Текущий учебный прогон:

- train files: `30`;
- test files: `16`;
- train block signatures: `293`;
- test block cases: `72`;
- token cases: `24`.

Результаты после последнего прогона:

```text
block model top-1 signature accuracy: 0.3750
block model top-5 signature accuracy: 0.5556
block template baseline top-1/top-5: 0.3056
token model top-1 accuracy: 0.9583
token model top-5 accuracy: 1.0
token prefix baseline top-1/top-5: 0.5417
```

Отчеты:

- `evaluation_report.json`;
- `evaluation_report.md`.

## Embeddings

В проекте используются lightweight vector embeddings на основе hashed TF-IDF. Это не нейросетевая модель, но это честное векторное представление кода, которое используется как дополнительный сигнал ранжирования.

Архитектура позволяет позже заменить `embeddings.py` на CodeBERT, CodeT5 или HuggingFace-модель без переписывания всего проекта.

## Baselines

Token baseline:

- generic prefix match по ключевым словам Python и builtins.

Block baseline:

- простые синтаксические шаблоны для `def`, `class`, `if`, `for`, `while`, `try`, `with`.

Если baseline оказывается сильнее основной модели, evaluation report выводит это честно в `comments`.

## Limitations

- система не обучает большую языковую модель;
- используется lightweight heuristic/statistical approach;
- основной язык — Python;
- web demo является IDE integration simulation, а не полноценной IDE;
- embeddings являются легким TF-IDF-векторным представлением, а не нейросетевой моделью;
- качество зависит от размера и близости обучающего корпуса.

