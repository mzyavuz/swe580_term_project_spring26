# SWE 580 - Applied Large Language Models | Term Project
**M. Zeynep Çakmakcı**

**Instructor: Atay Özgövde**

---

## 1. Introduction

When designing an AI assistant that helps users search through personal notes, one key decision is how to structure the tools it can use. Should the assistant have a small number of powerful, multi-purpose tools? Or many simple, single-purpose ones?

This project investigates that question empirically. Using a provided evaluation framework, I engineered the tool descriptions and system prompts for two configurations of an LLM-driven personal knowledge retrieval system and evaluated them on 25 standardized queries against a vault of 100 markdown notes:

- **Configuration A** — 4 coarse-grained tools with rich, flexible parameters
- **Configuration B** — 9 fine-grained tools with simple, focused parameters

Both configurations use the same Whoosh full-text search backend, the same vault, and the same evaluation queries. Only the tool interface and system prompt differ. I chose **Option 2: Direct API Function Calling** using the OpenRouter API, with Google Gemini 2.5 Flash as the primary model.

For extra credit, I also implemented note creation (synthesis) tools and compared results across two models: Gemini 2.5 Flash and Gemini 2.5 Pro.

---

## 2. Design

### 2.1 What Was Given vs. What I Contributed

The project scaffold was provided by the instructor. The tool names, parameter names, routing logic, search backend, vault, and test queries were all fixed. My task was to write the **tool descriptions** (the `"description"` fields in the JSON tool definitions) and the **system prompts** for both configurations — which are the only inputs the LLM actually sees when deciding how to behave.

The baseline distribution shipped with placeholder descriptions such as `"Search notes in the vault."` and a 3-line system prompt: *"You are a helpful assistant that searches through a personal knowledge vault. Use the provided tools to find relevant notes."* These produced only 20–28% success rates. The work in this project was to understand why, and to fix it through iterative prompt and description engineering.

For extra credit, I also implemented a `create_note` tool from scratch — adding the backend function, executor routing, tool definitions, and a synthesis evaluation script.

### 2.2 Configuration A — Coarse-Grained (4+1 Tools)

The tool structure was provided. Config A consolidates operations into 4 broad tools:

| Tool | Purpose |
|---|---|
| `search_notes` | Combined search by content, tags, and/or date range (all parameters optional) |
| `get_note` | Retrieve a note by title or path |
| `get_related_notes` | Find notes linked to/from a note (direction: incoming, outgoing, both) |
| `get_vault_overview` | Vault statistics and recently modified notes |
| `create_note` | *(extra credit, implemented by me)* Create a new note |

The design philosophy is consolidation: the LLM has fewer decisions to make and the backend handles combining filters internally.

### 2.3 Configuration B — Fine-Grained (9+1 Tools)

The tool structure was provided. Config B splits each operation into its own dedicated tool:

| Group | Tools |
|---|---|
| Search | `search_by_content`, `search_by_tags`, `search_by_date` |
| Retrieval | `get_note_by_path`, `get_note_by_title` |
| Graph | `get_outgoing_links`, `get_incoming_links` |
| Stats | `get_vault_stats`, `get_recent_notes` |
| Creation | `create_note` *(extra credit, implemented by me)* |

The design philosophy is specialization: each tool does exactly one thing, giving the LLM precise control but also more orchestration responsibility.

### 2.4 My Contribution — Tool Descriptions and System Prompts

The key engineering work was writing descriptions that guide the LLM's decision-making. Both system prompts I wrote include:

- **RESULT_PATHS convention** — The LLM must end every response with `RESULT_PATHS: ["path/to/note.md", ...]`. Without this, the evaluator cannot extract retrieved paths from free-text responses, causing correct retrievals to score zero.
- **Tool selection guide** — Explicit rules mapping query intent to tool choice (e.g. "what notes link to X?" → use the incoming links tool, not content search).
- **Title convention** — Notes have no `title` frontmatter field; title is derived from filename. The prompt documents that `Self_Attention.md` → `"Self Attention"`, preventing the LLM from inventing titles like "Reinforcement Learning Research" or "Chatbot Prototype Project".
- **Folder-to-tag mapping** — Meeting notes are tagged `meeting`, project notes tagged `project`, etc. Without this, the LLM searched `query="meeting notes"` instead of `tags=["meeting"]`, returning zero results.
- **Multi-step guidance** — Config B's prompt explains that multi-faceted queries require calling multiple tools and intersecting the results, since no single tool handles combined filters.

---

## 3. Methodology

### 3.1 Test Environment

