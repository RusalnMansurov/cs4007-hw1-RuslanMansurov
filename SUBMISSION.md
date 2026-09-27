# HW1 submission

**Name:** Ruslan Mansurov  
**Student ID:** S23068624
**Group:** ENG-8
**Repository:** cs4007-hw1-RuslanMansurov

## AI tool disclosure

I used ChatGPT to help understand the assignment, debug Python code, explain API errors, and help structure the final report. I ran the code and experiments myself and used the actual outputs from my runs in the tables below.

## Note on a model substitution (instructor-approved)

The assignment specifies `google/gemma-4-26b-a4b-it:free` via OpenRouter as the free model for both Sublab Easy and Sublab Medium. That model's free tier uses a rate limit shared across every student running this assignment at the same time, and it was consistently unavailable (HTTP 429, "rate-limited upstream") even after multiple retries spread over more than an hour, including a personally-linked Google AI Studio key (which returned HTTP 403, permission denied - likely a regional restriction on the Generative Language API).

The instructor approved using an alternative free model. I used **`openai/gpt-oss-120b` via Groq**, which has its own personal (non-shared) free-tier rate limit, for both Sublab Easy Run 2 and the free-model row in Sublab Medium. This is noted again at each relevant table below.

---

## Sublab Easy — the registration bot and its bill

**How I laid the catalogue out inside the system prompt, and why:**

I used one line for each course. Each line contains the course code, title, credits, prerequisites, schedule, seats and instructor. I chose this format because it is simple and gives the model all important information without making the prompt too complicated.

I also added strict rules telling the model to check prerequisites, seats and schedule conflicts, and not to invent courses outside the catalogue.

**My turn 5 (Kazakh or Russian):**

> Я студент третьего курса. На какие курсы я ещё могу записаться?

### Run 1 — OpenAI, `gpt-5.6-luna`

| Turn | Input tokens | Output tokens | Cost $ |
|---|---:|---:|---:|
| 1 | 804 | 477 | 0.000733 |
| 2 | 1128 | 220 | 0.000490 |
| 3 | 1287 | 110 | 0.000389 |
| 4 | 1377 | 85 | 0.000377 |
| 5 | 1454 | 525 | 0.000921 |
| **total** | **6050** | **1417** | **0.002910** |

### Run 2 — Groq, `openai/gpt-oss-120b` (substitute for OpenRouter's free model, see note above)

| Turn | Input tokens | Output tokens | Cost $ |
|---|---:|---:|---:|
| 1 | 868 | 1148 | 0.000000 |
| 2 | 1703 | 464 | 0.000000 |
| 3 | 2122 | 401 | 0.000000 |
| 4 | 2450 | 97 | 0.000000 |
| 5 | 2538 | 1056 | 0.000000 |
| **total** | **9681** | **3166** | **0.000000** |

### Turn 4, verbatim

The turn where I asked for CSS-4090, which does not exist.

**OpenAI (`gpt-5.6-luna`):**

```text
I cannot add **CSS-4090 Quantum Machine Learning** because it does not appear in the Narxoz University 2026-FALL course catalogue provided. Its credits, prerequisites, seats, and schedule cannot be verified, so it cannot be registered.
```

**Groq (`openai/gpt-oss-120b`):**

```text
I'm sorry, but **CSS-4090 Quantum Machine Learning** does not exist in the university's course catalogue that I have access to. I cannot register you for a course that is not listed. If you'd like to add a different course from the catalogue, please let me know!
```

### Written answers

**1. The two providers used almost identical code. What actually changed, and what did not?**

The Python client and message format stayed almost the same. All three providers (OpenAI, OpenRouter, Groq) use the OpenAI-compatible chat completions format, so the same client library and the same `chat()`/`ask_once()` functions reached all of them.

The main differences were the API key and the base URL. OpenAI used `OPENAI_API_KEY` with the default OpenAI base URL, OpenRouter used `OPENROUTER_API_KEY` and `https://openrouter.ai/api/v1`, and Groq used `GROQ_API_KEY` and `https://api.groq.com/openai/v1`. Everything else - how messages are built, how the reply and usage are read off the response - stayed identical.

