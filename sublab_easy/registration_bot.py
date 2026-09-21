"""Sublab Easy - a course-registration chatbot, and the bill it runs up."""

import json
import os
from pathlib import Path

from dotenv import load_dotenv
from openai import OpenAI


load_dotenv()


OPENROUTER_BASE_URL = "https://openrouter.ai/api/v1"

CATALOGUE = (
    Path(__file__).resolve().parent.parent
    / "data"
    / "courses.json"
)


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
}


def load_catalogue() -> dict:
    """Load course catalogue."""

    return json.loads(
        CATALOGUE.read_text(encoding="utf-8")
    )


# ----------------------------------------------------------
# API clients
# ----------------------------------------------------------

def openai_client() -> OpenAI:
    """Create OpenAI client."""

    key = os.environ.get("OPENAI_API_KEY")

    if not key:
        raise RuntimeError(
            "OPENAI_API_KEY is not set. "
            "Copy .env.example to .env."
        )

    return OpenAI(api_key=key)


def openrouter_client() -> OpenAI:
    """Create OpenRouter client."""

    key = os.environ.get("OPENROUTER_API_KEY")

    if not key:
        raise RuntimeError(
            "OPENROUTER_API_KEY is not set. "
            "Copy .env.example to .env."
        )

    return OpenAI(
        api_key=key,
        base_url=OPENROUTER_BASE_URL,
    )