- **Vault:** 100 markdown notes across 5 folders: `research/`, `projects/`, `meetings/`, `daily/`, `reference/`
- **Each note** has YAML frontmatter (tags, creation date, modification date), markdown content, and wiki-style `[[links]]` to other notes
- **Index:** Whoosh full-text search, rebuilt at evaluation start

### 3.2 Test Queries

25 queries across 6 categories:

| Category | Count | Example |
|---|---|---|
| simple_lookup | 2 | "Get the note titled Transformers" |
| tag_search | 2 | "Show me all notes tagged with attention" |
| temporal | 3 | "Find notes created on January 15, 2026" |
| content_search | 2 | "Find notes discussing gradient descent" |
| multi_faceted | 9 | "Find meeting notes from January 10 to 14, 2026" |
| graph_based | 7 | "What notes link to Transformers?" |

Each query has a fixed ground truth (correct note paths). Success requires returning exactly the right set.

### 3.3 Metrics

- **Success rate** — fraction of queries with perfect precision and full recall (up to 10 expected notes)
- **Precision** — of notes returned, how many were correct
- **Recall** — of correct notes (capped at 10), how many were returned
- **F1** — harmonic mean of precision and recall
- **Avg tool calls** — how many tool calls the LLM made per query
- **Avg tokens** — total input + output tokens per query
- **Avg latency** — wall-clock seconds per query

### 3.4 Implementation Choice

I used **Option 2: Direct API Function Calling** via OpenRouter (OpenAI-compatible endpoint). The LLM receives tool definitions in JSON, decides which tools to call, and the evaluator executes them against the Whoosh backend. The evaluation loop supports up to 10 rounds of tool calling per query.

Primary model: `google/gemini-2.5-flash`. Comparison model: `google/gemini-2.5-pro`.

### 3.5 The Baseline Problem and How It Was Fixed

Initial results were very poor (Config A: 20%, Config B: 28%) despite the LLM retrieving correct notes. The root cause was that the evaluator extracts note paths by looking for a `RESULT_PATHS: [...]` line in the response. Without this instruction in the system prompt, the LLM returned free-text answers like *"I found three notes: Self Attention, Transformers, and Attention Mechanisms"* — and scored zero even when the retrieval was perfect.

Adding the `RESULT_PATHS` instruction to both prompts was the single most impactful change, immediately improving scores by ~50 percentage points. The remaining improvements came from tool selection guidance and title convention documentation.

---

## 4. Results

### 4.1 Baseline vs Final (Gemini 2.5 Flash)

| | Config A Baseline | Config A Final | Config B Baseline | Config B Final |
|---|---|---|---|---|
| Success rate | 20% | **88%** | 28% | **84%** |
| Avg F1 | 0.200 | 0.932 | 0.280 | 0.956 |
| Avg tokens | 1,322 | 3,654 | 1,835 | 4,774 |
| Avg tool calls | 1.00 | 1.12 | 1.16 | 1.48 |

The token increase from baseline to final is expected — better prompts are longer and cause the LLM to write richer responses including the RESULT_PATHS line.

### 4.2 Config A vs Config B — Final Results (Gemini 2.5 Flash)

| Metric | Config A | Config B | Winner |
|---|---|---|---|
| Success rate | **88%** | 84% | A |
| Avg F1 | 0.932 | **0.956** | B |
| Avg precision | 0.947 | **0.987** | B |
| Avg recall | 0.933 | **0.947** | B |
| Avg tool calls | **1.12** | 1.48 | A |
| Avg tokens | **3,654** | 4,774 | A |
| Avg latency | **1.67s** | 1.71s | A |

Config A wins on success rate and efficiency. Config B wins on precision and recall when it does succeed — meaning it is more accurate per result returned, but fails more often overall.

### 4.3 Per-Category Breakdown (Gemini 2.5 Flash)

| Category | Config A | Config B |
|---|---|---|
| simple_lookup | **100%** | **100%** |
| tag_search | **100%** | **100%** |
| temporal | **100%** | **100%** |
| content_search | **100%** | **100%** |
| multi_faceted | **89%** | 78% |
| graph_based | **71%** | **71%** |

Both configurations handle straightforward queries (lookup, tag, date, content) perfectly. The gap appears in **multi_faceted** queries, where Config A's single combined tool handles parameter combinations internally, while Config B's separate tools must be intersected manually and are vulnerable to the 10-result cap cutting off valid notes. Both configurations fail equally on graph-based queries.

### 4.4 Failure Analysis

**Config A remaining failures (3/25):**