**2. Why did the input token count climb on every turn when your questions stayed roughly the same length? Use the numbers from your own table. What happens to the bill at fifty turns?**

The complete conversation history is sent again on every request. Because of this, the input increased from 804 to 1454 tokens across the OpenAI run, and even more sharply from 868 to 2538 tokens across the Groq run - the free model's answers were longer (it wrote out more detailed tables each turn), so each resend carried a bigger history.

With many more turns, for example 50, the conversation history would keep growing every turn, and since every earlier turn's full text is resent, the input token count - and therefore the cost - would grow roughly linearly or faster with the number of turns, even though each individual question stays short. A long-running conversation with a verbose model would get expensive quickly, purely from resending history rather than from anything new being asked.

**3. Turn 4: did the bot refuse, or did it invent CSS-4090? If it refused, what in your system prompt held the line?**

Both models refused to add CSS-4090. Neither invented credits, a schedule, seats, or an instructor for it.

The system prompt explicitly stated that the catalogue was the only source of truth and instructed the model to refuse course codes that do not appear in it, rather than guessing details. Both gpt-5.6-luna and gpt-oss-120b followed that instruction.

**4. Where else was either bot wrong? Turn 2 asks for two courses that meet at the same hour; two courses in the catalogue are full. Did the bots notice?**

Both models correctly noticed that CSS-4007 and CSS-4102 conflict on Tuesday from 09:00 to 10:50 and refused to register both together. Both also correctly identified CSS-4400 as full (0 seats remaining) when listing eligible courses, and correctly excluded CSS-3011 (also full, and already completed) from the eligible list.

The Groq/gpt-oss-120b run was notably more verbose than OpenAI's gpt-5.6-luna, restating the same conflict and credit-limit reasoning across multiple turns and even proposing next steps like "contact the registrar." But the underlying logic (prerequisites, seats, schedule conflicts) was correct in both runs - I did not find a case where either bot missed a conflict or a full course.

---

## Sublab Medium — one task, six models

| Model | Exact | Failed | Tokens | Cost $ |
|---|---:|---:|---:|---:|
| openai/gpt-oss-120b (via Groq, substitute for google/gemma-4-26b-a4b-it:free - see note above) | 3/8 | 0 | 6,342 | 0.00000 |
| qwen/qwen3.8-27b | 1 usable exact | 5 on retry | partial run | partial run |
| deepseek/deepseek-v4-flash-0731 | 4/8 | 0 | 26,584 | 0.00725 |
| gpt-5.6-luna | 2/8 | 0 | 2,968 | 0.00278 |
| gpt-5.6-terra | 2/8 | 0 | 2,216 | 0.01882 |
| gpt-5.6-sol | 4/8 | 0 | 2,148 | 0.04501 |

Qwen did not complete a clean eight-sentence run. The first run failed because OpenRouter returned HTTP 402 (insufficient credits combined with an unbounded default `max_tokens`). After limiting the request, KZ-03, KZ-04 and KZ-08 returned usable answers, while five requests returned empty content (the model likely spent its entire token budget on internal reasoning before producing a final answer).

### Which error types did each model repair?

Rows are error labels, columns are models.

| Error type | gpt-oss-120b (Groq) | qwen | deepseek | luna | terra | sol |
|---|---|---|---|---|---|---|
| kaz_to_rus | partial | partial | yes | partial | partial | partial |
| latin_homoglyph | yes | yes | yes | yes | yes | yes |
| drop_hyphen | partial | not recorded | yes | partial | partial | yes |
| join_words | partial | not recorded | yes | yes | yes | yes |
| double_letter | partial | yes | yes | yes | yes | yes |

**The `latin_homoglyph` row: what happened?**

