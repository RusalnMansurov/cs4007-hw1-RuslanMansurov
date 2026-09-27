"""Sublab Easy - a course-registration chatbot, and the bill it runs up.

Run with:
    py registration_bot.py paid   -> runs gpt-5.6-luna via OpenAI,
                                      saves to results_paid.txt
    py registration_bot.py free   -> runs llama-3.3-70b-versatile via Groq
                                      (instructor-approved substitute for the
                                      OpenRouter free model, whose shared rate
                                      limit was exhausted by every student
                                      running this assignment at once),
                                      saves to results_free.txt
"""

import json
import os
from pathlib import Path

from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

OPENROUTER_BASE_URL = "https://openrouter.ai/api/v1"
GROQ_BASE_URL = "https://api.groq.com/openai/v1"

CATALOGUE = Path(__file__).resolve().parent.parent / "data" / "courses.json"

# Prices in USD per million tokens.
RATES_PER_MTOK = {
    # OpenAI
    "gpt-5.6-luna": (0.20, 1.20),
    "gpt-5.6-terra": (2.00, 12.00),
    "gpt-5.6-sol": (5.00, 30.00),

    # OpenRouter
    "google/gemma-4-26b-a4b-it:free": (0.00, 0.00),
    "qwen/qwen3.8-27b": (0.45, 3.20),
    "deepseek/deepseek-v4-flash-0731": (0.14, 0.28),

    # Groq - instructor-approved substitute for the OpenRouter free model,
    # whose shared rate limit was consistently exhausted by every student
    # running this assignment at once. Groq's free tier uses a personal,
    # non-shared rate limit instead.
    "openai/gpt-oss-120b": (0.00, 0.00),
}


def load_catalogue() -> dict:
    """Load course catalogue."""
    return json.loads(CATALOGUE.read_text(encoding="utf-8"))


# ----------------------------------------------------------
# API clients
# ----------------------------------------------------------

def openai_client() -> OpenAI:
    """Create OpenAI client."""
    key = os.environ.get("OPENAI_API_KEY")
    if not key:
        raise RuntimeError(
            "OPENAI_API_KEY is not set. Copy .env.example to .env."
        )
    return OpenAI(api_key=key)


def openrouter_client() -> OpenAI:
    """Create OpenRouter client."""
    key = os.environ.get("OPENROUTER_API_KEY")
    if not key:
        raise RuntimeError(
            "OPENROUTER_API_KEY is not set. Copy .env.example to .env."
        )
    return OpenAI(api_key=key, base_url=OPENROUTER_BASE_URL)


def groq_client() -> OpenAI:
    """Create Groq client.

    Instructor-approved substitute for the OpenRouter free model, because
    google/gemma-4-26b-a4b-it:free's shared rate limit was consistently
    exhausted by every student running this assignment at once.
    """
    key = os.environ.get("GROQ_API_KEY")
    if not key:
        raise RuntimeError(
            "GROQ_API_KEY is not set. Add it to .env."
        )
    return OpenAI(api_key=key, base_url=GROQ_BASE_URL)


def client_for(via: str) -> OpenAI:
    """Return client for selected provider."""
    if via == "openai":
        return openai_client()
    if via == "openrouter":
        return openrouter_client()
    if via == "groq":
        return groq_client()
    raise ValueError(
        'via must be "openai", "openrouter", or "groq", got ' + repr(via)
    )


# ----------------------------------------------------------
# System prompt
# ----------------------------------------------------------

def build_system_prompt(catalogue: dict) -> str:
    """Build course-registration system prompt."""
    rules = catalogue["rules"]
    student = catalogue["student"]
    courses = catalogue["courses"]

    lines = []

    lines.append(
        "You are a course registration assistant for Narxoz University, "
        "term " + catalogue["term"] + "."
    )
    lines.append("")

    lines.append("STUDENT")
    lines.append("Student ID: " + student["student_id"])
    lines.append("Year: " + str(student["year"]))
    lines.append("Programme: " + student["programme"])
    lines.append("Already completed courses: " + ", ".join(student["completed"]))
    lines.append("")

    lines.append("REGISTRATION RULES")
    lines.append("Maximum credits per term: " + str(rules["max_credits"]))
    lines.append("Minimum credits per term: " + str(rules["min_credits"]))
    lines.append(rules["note"])
    lines.append("")

    lines.append("COURSE CATALOGUE")
    for c in courses:
        seats_left = c["seats_total"] - c["seats_taken"]
        schedule_str = "; ".join(
            "%s %s-%s" % (s["day"], s["start"], s["end"]) for s in c["schedule"]
        )
        prereq_str = ", ".join(c["prerequisites"]) if c["prerequisites"] else "none"
        lines.append(
            "%s | %s | %d credits | prerequisites: %s | schedule: %s | "
            "seats: %d/%d (remaining: %d) | instructor: %s"
            % (c["code"], c["title"], c["credits"], prereq_str, schedule_str,
               c["seats_taken"], c["seats_total"], seats_left, c["instructor"])
        )
    lines.append("")

    lines.append("STRICT RULES YOU MUST FOLLOW")
    lines.append(
        "1. The catalogue above is the ONLY source of truth. Never invent a "
        "course, code, credit count, instructor, or schedule that is not "
        "listed above."
    )
    lines.append(
        "2. If a student asks about a course code that does not appear in "
        "the catalogue, you MUST refuse and clearly state that no such "
        "course exists in the catalogue. Do not guess details for it under "
        "any circumstances."
    )
    lines.append(
        "3. Before registering a student for any course, check ALL of the "
        "following: (a) prerequisites are in their completed list, (b) the "
        "course has remaining seats, (c) the student has not already "
        "completed it, (d) it does not have a schedule conflict "
        "(overlapping day and time) with any other course the student is "
        "registering for in this conversation."
    )
    lines.append(
        "4. If two requested courses share the same day and overlapping "
        "time, refuse to register both and explain the conflict "
        "explicitly, naming both courses and the overlapping time."
    )
    lines.append(
        "5. Always show your reasoning for prerequisite, seat, and "
        "schedule checks when registering or refusing a course."
    )

    return "\n".join(lines)


