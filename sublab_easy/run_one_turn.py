"""Run ONE turn of the OpenRouter free-model script at a time.

Why this exists: the free model's rate limit is shared across every student
running this assignment right now, so a full 5-turn run can fail partway
through. This script remembers where you left off (in history_openrouter.json)
and appends each successful turn's transcript and token counts to
results_openrouter.txt. Just run it again and again until all 5 turns are done.
"""

import json
from pathlib import Path

from openai import RateLimitError

from registration_bot import (
    SCRIPT, load_catalogue, new_conversation, run_turn, cost_of,
)

HISTORY_FILE = Path(__file__).resolve().parent / "history_openrouter.json"
RESULTS_FILE = Path(__file__).resolve().parent / "results_openrouter.txt"

MODEL = "google/gemma-4-26b-a4b-it:free"
VIA = "openrouter"


def load_state():
    """Return (history, turns_done) from disk, or a fresh start."""
    if HISTORY_FILE.exists():
        data = json.loads(HISTORY_FILE.read_text(encoding="utf-8"))
        return data["history"], data["turns_done"]
    history = new_conversation(load_catalogue())
    return history, 0


def save_state(history, turns_done):
    HISTORY_FILE.write_text(
        json.dumps({"history": history, "turns_done": turns_done},
                   ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


def append_result(turn_number, user_text, usage):
    with RESULTS_FILE.open("a", encoding="utf-8") as f:
        f.write("\n--- turn %d ---\n" % turn_number)
        f.write("you: " + user_text + "\n")
        f.write("bot: " + usage["text"] + "\n")
        f.write("     in=%6d  out=%5d  $%.6f\n"
                 % (usage["input_tokens"], usage["output_tokens"], cost_of(usage)))


def main():
    history, turns_done = load_state()

    if turns_done >= len(SCRIPT):
        print("All %d turns already done. See %s" % (len(SCRIPT), RESULTS_FILE))
        return

    next_turn_text = SCRIPT[turns_done]
    turn_number = turns_done + 1

    print("Attempting turn %d / %d ..." % (turn_number, len(SCRIPT)))
    print("you: " + next_turn_text)

    try:
        history, usage = run_turn(history, next_turn_text, model=MODEL, via=VIA)
    except RateLimitError:
        print("Still rate-limited. Nothing saved. Just run this script again later.")
        return

    turns_done += 1
    save_state(history, turns_done)
    append_result(turn_number, next_turn_text, usage)

    print("bot: " + usage["text"])
    print("     in=%6d  out=%5d  $%.6f"
          % (usage["input_tokens"], usage["output_tokens"], cost_of(usage)))
    print("\nSaved turn %d to %s" % (turn_number, RESULTS_FILE))

    if turns_done == len(SCRIPT):
        print("\nAll 5 turns complete! See", RESULTS_FILE)
    else:
        print("Run this script again for turn %d." % (turns_done + 1))


if __name__ == "__main__":
    main()