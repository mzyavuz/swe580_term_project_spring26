"""
Synthesis Evaluator — Extra Credit
Tests note creation (synthesis) queries for both Config A and Config B.

Usage:
    python synthesis_evaluator.py --api-key YOUR_KEY
    python synthesis_evaluator.py --api-key YOUR_KEY --config a
"""

import argparse
import json
import os
import sys
import time
from datetime import datetime

from search_backend import build_index, get_note_by_path
from llm_runner import LLMRunner
from executors import create_executor_a, create_executor_b


SYNTHESIS_QUERIES = [
    {
        "id": "s01",
        "query": "Create a new research note titled 'Attention Survey' that summarizes the key ideas from the Transformers, Self Attention, and Attention Mechanisms notes.",
        "expected_folder": "research",
        "expected_title": "Attention Survey",
    },
    {
        "id": "s02",
        "query": "Write a new reference note called 'Deep Learning Glossary' defining the most important terms from my deep-learning tagged research notes.",
        "expected_folder": "reference",
        "expected_title": "Deep Learning Glossary",
    },
    {
        "id": "s03",
        "query": "Create a new project note for a 'Transformer Fine Tuner' project that builds on the Transformers and BERT research and links to the Fine Tuning Pipeline project.",
        "expected_folder": "projects",
        "expected_title": "Transformer Fine Tuner",
    },
]


def evaluate_synthesis_query(runner, query, tools, executor, vault_path, system_prompt="", verbose=False):
    """Run a synthesis query and verify a note was created."""
    result = runner.run(
        query=query["query"],
        tools=tools,
        tool_executor=executor,
        system_prompt=system_prompt,
        verbose=verbose,
    )

    # Check if create_note was called
    create_calls = [t for t in result["tool_calls"] if t["tool"] == "create_note"]
    note_created = len(create_calls) > 0

    # Verify file exists on disk
    expected_filename = query["expected_title"].replace(" ", "_") + ".md"
    expected_path = os.path.join(vault_path, query["expected_folder"], expected_filename)
    file_exists = os.path.exists(expected_path)

    # Check note is in index
    rel_path = f"{query['expected_folder']}/{expected_filename}"
    ix = build_index(vault_path)
    note_in_index = get_note_by_path(ix, rel_path) is not None

    return {
        "query_id": query["id"],
        "query": query["query"],
        "note_created_via_tool": note_created,
        "file_exists_on_disk": file_exists,
        "note_in_index": note_in_index,
        "expected_path": rel_path,
        "create_tool_calls": create_calls,
        "total_tool_calls": len(result["tool_calls"]),
        "total_tokens": result["total_input_tokens"] + result["total_output_tokens"],
        "rounds": result["rounds"],
        "response_preview": result["response"][:300],
    }


def run_synthesis_evaluation(runner, vault_path, tools, executor, config_name, system_prompt="",
                              delay=2.0, verbose=False):
    results = []
    print(f"\n{'='*60}")
    print(f"Synthesis Evaluation: {config_name}")
    print(f"{'='*60}")

    for i, query in enumerate(SYNTHESIS_QUERIES):
        print(f"\n[{i+1}/{len(SYNTHESIS_QUERIES)}] {query['id']}: {query['query'][:70]}...")
        try:
            result = evaluate_synthesis_query(runner, query, tools, executor,
                                               vault_path, system_prompt, verbose)
            status = "✓" if result["file_exists_on_disk"] else "✗"
            print(f"  {status} file_created={result['file_exists_on_disk']}  "
                  f"in_index={result['note_in_index']}  "
                  f"tool_calls={result['total_tool_calls']}  tokens={result['total_tokens']}")
            results.append(result)
        except Exception as e:
            print(f"  ✗ ERROR: {e}")
            results.append({"query_id": query["id"], "error": str(e),
                            "file_exists_on_disk": False, "note_in_index": False})

        if i < len(SYNTHESIS_QUERIES) - 1:
            time.sleep(delay)

    total = len(results)
    created = sum(1 for r in results if r.get("file_exists_on_disk"))
    print(f"\nSummary: {created}/{total} notes successfully created")
    return {"config": config_name, "results": results,
            "notes_created": created, "total_queries": total}


def main():
    parser = argparse.ArgumentParser(description="Synthesis (note creation) evaluator")
    parser.add_argument("--api-key", default=os.environ.get("LLM_API_KEY"))
    parser.add_argument("--base-url", default="https://openrouter.ai/api/v1")
    parser.add_argument("--model", default="google/gemini-2.5-flash")
    parser.add_argument("--vault", default="vault")
    parser.add_argument("--config", choices=["a", "b", "both"], default="both")
    parser.add_argument("--delay", type=float, default=2.0)
    parser.add_argument("--verbose", action="store_true")
    parser.add_argument("--output-dir", default="results")
    args = parser.parse_args()

    if not args.api_key:
        print("ERROR: Provide --api-key or set LLM_API_KEY.")
        sys.exit(1)

    ix = build_index(args.vault)
    runner = LLMRunner(base_url=args.base_url, api_key=args.api_key, model=args.model)
    print(f"Model: {args.model}")

    os.makedirs(args.output_dir, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    with open("config_a_tools.json") as f:
        tools_a = json.load(f)
    with open("config_b_tools.json") as f:
        tools_b = json.load(f)
    with open("config_a_prompt.txt") as f:
        prompt_a = f.read()
    with open("config_b_prompt.txt") as f:
        prompt_b = f.read()

    if args.config in ("a", "both"):
        eval_a = run_synthesis_evaluation(
            runner, args.vault, tools_a, create_executor_a(ix, args.vault),
            "Config A", prompt_a, args.delay, args.verbose,
        )
        out = os.path.join(args.output_dir, f"synthesis_a_{timestamp}.json")
        with open(out, "w") as f:
            json.dump(eval_a, f, indent=2)
        print(f"Config A synthesis results saved to {out}")

    if args.config in ("b", "both"):
        eval_b = run_synthesis_evaluation(
            runner, args.vault, tools_b, create_executor_b(ix, args.vault),
            "Config B", prompt_b, args.delay, args.verbose,
        )
        out = os.path.join(args.output_dir, f"synthesis_b_{timestamp}.json")
        with open(out, "w") as f:
            json.dump(eval_b, f, indent=2)
        print(f"Config B synthesis results saved to {out}")


if __name__ == "__main__":
    main()
