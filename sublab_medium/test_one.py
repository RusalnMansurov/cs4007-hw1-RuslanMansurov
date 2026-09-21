"""Quick sanity check: run ONE sentence through ONE cheap model before
spending money on the full paid run. Prints the raw model text, the parsed
JSON, and the token/cost numbers so you can eyeball that everything works.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from sublab_easy.registration_bot import RATES_PER_MTOK, estimate_cost  # noqa: E402
from correct_kazakh import build_prompt, correct_with, load_sentences, score_correction  # noqa: E402

# Cheapest paid model, to keep this test cheap.
TEST_MODEL = "gpt-5.6-luna"
TEST_VIA = "openai"


def main():
    sentences = load_sentences()
    s = sentences[0]  # just KZ-01

    print("Sentence ID:", s["id"])
    print("Corrupted:  ", s["corrupted"])
    print("Expected:   ", s["correct"])
    print("Error type: ", s["errors"])

    print("\n--- prompt sent to the model ---")
    print(build_prompt(s["corrupted"]))

    print("\n--- calling", TEST_MODEL, "via", TEST_VIA, "---")
    r = correct_with(TEST_MODEL, s["corrupted"], TEST_VIA)

    print("\n--- parsed result ---")
    print("corrected:", r["corrected"])
    print("changes:  ", r["changes"])

    score = score_correction(r["corrected"], s["correct"])
    rate_in, rate_out = RATES_PER_MTOK[TEST_MODEL]
    cost = estimate_cost(r["input_tokens"], r["output_tokens"], rate_in, rate_out)

    print("\n--- score ---")
    print("exact match:", score["exact"])
    print("char_diff:  ", score["char_diff"])
    print("input_tokens:", r["input_tokens"])
    print("output_tokens:", r["output_tokens"])
    print("cost: $%.6f" % cost)


if __name__ == "__main__":
    main()