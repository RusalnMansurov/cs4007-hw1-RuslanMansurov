"""Sublab Harder - why Kazakh costs more, and what a homoglyph does to a word."""

import json
import unicodedata
from pathlib import Path

import tiktoken


DATA = Path(__file__).resolve().parent.parent / "data"
PARALLEL = DATA / "parallel.json"
KAZAKH_ERRORS = DATA / "kazakh_errors.json"

ENCODINGS = ["cl100k_base", "o200k_base"]
LANGS = ["kk", "ru", "en"]


def load_triplets() -> list[dict]:
    """Six meanings, each written in Kazakh, Russian and English."""

    return json.loads(
        PARALLEL.read_text(encoding="utf-8")
    )["triplets"]


def load_sentences() -> list[dict]:
    """The corrupted Kazakh sentences from Sublab Medium."""

    return json.loads(
        KAZAKH_ERRORS.read_text(encoding="utf-8")
    )["sentences"]


# --------------------------------------------------------------------------
# The tokenizer itself
# --------------------------------------------------------------------------

def encode(
    text: str,
    encoding_name: str = "o200k_base"
) -> list[int]:
    """Return token IDs for text."""

    encoding = tiktoken.get_encoding(encoding_name)

    return encoding.encode(text)


def pieces(
    ids: list[int],
    encoding_name: str = "o200k_base"
) -> list[str]:
    """Return the text represented by each individual token."""

    encoding = tiktoken.get_encoding(encoding_name)

    result = []

    for token_id in ids:
        token_bytes = encoding.decode_single_token_bytes(token_id)

        result.append(
            token_bytes.decode(
                "utf-8",
                errors="replace"
            )
        )

    return result


# --------------------------------------------------------------------------
# Pure measurements
# --------------------------------------------------------------------------

def tokens_per_char(
    text: str,
    ids: list[int]
) -> float:
    """Return number of tokens per character."""

    if len(text) == 0:
        return 0.0

    return len(ids) / len(text)


def first_divergence(
    a: list[int],
    b: list[int]
) -> int | None:
    """Return index of first different token."""

    common_length = min(
        len(a),
        len(b)
    )

    for i in range(common_length):
        if a[i] != b[i]:
            return i

    if len(a) != len(b):
        return common_length

    return None


def foreign_chars(
    text: str
) -> list[tuple[int, str, str]]:
    """Find letters that are not Cyrillic."""

    result = []

    for index, ch in enumerate(text):

        # Ignore spaces, digits and punctuation.
        if not ch.isalpha():
            continue

        name = unicodedata.name(
            ch,
            "UNKNOWN"
        )

        if "CYRILLIC" not in name:
            result.append(
                (
                    index,
                    ch,
                    name,
                )
            )

    return result


# --------------------------------------------------------------------------
# A. The price of a language
# --------------------------------------------------------------------------

def language_table(
    encoding_name: str
) -> dict[str, dict]:
    """Calculate token statistics for each language."""

    triplets = load_triplets()

    result = {}

    for lang in LANGS:

        total_tokens = 0
        total_chars = 0

        for row in triplets:

            text = row[lang]

            ids = encode(
                text,
                encoding_name
            )

            total_tokens += len(ids)
            total_chars += len(text)

        if total_chars == 0:
            ratio = 0.0
        else:
            ratio = (
                total_tokens
                / total_chars
            )

        result[lang] = {
            "tokens": total_tokens,
            "chars": total_chars,
            "tok_per_char": ratio,
        }

    return result


def cost_per_thousand(
    tok_per_char: float,
    chars: int,
    rate_in: float = 5.00
) -> float:
    """Calculate input cost for 1,000 sentences."""

    tokens_per_sentence = (
        tok_per_char * chars
    )

    total_tokens = (
        tokens_per_sentence * 1000
    )

    return (
        total_tokens
        / 1_000_000
    ) * rate_in


# --------------------------------------------------------------------------
# B. What the homoglyph did
# --------------------------------------------------------------------------

def homoglyph_report(
    corrupted: str,
    correct: str,
    encoding_name: str = "o200k_base"
) -> dict:
    """Compare correct and corrupted token streams."""

    correct_ids = encode(
        correct,
        encoding_name
    )

    corrupted_ids = encode(
        corrupted,
        encoding_name
    )

    return {
        "foreign": foreign_chars(
            corrupted
        ),

        "tokens_correct": len(
            correct_ids
        ),

        "tokens_corrupted": len(
            corrupted_ids
        ),

        "delta": (
            len(corrupted_ids)
            - len(correct_ids)
        ),

        "diverge_at": first_divergence(
            correct_ids,
            corrupted_ids
        ),

        "pieces_correct": pieces(
            correct_ids,
            encoding_name
        ),

        "pieces_corrupted": pieces(
            corrupted_ids,
            encoding_name
        ),
    }


def show_homoglyphs(
    encoding_name: str = "o200k_base"
) -> None:
    """Print report for latin_homoglyph rows."""

    rows = [
        r
        for r in load_sentences()
        if "latin_homoglyph" in r["errors"]
    ]

    if not rows:
        print(
            "  no latin_homoglyph rows "
            "in the dataset"
        )
        return

    for row in rows:

        rep = homoglyph_report(
            row["corrupted"],
            row["correct"],
            encoding_name
        )

        print(
            "\n  [%s]  %+d tokens (%d -> %d), "
            "diverging at index %s"
            % (
                row["id"],
                rep["delta"],
                rep["tokens_correct"],
                rep["tokens_corrupted"],
                rep["diverge_at"],
            )
        )

        for idx, ch, name in rep["foreign"]:

            print(
                "    char %d is %r - %s"
                % (
                    idx,
                    ch,
                    name,
                )
            )

        d = rep["diverge_at"] or 0

        print(
            "    correct  : %s"
            % rep["pieces_correct"][
                max(0, d - 1):d + 5
            ]
        )

        print(
            "    corrupted: %s"
            % rep["pieces_corrupted"][
                max(0, d - 1):d + 5
            ]
        )


# --------------------------------------------------------------------------
# Main
# --------------------------------------------------------------------------

if __name__ == "__main__":

    print(
        "=== A. the same six meanings, "
        "three languages, two tokenizers ==="
    )

    for enc_name in ENCODINGS:

        table = language_table(
            enc_name
        )

        print(
            "\n  %s"
            % enc_name
        )

        print(
            "    %-4s %8s %8s %12s"
            % (
                "lang",
                "tokens",
                "chars",
                "tok/char",
            )
        )

        for lang in LANGS:

            row = table[lang]

            print(
                "    %-4s %8d %8d %12.3f"
                % (
                    lang,
                    row["tokens"],
                    row["chars"],
                    row["tok_per_char"],
                )
            )

        base = table["en"][
            "tok_per_char"
        ]

        for lang in LANGS:

            print(
                "    %s costs %.2fx English"
                % (
                    lang,
                    table[lang][
                        "tok_per_char"
                    ] / base,
                )
            )

    print(
        "\n=== B. what a Latin homoglyph "
        "does to the token stream ==="
    )

    show_homoglyphs(
        "o200k_base"
    )

    print(
        "\n=== C. did the newer tokenizer "
        "narrow the gap? ==="
    )

    old, new = (
        language_table(e)
        for e in ENCODINGS
    )

    for lang in LANGS:

        print(
            "  %s: %.3f -> %.3f tok/char"
            % (
                lang,
                old[lang]["tok_per_char"],
                new[lang]["tok_per_char"],
            )
        )

    print(
        "\n  Now answer question 2 in "
        "SUBMISSION.md, with these numbers in hand."
    )