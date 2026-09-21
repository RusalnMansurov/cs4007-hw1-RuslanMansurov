"""Sublab Medium - Kazakh correction experiment."""

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from sublab_easy.registration_bot import (
    RATES_PER_MTOK,
    ask_once,
    estimate_cost,
)


DATA = Path(__file__).resolve().parent.parent / "data" / "kazakh_errors.json"


MODELS = [
    ("openrouter", "google/gemma-4-26b-a4b-it:free"),
    ("openrouter", "qwen/qwen3.8-27b"),
    ("openrouter", "deepseek/deepseek-v4-flash-0731"),
    ("openai", "gpt-5.6-luna"),
    ("openai", "gpt-5.6-terra"),
    ("openai", "gpt-5.6-sol"),
]


FREE_MODELS = [
    ("openrouter", "google/gemma-4-26b-a4b-it:free"),
]


PAID_MODELS = [
    ("openrouter", "qwen/qwen3.8-27b"),
    ("openrouter", "deepseek/deepseek-v4-flash-0731"),
    ("openai", "gpt-5.6-luna"),
    ("openai", "gpt-5.6-terra"),
    ("openai", "gpt-5.6-sol"),
]


QWEN_ONLY = [
    ("openrouter", "qwen/qwen3.8-27b"),
]


def load_sentences() -> list[dict]:
    """Load corrupted Kazakh sentences."""

    return json.loads(
        DATA.read_text(encoding="utf-8")
    )["sentences"]


def build_prompt(corrupted: str) -> str:
    """Create prompt for correcting Kazakh text."""

    return (
        "The following text is in Kazakh and may contain incorrect letters, "
        "joined words, doubled letters, missing hyphens, or letters from the "
        "wrong alphabet.\n\n"
        f"Text: {corrupted}\n\n"
        "Correct the sentence and list the changes you made.\n"
        "Return exactly one JSON object and nothing else in this format:\n"
        '{"corrected": "...", "changes": ["...", "..."]}'
    )


def parse_response(text: str) -> dict:
    """Extract JSON from model response."""

    text = text.strip()

    # Try pure JSON first.
    try:
        data = json.loads(text)

    except json.JSONDecodeError:
        data = None

    # If model added Markdown/prose, find JSON object.
    if data is None:

        start = text.find("{")
        end = text.rfind("}")

        if start == -1 or end == -1 or end < start:
            raise ValueError(
                f"No JSON found in response: {text}"
            )

        json_text = text[start:end + 1]

        try:
            data = json.loads(json_text)

        except json.JSONDecodeError as exc:
            raise ValueError(
                f"Invalid JSON in response: {text}"
            ) from exc

    if not isinstance(data, dict):
        raise ValueError("JSON response is not an object")

    if not isinstance(data.get("corrected"), str):
        raise ValueError("Missing or invalid 'corrected'")

    if not isinstance(data.get("changes"), list):
        raise ValueError("Missing or invalid 'changes'")

    return data


def correct_with(model: str, corrupted: str, via: str) -> dict:
    """Correct one sentence with one model."""

    prompt = build_prompt(corrupted)

    # Qwen needs a small max_tokens limit.
    if model == "qwen/qwen3.8-27b":

        response = ask_once(
            prompt,
            model=model,
            via=via,
            max_tokens=500,
        )

    else:

        response = ask_once(
            prompt,
            model=model,
            via=via,
        )

    parsed = parse_response(
        response["text"]
    )

    return {
        "corrected": parsed["corrected"],
        "changes": parsed["changes"],
        "input_tokens": response["input_tokens"],
        "output_tokens": response["output_tokens"],
        "model": response["model"],
    }


def score_correction(returned: str, expected: str) -> dict:
    """Compare returned sentence with expected sentence."""

    exact = returned == expected

    common_length = min(
        len(returned),
        len(expected)
    )

    char_diff = sum(
        1
        for i in range(common_length)
        if returned[i] != expected[i]
    )

    char_diff += abs(
        len(returned) - len(expected)
    )

    return {
        "exact": exact,
        "char_diff": char_diff,
    }