| Query | Root cause |
|---|---|
| q09: "research notes about attention from January 2026" | LLM passed 4 tags with AND logic — over-constrained, zero results returned |
| q16: "prerequisite topics of Transformers" | Tool correctly returned 3 outgoing links; LLM included `projects/Paper_Recommender.md` which is not a prerequisite topic — semantic filtering needed |
| q18: "project notes related to attention mechanism research" | Target projects link to Transformers/Self_Attention, not directly to Attention_Mechanisms — requires multi-hop graph traversal |

**Config B remaining failures (4/25):**

| Query | Root cause |
|---|---|
| q15: "deep-learning notes mentioning neural networks" | `search_by_tags(["deep-learning"])` hit the 10-result cap, cutting off Diffusion_Models and Recurrent_Networks before intersection |
| q16: same as Config A (semantic filtering) | Additionally, LLM emitted `RESULT_PATHS:` with no array — a formatting bug |
| q18: same multi-hop failure as Config A | — |
| q22: "meeting notes discussing BERT" | `search_by_content("BERT")` ranked Advisor_Meeting_Feb07 outside the top-10, so it was excluded from the intersection |

The key insight here is that Config B introduced a new failure mode that Config A doesn't have: **cap-sensitive intersection**. When two separate tool results are intersected, any note that fell outside either tool's 10-result cap is silently excluded. Config A's combined `search_notes` tool filters and ranks internally before returning, which avoids this problem.

### 4.5 Cross-Model Comparison: Flash vs Pro

| Metric | Flash / A | Flash / B | Pro / A | Pro / B |
|---|---|---|---|---|
| Success rate | **88%** | **84%** | **88%** | 80% |
| Avg F1 | 0.932 | 0.956 | **0.980** | **0.941** |
| Avg precision | 0.947 | **0.987** | 0.979 | 0.981 |
| Avg recall | 0.933 | 0.947 | **0.987** | 0.933 |
| Avg tool calls | 1.12 | 1.48 | 1.20 | **1.56** |
| Avg tokens | 3,654 | 4,774 | 4,569 | **5,826** |
| Avg latency | **1.67s** | **1.71s** | 8.45s | 9.84s |

Gemini 2.5 Pro achieves a higher F1 score (0.980 on Config A) and recall (0.987) than Flash, but its success rate is identical on Config A and lower on Config B (80% vs 84%). More notably, Pro is **5× slower** and uses 25–30% more tokens. For this task, Flash offers a better cost-efficiency trade-off. The higher F1 from Pro reflects that it retrieves slightly more of the correct notes per query — but the strict success-rate metric (requiring perfect precision AND full recall) punishes this if any extra notes are included.

### 4.6 Synthesis Evaluation (Extra Credit)

I added a `create_note` tool to both configurations and tested 3 synthesis queries:

| Query | Expected outcome |
|---|---|
| s01 | Create "Attention Survey" synthesizing Transformers, Self Attention, Attention Mechanisms |
| s02 | Create "Deep Learning Glossary" from all deep-learning tagged notes |
| s03 | Create "Transformer Fine Tuner" project note linking to existing notes |

**All 12 combinations (3 queries × 2 configs × 2 models) succeeded.** Every note was created on disk and immediately indexed.

| | Flash / A | Flash / B | Pro / A | Pro / B |
|---|---|---|---|---|
| Notes created | 3/3 | 3/3 | 3/3 | 3/3 |
| s01 tokens | 8,417 | 9,418 | 9,893 | 11,404 |
| s02 tokens | 22,837 | 18,863 | 26,439 | 30,777 |
| s03 tokens | 3,891 | 4,535 | 12,302 | 12,207 |
| s02 tool calls | 12 | 8 | 12 | 13 |
| s03 tool calls | 1 | 1 | 4 | 4 |

s02 (Deep Learning Glossary) was the most expensive query — the LLM had to retrieve many individual notes before synthesizing, resulting in 8–13 tool calls and 18k–30k tokens. s03 showed a model difference: Flash created the project note in 1 tool call without looking up sources, while Pro made 4 calls to retrieve Transformers, BERT, and the Fine Tuning Pipeline note first. Pro produced a richer, more connected note; Flash was faster but less thorough.

Config B was slightly more token-efficient for s02 (18,863 vs 22,837 for Flash) because its fine-grained tools let the LLM fetch only the fields it needs, rather than receiving full note objects from a combined tool.

---

## 5. Discussion

### 5.1 Which Configuration Performed Better?

**Config A performed better overall.** It had a higher success rate (88% vs 84%), lower token usage, fewer tool calls, and lower latency. Its coarse-grained design means the LLM has fewer decisions to make — it uses one tool and lets the backend handle the filtering logic internally.