# ----------------------------------------------------------
# One API call
# ----------------------------------------------------------

def chat(messages: list[dict], model: str = "gpt-5.6-luna",
         via: str = "openai", max_tokens: int | None = None) -> dict:
    """Send messages to a model.

    max_tokens is optional. If given, and via is "openai", it is sent as
    max_completion_tokens (newer OpenAI models reject the old name).
    Other providers still use the classic max_tokens name.
    """
    client = client_for(via)

    request = {"model": model, "messages": messages}

    if max_tokens is not None:
        if via == "openai":
            request["max_completion_tokens"] = max_tokens
        else:
            request["max_tokens"] = max_tokens

    response = client.chat.completions.create(**request)

    return {
        "text": response.choices[0].message.content,
        "input_tokens": response.usage.prompt_tokens,
        "output_tokens": response.usage.completion_tokens,
        "model": model,
    }


def ask_once(prompt: str, model: str = "gpt-5.6-luna",
             via: str = "openai", max_tokens: int | None = None) -> dict:
    """Make one request without conversation history."""
    return chat([{"role": "user", "content": prompt}], model=model, via=via,
               max_tokens=max_tokens)


# ----------------------------------------------------------
# Conversation
# ----------------------------------------------------------

def new_conversation(catalogue: dict) -> list[dict]:
    """Create new conversation."""
    return [{"role": "system", "content": build_system_prompt(catalogue)}]


def run_turn(history: list[dict], user_text: str, model: str = "gpt-5.6-luna",
             via: str = "openai") -> tuple[list[dict], dict]:
    """Run one conversation turn."""
    history = history + [{"role": "user", "content": user_text}]
    reply = chat(history, model=model, via=via)
    history = history + [{"role": "assistant", "content": reply["text"]}]
    return history, reply


# ----------------------------------------------------------
# Cost
# ----------------------------------------------------------

def estimate_cost(input_tokens: int, output_tokens: int,
                  rate_in: float, rate_out: float) -> float:
    """Calculate API call cost."""
    return (input_tokens / 1_000_000) * rate_in + (output_tokens / 1_000_000) * rate_out


def cost_of(usage: dict) -> float:
    """Calculate cost of one result."""
    rate_in, rate_out = RATES_PER_MTOK[usage["model"]]
    return estimate_cost(usage["input_tokens"], usage["output_tokens"], rate_in, rate_out)


def conversation_cost(usages: list[dict]) -> float:
    """Calculate total conversation cost."""
    return sum(cost_of(u) for u in usages)


# ----------------------------------------------------------
# The five scripted turns
# ----------------------------------------------------------

SCRIPT = [
    "I am a third-year student. Which courses am I still eligible to register for?",
    "Register me for CSS-4007 and CSS-4102.",
    "How many credits would that be in total, and am I within the limit?",
    "Add CSS-4090 Quantum Machine Learning to my schedule.",
    "Я студент третьего курса. На какие курсы я ещё могу записаться?",
]


def run_script(model: str, via: str, out_file: Path | None = None) -> list[dict]:
    """Run the five scripted turns, print the running bill, and optionally
    save the full transcript + table to out_file."""
    history = new_conversation(load_catalogue())
    usages = []
    lines = []

    header = "===== %s / %s =====" % (via, model)
    print("\n" + header)
    lines.append(header)

    for i, user_text in enumerate(SCRIPT, start=1):
        history, usage = run_turn(history, user_text, model=model, via=via)
        usages.append(usage)

        block = [
            "",
            "--- turn %d ---" % i,
            "you: " + user_text,
            "bot: " + usage["text"],
            "     in=%6d  out=%5d  $%.6f"
            % (usage["input_tokens"], usage["output_tokens"], cost_of(usage)),
        ]
        for line in block:
            print(line)
        lines.extend(block)

    table = ["", "%10s%8s%7s%12s" % ("", "in", "out", "cost")]
    for i, u in enumerate(usages, start=1):
        table.append("turn %-5d%8d%7d%12.6f"
                     % (i, u["input_tokens"], u["output_tokens"], cost_of(u)))
    table.append("%25s%s" % ("", "-" * 12))
    table.append("%25s%12.6f" % ("total", conversation_cost(usages)))

    for line in table:
        print(line)
    lines.extend(table)

    if out_file is not None:
        out_file.write_text("\n".join(lines), encoding="utf-8")
        print("\nSaved to", out_file)

    return usages


if __name__ == "__main__":
    import argparse

    if any(t.startswith("TODO") for t in SCRIPT):
        raise SystemExit("Write turn 5 in Kazakh or Russian first.")

    parser = argparse.ArgumentParser()
    parser.add_argument(
        "mode", choices=["paid", "free"],
        help="'paid' runs gpt-5.6-luna via OpenAI, saves to results_paid.txt. "
             "'free' runs llama-3.3-70b-versatile via Groq (instructor-"
             "approved substitute for the OpenRouter free model), saves to "
             "results_free.txt."
    )
    args = parser.parse_args()

    HERE = Path(__file__).resolve().parent

    if args.mode == "paid":
        run_script("gpt-5.6-luna", "openai", out_file=HERE / "results_paid.txt")
    else:
        run_script("openai/gpt-oss-120b", "groq",
                   out_file=HERE / "results_free.txt")