def run_all(models=None) -> list[dict]:
    """Run selected models against all sentences."""

    if models is None:
        models = MODELS

    rows = []
    sentences = load_sentences()

    for via, model in models:

        print()
        print("=" * 60)
        print(f"MODEL: {model}")
        print("=" * 60)

        for s in sentences:

            print(
                f"Running {s['id']}...",
                end=" ",
                flush=True
            )

            try:

                result = correct_with(
                    model,
                    s["corrupted"],
                    via,
                )

            except Exception as exc:

                print("FAILED")

                rows.append({
                    "model": model,
                    "id": s["id"],
                    "errors": s["errors"],
                    "failed": repr(exc),
                })

                continue

            rate_in, rate_out = RATES_PER_MTOK[model]

            score = score_correction(
                result["corrected"],
                s["correct"],
            )

            cost = estimate_cost(
                result["input_tokens"],
                result["output_tokens"],
                rate_in,
                rate_out,
            )

            rows.append({
                "model": model,
                "id": s["id"],
                "errors": s["errors"],
                "corrupted": s["corrupted"],
                "expected": s["correct"],
                "corrected": result["corrected"],
                "changes": result["changes"],
                "exact": score["exact"],
                "char_diff": score["char_diff"],
                "input_tokens": result["input_tokens"],
                "output_tokens": result["output_tokens"],
                "cost": cost,
            })

            if score["exact"]:
                print("EXACT")

            else:
                print(
                    f"NOT EXACT "
                    f"(char_diff={score['char_diff']})"
                )

    return rows


def summarise(rows: list[dict], models=None) -> None:
    """Print summary."""

    if models is None:
        models = MODELS

    print()
    print("=" * 76)
    print("SUMMARY")
    print("=" * 76)

    print(
        f"{'model':38}"
        f"{'exact':>7}"
        f"{'failed':>8}"
        f"{'tokens':>10}"
        f"{'cost $':>11}"
    )

    print("-" * 76)

    for _, model in models:

        mine = [
            r
            for r in rows
            if r["model"] == model
        ]

        exact = sum(
            1
            for r in mine
            if r.get("exact")
        )

        failed = sum(
            1
            for r in mine
            if r.get("failed")
        )

        tokens = sum(
            r.get("input_tokens", 0)
            + r.get("output_tokens", 0)
            for r in mine
        )

        cost = sum(
            r.get("cost", 0.0)
            for r in mine
        )

        print(
            f"{model:38}"
            f"{exact:>7}"
            f"{failed:>8}"
            f"{tokens:>10}"
            f"{cost:>11.5f}"
        )


def save_results(rows: list[dict], filename: str) -> None:
    """Save results to outputs folder."""

    output_dir = (
        Path(__file__).resolve().parent.parent
        / "outputs"
    )

    output_dir.mkdir(exist_ok=True)

    output_file = output_dir / filename

    output_file.write_text(
        json.dumps(
            rows,
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )

    print()
    print("=" * 60)
    print(f"Saved {len(rows)} results")
    print(f"File: {output_file}")
    print("=" * 60)


def main() -> None:

    print()
    print("=" * 60)
    print("KAZAKH CORRECTION EXPERIMENT")
    print("=" * 60)

    print()
    print("Choose mode:")
    print("1 - FREE model only")
    print("2 - ALL PAID models")
    print("3 - QWEN only")
    print("0 - Exit")

    print()

    choice = input(
        "Enter 1, 2, 3 or 0: "
    ).strip()

    # FREE MODE
    if choice == "1":

        print()
        print("FREE MODE")
        print("Model: Gemma")
        print("Requests: 8")

        results = run_all(
            FREE_MODELS
        )

        summarise(
            results,
            FREE_MODELS
        )

        save_results(
            results,
            "free_corrections.json"
        )

    # ALL PAID MODELS
    elif choice == "2":

        print()
        print("=" * 60)
        print("WARNING: ALL PAID MODELS")
        print("=" * 60)

        print()
        print("5 models x 8 sentences")
        print("Total: 40 paid requests")

        confirm = input(
            "Type YES to continue: "
        ).strip()

        if confirm != "YES":
            print("Cancelled.")
            return

        results = run_all(
            PAID_MODELS
        )

        summarise(
            results,
            PAID_MODELS
        )

        save_results(
            results,
            "paid_corrections.json"
        )

    # QWEN ONLY
    elif choice == "3":

        print()
        print("=" * 60)
        print("QWEN ONLY MODE")
        print("=" * 60)

        print()
        print("Model: qwen/qwen3.8-27b")
        print("Requests: 8")
        print("DeepSeek and GPT models will NOT run.")

        print()

        confirm = input(
            "Type YES to start Qwen: "
        ).strip()

        if confirm != "YES":
            print("Cancelled.")
            return

        results = run_all(
            QWEN_ONLY
        )

        summarise(
            results,
            QWEN_ONLY
        )

        save_results(
            results,
            "qwen_corrections.json"
        )

    elif choice == "0":

        print("Exit.")
        return

    else:

        print("Invalid choice.")
        return


if __name__ == "__main__":
    main()