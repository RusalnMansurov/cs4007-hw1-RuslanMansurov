# HW1 submission

**Name:** Ruslan Mansurov  
**Student ID:**  S23068624
**Group:**  ENG-8
**Repository:** cs4007-hw1-RuslanMansurov

## AI tool disclosure

I used ChatGPT to help understand the assignment, debug Python code, explain API errors, and help structure the final report. I ran the code and experiments myself and used the actual outputs from my runs in the tables below.

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

### Run 2 — OpenRouter, `google/gemma-4-26b-a4b-it:free`

| Turn | Input tokens | Output tokens | Cost $ |
|---|---:|---:|---:|
| 1 | NOT RECORDED | NOT RECORDED | 0 |
| 2 | NOT RECORDED | NOT RECORDED | 0 |
| 3 | NOT RECORDED | NOT RECORDED | 0 |
| 4 | NOT RECORDED | NOT RECORDED | 0 |
| 5 | NOT RECORDED | NOT RECORDED | 0 |
| **total** | **NOT RECORDED** | **NOT RECORDED** | **0** |

### Turn 4, verbatim

The turn where I asked for CSS-4090, which does not exist.

**OpenAI:**

```text
I cannot add **CSS-4090 Quantum Machine Learning** because it does not appear in the Narxoz University 2026-FALL course catalogue provided. Its credits, prerequisites, seats, and schedule cannot be verified, so it cannot be registered.
```

**OpenRouter:**

```text
NOT RECORDED
```

### Written answers

**1. The two providers used almost identical code. What actually changed, and what did not?**

The Python client and message format stayed almost the same. Both providers use the OpenAI-compatible chat format.

The main differences were the API key and base URL. OpenAI used `OPENAI_API_KEY`, while OpenRouter used `OPENROUTER_API_KEY` and `https://openrouter.ai/api/v1`.

**2. Why did the input token count climb on every turn when your questions stayed roughly the same length? Use the numbers from your own table. What happens to the bill at fifty turns?**

The complete conversation history is sent again on every request. Because of this, the input increased from 804 tokens on turn 1 to 1454 tokens on turn 5.

With many more turns, for example 50, the conversation history would become much larger and the later requests would cost more because they would repeatedly include previous messages.

**3. Turn 4: did the bot refuse, or did it invent CSS-4090? If it refused, what in your system prompt held the line?**

GPT-5.6 Luna refused to add CSS-4090. It did not invent credits, schedule or an instructor.

The system prompt explicitly said that the catalogue was the only source of truth and that the model must refuse course codes that do not appear in it.

**4. Where else was either bot wrong? Turn 2 asks for two courses that meet at the same hour; two courses in the catalogue are full. Did the bots notice?**

GPT-5.6 Luna correctly noticed that CSS-4007 and CSS-4102 conflict on Tuesday from 09:00 to 10:50 and refused to register both together.

It also noticed full courses when listing available courses. For example, it reported CSS-4400 as full. The OpenRouter run was not recorded, so I cannot make the same claim about that run from my saved results.

---

## Sublab Medium — one task, six models

| Model | Exact | Failed | Tokens | Cost $ |
|---|---:|---:|---:|---:|
| google/gemma-4-26b-a4b-it:free | NOT RECORDED | NOT RECORDED | NOT RECORDED | 0 |
| qwen/qwen3.8-27b | 1 usable exact | 5 on retry | partial run | partial run |
| deepseek/deepseek-v4-flash-0731 | 4/8 | 0 | 26,584 | 0.00725 |
| gpt-5.6-luna | 2/8 | 0 | 2,968 | 0.00278 |
| gpt-5.6-terra | 2/8 | 0 | 2,216 | 0.01882 |
| gpt-5.6-sol | 4/8 | 0 | 2,148 | 0.04501 |

Qwen did not complete a clean eight-sentence run. The first run failed because OpenRouter returned HTTP 402. After limiting the request, KZ-03, KZ-04 and KZ-08 returned usable answers, while five requests returned empty content.

### Which error types did each model repair?

Rows are error labels, columns are models.

| Error type | gemma | qwen | deepseek | luna | terra | sol |
|---|---|---|---|---|---|---|
| kaz_to_rus | not recorded | partial | yes | partial | partial | partial |
| latin_homoglyph | not recorded | yes | yes | yes | yes | yes |
| drop_hyphen | not recorded | not recorded | yes | partial | partial | yes |
| join_words | not recorded | not recorded | yes | yes | yes | yes |
| double_letter | not recorded | yes | yes | yes | yes | yes |

**The `latin_homoglyph` row: what happened?**

The models generally understood what the corrupted words were supposed to be. In KZ-03, Qwen correctly changed the mixed Latin/Cyrillic word to `Алаяқтарға`, but it also added a question mark. Because of this the answer was good Kazakh but was not an exact match.

In KZ-08, Qwen correctly replaced the Latin characters and removed the doubled letter, producing an exact match.

**Where a model returned good Kazakh that was not identical to the original, say so here. Exact match is not correctness.**

This happened several times. Models often fixed the intended spelling error correctly but added punctuation such as `?` or `.`.

For example, Qwen returned:

`Елде жалған дипломдар үшін қандай жаза қарастырылған?`

The correction itself is good, but the expected answer had no question mark. Therefore it received `exact = false` with `char_diff = 1`.

Some models also made extra grammatical changes, such as changing `елшісінен` to `елшілерінен`.

**Cheapest model that was good enough, and why:**

Among my complete paid runs, GPT-5.6 Luna was the cheapest at about **$0.00278**. It only had 2/8 strict exact matches, but several non-exact answers still fixed the intended Kazakh errors and differed mainly because of punctuation.

DeepSeek produced more exact matches, 4/8, for about **$0.00725**, so it was also relatively inexpensive compared with GPT-5.6 Sol.

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

So the Kazakh token ratio improved from 0.760 to 0.319 tokens per character. The gap became much smaller with the newer tokenizer.

**2. Why did the models repair `kaz_to_rus` but struggle with `latin_homoglyph`? Both are single-letter substitutions and both look almost identical on screen. Use your token streams from B as the evidence. Say what the model actually received in each case.**

A Latin homoglyph may look almost identical to a Cyrillic letter, but it is a different Unicode character. Because of this, the tokenizer can split the word differently.

For KZ-03, the correct sentence used 16 tokens, while the corrupted sentence used 20. The correct beginning was tokenized as:

`['А', 'лая', 'қ', 'тарға', ' ақша']`

but the corrupted version started as:

`['A', 'л', 'a', 'я', 'қ']`.

So the model did not receive the same word with a small visual typo. It received a different and more fragmented token sequence.

KZ-08 showed the same effect: the correct sentence used 21 tokens and the corrupted version used 24.

This helps explain why mixed Latin/Cyrillic text can be harder to process. For `kaz_to_rus`, the characters are still Cyrillic and may stay closer to patterns the tokenizer/model already knows, while Latin homoglyphs can break those patterns.

**3. Name one thing this measurement does not explain about your Sublab Medium results. You measured OpenAI's tokenizers; three of your six models were not OpenAI's. What follows, and what would you have to do to close the gap?**

This experiment only measured `cl100k_base` and `o200k_base`, which are OpenAI tokenizers.

Gemma, Qwen and DeepSeek may use different tokenizers. Therefore, I cannot assume that the same Kazakh and homoglyph tokenization results apply to those models.

To make the comparison complete, I would need to use the real tokenizer for each non-OpenAI model and run the same Kazakh, Russian, English and homoglyph tests on them.