Config B performed better on precision (0.987 vs 0.947) and F1 (0.956 vs 0.932) — meaning when it retrieves notes, they tend to be exactly right. But it fails more often due to the intersection problem created by the 10-result cap on each individual tool.

### 5.2 Why Does Tool Granularity Matter?

The core trade-off is about **where the complexity lives**:

- In **Config A**, complexity is hidden inside the tool. The LLM makes one call and the backend resolves the intersection of content, tags, and date filters in a single ranked query. The LLM doesn't need to coordinate multiple results.
- In **Config B**, complexity is exposed to the LLM. The LLM must decide which tools to call, execute them separately, and mentally intersect the results. This works well when queries are simple and a single tool is sufficient, but breaks down for multi-faceted queries due to cap limitations.

This suggests that **coarse-grained tools are more robust for LLMs** when the underlying operations are naturally combinatorial. Fine-grained tools are better suited to cases where the LLM needs precise, predictable control over what data it receives — for example, in synthesis tasks where Config B showed slightly better token efficiency.

### 5.3 The Role of Prompt Engineering

Perhaps the most important finding of this project is that **prompt engineering contributed more to performance than tool granularity did**. The improvement from baseline to final was +68 percentage points for Config A and +56 percentage points for Config B — almost entirely driven by:

1. Adding the `RESULT_PATHS` output format
2. Writing a clear tool selection guide
3. Documenting the title convention (filename = title)
4. Mapping folder categories to tag values

Without these prompt changes, neither configuration worked well regardless of how the tools were structured. With them, both configurations worked well. The tool design created the final 4% difference — the prompts created the 60%+ difference.

### 5.4 Flash vs Pro — Is More Power Worth It?

For this task: **no**. Gemini 2.5 Pro achieved marginally higher F1 scores but the same or lower success rates, while being 5× slower and 25–30% more expensive per query. The main observable difference was in synthesis tasks, where Pro retrieved more source material before writing — producing richer notes but at significantly higher cost.

For production use, the right model choice depends on what metric matters most. If every missed note has a cost, Pro's higher recall is worth it. If throughput and cost matter more, Flash is the better choice.

### 5.5 Recommendations

1. **Use coarse-grained tools (Config A style)** as the default for retrieval tasks. Fewer tools reduce the LLM's coordination burden and avoid cap-sensitive intersection failures.
2. **Use fine-grained tools (Config B style)** when precise cost control is needed, or when queries are typically single-dimension (tag only, date only, etc.).
3. **Invest heavily in system prompt design.** Tool descriptions and output format instructions matter more than tool granularity for raw performance.
4. **Raise the result cap above 10** if the vault will grow. The 10-result limit was the proximate cause of 3 out of 7 remaining failures.
5. **For synthesis tasks**, fine-grained tools offer slightly better token efficiency because the LLM can fetch only the fields it needs.

---

## 6. Conclusion

This project compared coarse-grained and fine-grained tool interfaces for LLM-driven personal knowledge retrieval. After prompt engineering, Config A achieved 88% success rate and Config B achieved 84%, both far exceeding the 20–28% baseline.

Config A outperformed Config B on overall success, token efficiency, and latency. Config B outperformed on precision when it succeeded, but was vulnerable to a failure mode unique to fine-grained tools: intersection queries that silently drop valid notes when any single tool hits its result cap.

Across two models (Gemini 2.5 Flash and Pro), Flash offered better cost-efficiency with comparable success rates. Pro showed marginal gains in F1 and recall at 5× the latency. All synthesis queries succeeded across all combinations.

The most significant finding is that **prompt engineering dominated tool design** as a performance driver. The output format convention (`RESULT_PATHS`), tool selection guide, and title convention together accounted for the majority of the improvement — suggesting that regardless of tool granularity, clear LLM instructions are the prerequisite for any system to work.

**Limitations:**
- Results depend on a single 100-note vault; a larger or differently structured vault may shift the balance
- LLM outputs are non-deterministic; repeated runs may produce slightly different scores
- The 10-result cap in the search backend artificially limits recall for large result sets and disproportionately penalizes Config B's intersection-based approach
- Only two models from the same provider (Google) were compared; results may differ with models from other families

**Future work:**
- Test with a larger vault (1000+ notes) to stress-test the result cap problem
- Evaluate with open-source models (Llama, Mistral) to assess cross-family generalization
- Explore hybrid configurations: coarse tools for retrieval, fine tools for post-retrieval filtering
- Implement multi-hop graph traversal to address the remaining graph_based failures
