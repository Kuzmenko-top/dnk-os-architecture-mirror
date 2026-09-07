# Patent Claim Parsing & Normalization Patterns

## Overview
Patent claims follow standardized legal formatting conventions governed by patent offices (USPTO, EPO, WIPO). This reference outlines robust regex and structure extraction strategies for clean-room IP analysis.

## Claim Types and Structure

1. **Independent Claims**:
   - Preamble stating the technical field and subject matter (e.g., "A computer-implemented method for...", "A distributed system comprising...").
   - Transitional phrase ("comprising", "consisting essentially of", "consisting of").
   - Body containing structural or procedural limitations (elements / steps).

2. **Dependent Claims**:
   - Reference back to a parent claim (e.g., "The method of claim 1, wherein...").
   - Additional narrowing limitations.

## Normalization Workflow

```
[Raw Patent Document (JSON/XML/Text)]
                  │
                  ▼
         [Preamble Stripper]
                  │
                  ▼
         [Claims Tokenizer (Regex Splitter)]
                  │
        ┌─────────┴─────────┐
        ▼                   ▼
[Independent Claims]  [Dependent Claims Hierarchy]
        │                   │
        ▼                   ▼
[Normalized Vector]   [Element Dependency Graph]
```

## Regular Expression Patterns for Claim Tokenization

```python
import re

# Split claims numbered 1., 2., 3.
CLAIM_SPLIT_REGEX = re.compile(r'(?=\b\d+\.\s+)')

# Extract claim number and reference dependencies
CLAIM_DEP_REGEX = re.compile(r'^\s*(\d+)\.\s+(?:The\s+\w+\s+(?:of|according\s+to)\s+claim\s+(\d+))?', re.IGNORECASE)
```