Every model that produced an answer correctly identified and fixed the Latin-letter substitutions in both KZ-03 and KZ-08. `gpt-oss-120b` fixed KZ-03's Latin `A`, `l`, `a`, `t` correctly (`Aлaяқtарға` → `Алаяқтарға`), though it also appended a question mark that was not in the original, so the result was good Kazakh but not an exact match (`char_diff = 1`). It fixed KZ-08 exactly, replacing `Дoнaлльд Tрамп` with `Дональд Трамп` and removing the doubled `л`.

Qwen showed the same pattern: it correctly changed the mixed Latin/Cyrillic word to `Алаяқтарға` in KZ-03 but also added a question mark, and produced an exact match on KZ-08.

**Where a model returned good Kazakh that was not identical to the original, say so here. Exact match is not correctness.**

This happened several times across models. A common pattern was fixing the intended spelling error correctly but adding punctuation such as `?` or `.` that was not in the published original - for example, Qwen returned `Елде жалған дипломдар үшін қандай жаза қарастырылған?` for KZ-04, which is a correct fix but not an exact match (`char_diff = 1`) purely because of the added question mark.

`gpt-oss-120b` went further on KZ-01 and KZ-07, making the letters correct but also substituting different (still valid) words - for example replacing `грамоталарын` (credentials) with `хаттарын` (letters) in KZ-01, and `корганужолдары` → `қорғау жолдары` instead of the published `қорғану жолдары` in KZ-07. These are good, natural Kazakh but diverge from the reference wording, which is exactly the "exact match is not correctness" case the assignment warns about.

**Cheapest model that was good enough, and why:**

Among my complete paid runs, GPT-5.6 Luna was the cheapest at about **$0.00278**. It only had 2/8 strict exact matches, but several non-exact answers still fixed the intended Kazakh errors and differed mainly because of punctuation or minor rewording, not because the correction was wrong.

DeepSeek produced more exact matches (4/8) for about **$0.00725**, still relatively inexpensive compared with GPT-5.6 Sol's $0.04501 for the same 4/8 exact-match rate. If exact string matching genuinely mattered, DeepSeek would be the better value; if "good Kazakh, punctuation aside" is the bar, GPT-5.6 Luna is cheaper and adequate.

---

## Sublab Harder — open the tokenizer

### A. What a language costs

The dollar values below use the default input rate of **$5 per million tokens** and the average sentence length of the six sentences.

**`cl100k_base`:**

| Language | Tokens | Chars | Tok/char | × English | $ per 1,000 sentences |
|---|---:|---:|---:|---:|---:|
| kk | 200 | 263 | 0.760 | 3.75 | 0.1667 |
| ru | 129 | 277 | 0.466 | 2.30 | 0.1075 |
| en | 59 | 291 | 0.203 | 1.00 | 0.0492 |

**`o200k_base`:**

| Language | Tokens | Chars | Tok/char | × English | $ per 1,000 sentences |
|---|---:|---:|---:|---:|---:|
| kk | 84 | 263 | 0.319 | 1.58 | 0.0700 |
| ru | 74 | 277 | 0.267 | 1.32 | 0.0617 |
| en | 59 | 291 | 0.203 | 1.00 | 0.0492 |

### B. What a homoglyph does

| Sentence id | Foreign char (index, name) | Tokens correct | Tokens corrupted | Δ | Diverges at |
|---|---|---:|---:|---:|---:|
| KZ-03 | 0 `A` LATIN CAPITAL LETTER A; 2 `a` LATIN SMALL LETTER A; 5 `t` LATIN SMALL LETTER T | 16 | 20 | +4 | 0 |
| KZ-08 | 1 `o` LATIN SMALL LETTER O; 3 `a` LATIN SMALL LETTER A; 9 `T` LATIN CAPITAL LETTER T | 21 | 24 | +3 | 1 |

**Token pieces around the divergence:**

KZ-03:

```text
correct  : ['А', 'лая', 'қ', 'тарға', ' ақша']
corrupted: ['A', 'л', 'a', 'я', 'қ']
```

