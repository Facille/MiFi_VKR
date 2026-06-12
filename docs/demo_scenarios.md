# Demo Scenarios

Use these snippets in the web demo at `http://127.0.0.1:8765`.

## Token-Level Autocomplete

```python
pri<CURSOR>
```

Expected top suggestion:

```python
print
```

```python
numbers = [1, 2, 3]
num<CURSOR>
```

Expected top suggestion:

```python
numbers
```

```python
def calculate_sum(numbers):
    ret<CURSOR>
```

Expected top suggestion:

```python
return
```

## Block-Level Prediction

```python
def clean_names(names):
    result = []
    for name in names:
        result.append(name.strip().lower())
    <CURSOR>
```

Expected idea:

```python
return result
```

```python
def total_prices(prices):
    total = 0
    for price in prices:
        total += price
    <CURSOR>
```

Expected idea:

```python
return total
```

```python
def is_positive(number):
    if number > 0:
        <CURSOR>
```

Expected idea:

```python
return True
```

```python
class TaskList:
    def __init__(self):
        self.tasks = []

    def add(self, task):
        self.tasks.append(task)
        <CURSOR>
```

Expected idea:

```python
return len(self.tasks)
```

## What To Explain During The Demo

- Token suggestions use the current token prefix and context symbols.
- Block predictions use AST context, previous block signatures, scope, tokens, embeddings and fallback templates.
- The system shows reasons and matched features for interpretability.
- The web page is an IDE integration simulation, not a full IDE extension.