def client_for(via: str) -> OpenAI:
    """Return client for selected provider."""

    if via == "openai":
        return openai_client()

    if via == "openrouter":
        return openrouter_client()

    raise ValueError(
        'via must be "openai" or "openrouter", got '
        + repr(via)
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

    # Student information
    lines.append("STUDENT")
    lines.append(
        "Student ID: " + student["student_id"]
    )
    lines.append(
        "Year: " + str(student["year"])
    )
    lines.append(
        "Programme: " + student["programme"]
    )
    lines.append(
        "Already completed courses: "
        + ", ".join(student["completed"])
    )

    lines.append("")

    # Registration rules
    lines.append("REGISTRATION RULES")
    lines.append(
        "Maximum credits per term: "
        + str(rules["max_credits"])
    )
    lines.append(
        "Minimum credits per term: "
        + str(rules["min_credits"])
    )
    lines.append(rules["note"])

    lines.append("")

    # Course catalogue
    lines.append("COURSE CATALOGUE")

    for c in courses:

        seats_left = (
            c["seats_total"]
            - c["seats_taken"]
        )

        schedule_str = "; ".join(
            "%s %s-%s"
            % (
                s["day"],
                s["start"],
                s["end"],
            )
            for s in c["schedule"]
        )

        if c["prerequisites"]:
            prereq_str = ", ".join(
                c["prerequisites"]
            )
        else:
            prereq_str = "none"

        lines.append(
            "%s | %s | %d credits | "
            "prerequisites: %s | "
            "schedule: %s | "
            "seats: %d/%d (remaining: %d) | "
            "instructor: %s"
            % (
                c["code"],
                c["title"],
                c["credits"],
                prereq_str,
                schedule_str,
                c["seats_taken"],
                c["seats_total"],
                seats_left,
                c["instructor"],
            )
        )

    lines.append("")

    # Strict rules
    lines.append("STRICT RULES YOU MUST FOLLOW")

    lines.append(
        "1. The catalogue above is the ONLY source of truth. "
        "Never invent a course, code, credit count, instructor, "
        "or schedule that is not listed above."
    )

    lines.append(
        "2. If a student asks about a course code that does not "
        "appear in the catalogue, you MUST refuse and clearly "
        "state that no such course exists in the catalogue. "
        "Do not guess details for it under any circumstances."
    )

    lines.append(
        "3. Before registering a student for any course, check "
        "ALL of the following: "
        "(a) prerequisites are in their completed list, "
        "(b) the course has remaining seats, "
        "(c) the student has not already completed it, "
        "(d) it does not have a schedule conflict "
        "(overlapping day and time) with any other course "
        "the student is registering for in this conversation."
    )

    lines.append(
        "4. If two requested courses share the same day and "
        "overlapping time, refuse to register both and explain "
        "the conflict explicitly, naming both courses and the "
        "overlapping time."
    )

    lines.append(
        "5. Always show your reasoning for prerequisite, seat, "
        "and schedule checks when registering or refusing a course."
    )

    return "\n".join(lines)


# ----------------------------------------------------------
# One API call
# ----------------------------------------------------------

def chat(
    messages: list[dict],
    model: str = "gpt-5.6-luna",
    via: str = "openai",
    max_tokens: int | None = None,
) -> dict:
    """
    Send messages to a model.

    max_tokens is optional.
    If it is None, no output-token limit is explicitly sent.
    """

    client = client_for(via)

    request = {
        "model": model,
        "messages": messages,
    }

    # IMPORTANT:
    # Only send max_tokens when we explicitly provide it.
    if max_tokens is not None:
        request["max_tokens"] = max_tokens

    response = client.chat.completions.create(
        **request
    )

    return {
        "text": response.choices[0].message.content,
        "input_tokens": response.usage.prompt_tokens,
        "output_tokens": response.usage.completion_tokens,
        "model": model,
    }


def ask_once(
    prompt: str,
    model: str = "gpt-5.6-luna",
    via: str = "openai",
    max_tokens: int | None = None,
) -> dict:
    """Make one request without conversation history."""

    return chat(
        [
            {
                "role": "user",
                "content": prompt,
            }
        ],
        model=model,
        via=via,
        max_tokens=max_tokens,
    )


# ----------------------------------------------------------
# Conversation
# ----------------------------------------------------------

def new_conversation(
    catalogue: dict,
) -> list[dict]:
    """Create new conversation."""

    return [
        {
            "role": "system",
            "content": build_system_prompt(
                catalogue
            ),
        }
    ]


def run_turn(
    history: list[dict],
    user_text: str,
    model: str = "gpt-5.6-luna",
    via: str = "openai",
) -> tuple[list[dict], dict]:
    """Run one conversation turn."""

    history = history + [
        {
            "role": "user",
            "content": user_text,
        }
    ]

    reply = chat(
        history,
        model=model,
        via=via,
    )

    history = history + [
        {
            "role": "assistant",
            "content": reply["text"],
        }
    ]

    return history, reply


# ----------------------------------------------------------
# Cost
# ----------------------------------------------------------

def estimate_cost(
    input_tokens: int,
    output_tokens: int,
    rate_in: float,
    rate_out: float,
) -> float:
    """Calculate API call cost."""

    return (
        (input_tokens / 1_000_000) * rate_in
        + (output_tokens / 1_000_000) * rate_out
    )


def cost_of(usage: dict) -> float:
    """Calculate cost of one result."""

    rate_in, rate_out = RATES_PER_MTOK[
        usage["model"]
    ]

    return estimate_cost(
        usage["input_tokens"],
        usage["output_tokens"],
        rate_in,
        rate_out,
    )


def conversation_cost(
    usages: list[dict],
) -> float:
    """Calculate total conversation cost."""

    return sum(
        cost_of(u)
        for u in usages
    )


# ----------------------------------------------------------
# Easy assignment script
# ----------------------------------------------------------

SCRIPT = [
    "I am a third-year student. "
    "Which courses am I still eligible to register for?",

    "Register me for CSS-4007 and CSS-4102.",

    "How many credits would that be in total, "
    "and am I within the limit?",

    "Add CSS-4090 Quantum Machine Learning "
    "to my schedule.",

    "Я студент третьего курса. "
    "На какие курсы я ещё могу записаться?",
]


def run_script(
    model: str,
    via: str,
) -> list[dict]:
    """Run five scripted conversation turns."""

    history = new_conversation(
        load_catalogue()
    )

    usages = []

    print(
        "\n===== "
        + via
        + " / "
        + model
        + " ====="
    )

    for i, user_text in enumerate(
        SCRIPT,
        start=1,
    ):

        history, usage = run_turn(
            history,
            user_text,
            model=model,
            via=via,
        )

        usages.append(usage)

        print(
            "\n--- turn %d ---"
            % i
        )

        print(
            "you: " + user_text
        )

        print(
            "bot: " + usage["text"]
        )

        print(
            "     in=%6d  out=%5d  $%.6f"
            % (
                usage["input_tokens"],
                usage["output_tokens"],
                cost_of(usage),
            )
        )

    print(
        "\n%10s%8s%7s%12s"
        % (
            "",
            "in",
            "out",
            "cost",
        )
    )

    for i, u in enumerate(
        usages,
        start=1,
    ):

        print(
            "turn %-5d%8d%7d%12.6f"
            % (
                i,
                u["input_tokens"],
                u["output_tokens"],
                cost_of(u),
            )
        )

    print(
        "%25s%s"
        % (
            "",
            "-" * 12,
        )
    )

    print(
        "%25s%12.6f"
        % (
            "total",
            conversation_cost(usages),
        )
    )

    return usages


if __name__ == "__main__":

    if any(
        t.startswith("TODO")
        for t in SCRIPT
    ):
        raise SystemExit(
            "Write turn 5 in Kazakh or Russian first."
        )

    # Already ran successfully.
    # Keep commented to save credits.
    #
    # run_script(
    #     "gpt-5.6-luna",
    #     "openai"
    # )

    run_script(
        "google/gemma-4-26b-a4b-it:free",
        "openrouter",
    )