KZ-08:

```text
correct  : ['Д', 'он', 'аль', 'д', ' Т', 'рамп']
corrupted: ['Д', 'o', 'н', 'a', 'л', 'ль']
```

### C. Did it get better?

| Language | cl100k_base | o200k_base | Change |
|---|---:|---:|---:|
| kk | 0.760 | 0.319 | -0.441 |
| ru | 0.466 | 0.267 | -0.199 |
| en | 0.203 | 0.203 | 0.000 |

### Written answers

**1. What is the Kazakh tax? The ratio against English in both encodings, the dollar figure from A, and how much it changed between the two tokenizers.**

With `cl100k_base`, Kazakh used **3.75x** as many tokens per character as English. The estimated input cost for 1,000 average Kazakh sentences was about **$0.1667**, compared with about **$0.0492** for English.

With `o200k_base`, Kazakh decreased to **1.58x** English and about **$0.0700** per 1,000 average sentences.

So the Kazakh token ratio improved from 0.760 to 0.319 tokens per character. The gap became much smaller with the newer tokenizer, roughly cutting the "Kazakh tax" multiplier in half (3.75x down to 1.58x), though Kazakh is still noticeably more expensive per sentence than English even with the newer encoding.

**2. Why did the models repair `kaz_to_rus` but struggle with `latin_homoglyph`? Both are single-letter substitutions and both look almost identical on screen. Use your token streams from B as the evidence. Say what the model actually received in each case.**

A Latin homoglyph may look almost identical to a Cyrillic letter on screen, but it is a completely different Unicode character. Because of this, the tokenizer can split the word differently from how it would split the correct Cyrillic version.

For KZ-03, the correct sentence used 16 tokens, while the corrupted sentence used 20. The correct beginning was tokenized as:

`['А', 'лая', 'қ', 'тарға', ' ақша']`

but the corrupted version started as:

`['A', 'л', 'a', 'я', 'қ']`.

So the model did not receive "the same word with a small visual typo" the way a human reader sees it. It received a different and more fragmented token sequence right from the first token - the divergence starts at position 0. The model has to recognize a token pattern it has effectively never seen in Kazakh training data (Latin `A` followed by Kazakh letters), rather than a familiar misspelling.

KZ-08 showed the same effect: the correct sentence used 21 tokens and the corrupted version used 24, diverging at token position 1.

This helps explain why mixed Latin/Cyrillic text can be harder to process than a same-alphabet substitution. For `kaz_to_rus`, the corrupted characters are still Cyrillic letters that exist in the same script the model was trained on extensively (via Russian text), so the tokenizer produces recognizable token patterns even if the specific Kazakh letter is wrong. For `latin_homoglyph`, the substituted characters are visually similar but come from an entirely different Unicode block, which breaks the tokenizer's pattern matching and gives the model a genuinely unfamiliar sequence to work from - not just a "typo" in the way a human would perceive it.

**3. Name one thing this measurement does not explain about your Sublab Medium results. You measured OpenAI's tokenizers; three of your six models were not OpenAI's. What follows, and what would you have to do to close the gap?**

This experiment only measured `cl100k_base` and `o200k_base`, which are OpenAI's tokenizers.

Gemma (and its Groq substitute, gpt-oss-120b), Qwen, and DeepSeek almost certainly use different tokenizers with different vocabularies, since they come from different model families. Therefore, I cannot assume the same token counts, divergence points, or "Kazakh tax" ratios apply to those models - a homoglyph that fragments badly under `cl100k_base` might tokenize more (or less) gracefully under, say, Qwen's tokenizer, and that would directly affect how well that model can recognize and repair the corruption.

To make the comparison complete, I would need to obtain or load the actual tokenizer for each non-OpenAI model (for example via each model's `tokenizer.json` or a library like Hugging Face's `tokenizers`) and re-run the same language-cost and homoglyph-divergence tests from measurements A and B against each one, rather than assuming OpenAI's tokenizer behavior generalizes across model families.