---
tags: [deep-learning, glossary, reference]
created: 2026-05-20T13:22:25
modified: 2026-05-20T13:22:25
---

# Deep Learning Glossary

# Deep Learning Glossary

This note defines key deep learning terms based on information from research notes in this vault.

## Attention Mechanism
A mechanism that enables a model to focus on relevant parts of an input sequence by computing a weighted sum of value vectors based on query-key compatibility. The Transformer architecture is built upon this concept.
*Source: [[Attention Survey]]*

## BERT (Bidirectional Encoder Representations from Transformers)
A model architecture based on the encoder part of the [[Transformers]] architecture. It uses bidirectional self-attention to learn representations from both the left and right context of a token. It is pre-trained using Masked Language Modeling and is highly effective for fine-tuning on various NLP tasks.
*Source: [[BERT]]*

## Contrastive Learning
A self-supervised learning method that trains a model to place similar (positive) inputs close together in an embedding space while pushing dissimilar (negative) inputs far apart. This is used to learn representations without labels.
*Source: [[Contrastive Learning]]*

## GAN (Generative Adversarial Network)
A framework for generative modeling where a *generator* network tries to create realistic data samples and a *discriminator* network tries to distinguish real samples from fake ones. They are powerful but can be unstable to train.
*Source: [[GAN Architecture]]*

## GPT (Generative Pre-trained Transformer)
A family of autoregressive language models based on the decoder part of the [[Transformers]] architecture. It uses causal (left-to-right) attention, making it particularly well-suited for text generation tasks.
*Source: [[GPT]]*

## Knowledge Distillation
A model compression technique where a smaller "student" model is trained to mimic the output (specifically, the soft probability distributions) of a larger, pre-trained "teacher" model. This allows for creating faster, smaller models that retain much of the original's performance.
*Source: [[Knowledge Distillation]]*

## Transformer
An architecture that replaces sequence-based recurrence (RNNs) with multi-head [[Self Attention]]. It is the foundation for most modern large language models, including [[BERT]] and [[GPT]], due to its parallelizability and scaling properties.
*Source: [[Transformers]]*
