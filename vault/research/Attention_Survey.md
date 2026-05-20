---
tags: [attention, transformer, deep-learning, nlp, survey]
created: 2026-05-20T13:21:54
modified: 2026-05-20T13:21:54
---

# Attention Survey

# Attention Survey

This note summarizes the key concepts behind attention mechanisms, as detailed in the [[Attention Mechanisms]], [[Self Attention]], and [[Transformers]] notes.

## Core Idea

Attention mechanisms enable a model to focus on relevant parts of an input sequence. The most common formulation is Scaled Dot-Product Attention, defined as:

`Attention(Q, K, V) = softmax(QK^T / sqrt(d_k)) V`

This computes a weighted sum of `Value` vectors based on the compatibility of `Query` and `Key` vectors.

## Self-Attention

[[Self Attention]] is a specific type of attention where the Queries, Keys, and Values all derive from the same input sequence. This allows the model to weigh the importance of all other tokens in the sequence for a given token, capturing internal contextual relationships. The main drawback is its O(n²) computational cost.

## The Transformer

The [[Transformers|Transformer architecture]], introduced in "Attention Is All You Need", is a model that uses [[Self Attention]] as its core component, completely replacing recurrent layers. This allows for greater parallelization and has become the foundation for modern NLP models like BERT and GPT. Key components include Multi-Head Attention and Positional Encodings.