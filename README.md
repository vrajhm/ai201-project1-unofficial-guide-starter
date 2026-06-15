# The Unofficial Guide — Project 1

A RAG system that answers questions about campus dining using student-generated reviews, forum posts, and unofficial guides. Ask a plain-language question and get a grounded, cited answer.

## Setup

```bash
cd ai201-project1
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env   # add your Groq API key
python app.py          # open http://127.0.0.1:7860
```

---

## Domain

Campus dining — student reviews and unofficial guides covering dining hall wait times, meal plan rules, dietary options, late-night food, and dining app reliability. Official university pages list menus and hours but not which hall has 30-minute lunch lines, whether the housing lottery affects where you can eat, or if the app's wait-time estimates are accurate. Students share this knowledge in scattered Reddit threads, Discord servers, and orientation wikis. This system makes it searchable in one place.

---

## Document Sources

| # | Source | Type | URL or file path |
|---|--------|------|-----------------|
| 1 | r/college dining thread | Forum reviews | `documents/north_hall_reviews.txt` |
| 2 | Yelp + Reddit compilation | Reviews | `documents/south_hall_reviews.txt` |
| 3 | Discord #food channel | Chat logs | `documents/west_village_eats.txt` |
| 4 | Orientation wiki | Guide | `documents/meal_plan_guide.txt` |
| 5 | Housing forum FAQ | FAQ | `documents/housing_dining_faq.txt` |
| 6 | Student survival thread | Forum | `documents/late_night_food.txt` |
| 7 | CS department Discord | Pinned message | `documents/cs_major_food_tips.txt` |
| 8 | App Store + Reddit | Reviews | `documents/dining_app_complaints.txt` |
| 9 | Sustainability club audit | Report | `documents/sustainability_dining.txt` |
| 10 | Student blog repost | Blog | `documents/finals_week_survival.txt` |
| 11 | Orientation mentor handout | Handout | `documents/freshman_dining_mistakes.txt` |

**Ingestion pipeline:** `ingest.py` loads all `.txt` files from `documents/`, strips HTML tags and boilerplate (navigation text, cookie banners, share buttons) via regex, normalizes whitespace, then chunks the cleaned text. Raw text is read as UTF-8; no live scraping is used.

---

## Chunking Strategy

**Chunk size:** 400 characters

**Overlap:** 80 characters

**Why these choices fit your documents:**

My corpus is review-heavy — most documents are 1–3 short paragraphs, not long-form guides. Four hundred characters captures 2–3 sentences of opinion text, which is enough for a single retrievable thought (e.g., one reviewer's take on wait times). I split on paragraph boundaries first to keep reviews intact, then use overlapping fixed windows for paragraphs longer than 400 characters. The 80-character overlap prevents losing context when a key fact spans a chunk boundary.

**Preprocessing before chunking:** HTML tag removal, HTML entity cleanup, boilerplate phrase removal, whitespace normalization.

**Final chunk count:** 34 chunks across 11 documents

### Sample Chunks

**1. Source: `north_hall_reviews.txt`**
> North Hall Dining — Student Reviews (r/college dining thread, Fall 2025) Review by u/coffee_and_code: North Hall has the shortest lunch wait on campus if you go before 11:45. After noon the line wraps around the pasta station and you're looking at 20-25 minutes. The grilled chicken is consistently good; avoid the mystery casserole on Tuesdays.

**2. Source: `housing_dining_faq.txt`**
> Off-campus and housing forum FAQ — dining edition Q: Does the housing lottery affect dining hall access? A: No. Meal plan access is the same regardless of dorm assignment. South Hall is closest to the engineering quad; North Hall is closest to the freshman dorms.

**3. Source: `late_night_food.txt`**
> Late Night Food Options — student survival thread After midnight your options are slim. South Hall late night (Sun-Wed 9pm-12am) serves fries, pizza, and cereal. North Hall closes at 8pm sharp — no exceptions.

**4. Source: `dining_app_complaints.txt`**
> Wait time estimates in the app launched in 2024 but are unreliable. North Hall showed "5 minutes" during a 30-minute line according to a viral tweet from a sophomore. Push notifications for "your favorite station" require creating an account separate from the campus SSO.

**5. Source: `meal_plan_guide.txt`**
> The housing lottery does NOT affect which dining hall you can use. Any student on a meal plan can eat at North, South, or the satellite locations. Only West Village requires dining dollars for most vendors.

---

## Embedding Model

**Model used:** `all-MiniLM-L6-v2` via sentence-transformers (runs locally, no API key required)

**Production tradeoff reflection:** For a production deployment with no cost constraint, I would evaluate: (1) **domain-specific accuracy** — larger models like `e5-large-v2` may better match informal student language and slang; (2) **multilingual support** — a campus with many international students might need `multilingual-e5`; (3) **context length** — longer syllabi or housing contracts would need models supporting more tokens per input; (4) **latency** — API-hosted embeddings (OpenAI, Cohere) offer faster GPU inference at scale but add per-query cost; (5) **local vs. hosted** — local models avoid data-privacy concerns for sensitive student posts. MiniLM is the right tradeoff for this prototype: fast on CPU, free, and sufficient for short English reviews.

### Retrieval Test Results

**Query 1: "Which dining hall has the shortest lunch wait?"**

| Rank | Source | Distance | Snippet |
|------|--------|----------|---------|
| 1 | `north_hall_reviews.txt` | 0.637 | "North Hall has the shortest lunch wait on campus if you go before 11:45…" |
| 2 | `south_hall_reviews.txt` | 0.801 | "Lunch at South is faster than North according to multiple posts, averaging 10-15 minutes…" |
| 3 | `housing_dining_faq.txt` | 0.871 | Break schedule fragment (off-topic) |

**Why relevant:** The top two chunks directly discuss lunch wait times at North and South Hall. The #1 result is the best match — it explicitly says North has the shortest wait before 11:45.

**Query 2: "Does the housing lottery affect dining hall access?"**

| Rank | Source | Distance | Snippet |
|------|--------|----------|---------|
| 1 | `housing_dining_faq.txt` | 0.517 | "Q: Does the housing lottery affect dining hall access? A: No." |
| 2 | `housing_dining_faq.txt` | 0.666 | Spring break schedule fragment |
| 3 | `meal_plan_guide.txt` | 0.888 | "The housing lottery does NOT affect which dining hall you can use." |

**Why relevant:** The top result is an exact FAQ match — the question and answer appear verbatim. The #3 result reinforces the same fact from a different document.

**Query 3: "What are the late-night food options?"**

| Rank | Source | Distance | Snippet |
|------|--------|----------|---------|
| 1 | `late_night_food.txt` | 0.847 | "South Hall late night (Sun-Wed 9pm-12am) serves fries, pizza, and cereal." |
| 2 | `north_hall_reviews.txt` | 0.984 | Breakfast/lunch review (loosely related) |
| 3 | `freshman_dining_mistakes.txt` | 1.000 | Thursday international night warning (off-topic) |

**Why relevant:** The #1 chunk is from the dedicated late-night food document and lists specific options and hours. Results #2 and #3 are weaker matches with distances near 1.0, showing the system correctly ranks the dedicated source highest.

---

## Grounded Generation

**System prompt grounding instruction:**

```
You are a helpful campus guide assistant. Answer the user's question using ONLY the provided context documents.

Rules:
- Use only facts explicitly stated in the context. Do not use outside knowledge.
- If the context does not contain enough information, respond exactly: "I don't have enough information on that."
- Be concise and specific.
- When you use information from a source, mention the source filename in your answer.
```

Each retrieved chunk is formatted as `[Source: filename.txt]\n{chunk text}` and passed in the user message. Temperature is set to 0.1 to reduce hallucination. No chunks are filtered by distance threshold — all top-5 results are sent to the LLM.

**How source attribution is surfaced in the response:**

1. The system prompt instructs the LLM to name source filenames in its answer.
2. The Gradio UI displays a separate **"Retrieved from"** field listing all unique source filenames from the top-k retrieval, regardless of what the LLM cites.

### Example Responses

**In-scope query:**
- **Question:** "Does the housing lottery affect which dining hall I can use?"
- **Answer:** "No, the housing lottery does not affect which dining hall you can use. (Source: housing_dining_faq.txt, meal_plan_guide.txt)"
- **Retrieved from:** `housing_dining_faq.txt`, `meal_plan_guide.txt`, `north_hall_reviews.txt`

**In-scope query:**
- **Question:** "What do students say about the dining app wait time estimates?"
- **Answer:** "According to dining_app_complaints.txt, students report that the wait time estimates in the app are unreliable. For example, North Hall showed '5 minutes' during a 30-minute line."
- **Retrieved from:** `dining_app_complaints.txt`, `cs_major_food_tips.txt`, `finals_week_survival.txt`, `north_hall_reviews.txt`

**Out-of-scope query:**
- **Question:** "Who is the university president?"
- **Answer:** "I don't have enough information on that."

---

## Query Interface

**Interface:** Gradio web UI (`app.py`)

| Field | Description |
|-------|-------------|
| **Your question** | Text input for a plain-language question |
| **Ask** button | Submits the question (Enter key also works) |
| **Answer** | Grounded response from the LLM with inline source citations |
| **Retrieved from** | Bulleted list of source document filenames used in retrieval |

**Sample interaction:**

```
Your question:  What are the late-night food options on campus?

Answer:         According to late_night_food.txt, the late-night food options on campus are:
                1. South Hall late night (Sun-Wed 9pm-12am) serving fries, pizza, and cereal.
                2. The 24-hour diner on College Ave (accepts dining dollars until 2am on weekends only).
                3. Food trucks on Library Lawn on Friday nights (take cash and card, not meal swipes).

Retrieved from: • cs_major_food_tips.txt
                • dining_app_complaints.txt
                • late_night_food.txt
                • west_village_eats.txt
```

---

## Evaluation Report

| # | Question | Expected answer | System response (summarized) | Retrieval quality | Response accuracy |
|---|----------|-----------------|------------------------------|-------------------|-------------------|
| 1 | Which dining hall has the shortest lunch wait? | North Hall before 11:45; South averages 10–15 min at lunch | Said South Hall is faster, averaging 10–15 minutes | Relevant | Inaccurate |
| 2 | Does the housing lottery affect which dining hall I can use? | No — meal plan access is the same regardless of dorm | Correctly answered No, cited housing_dining_faq.txt | Relevant | Accurate |
| 3 | What gluten-free options do students recommend? | North Hall dedicated GF station; South has labels but shared fryers | Recommended North Hall GF station, noted South's shared fryers | Relevant | Accurate |
| 4 | What are the late-night food options on campus? | South late night Sun–Wed, College Ave diner weekends, Friday food trucks | Listed all three options with hours | Relevant | Accurate |
| 5 | What do students say about the dining app wait time estimates? | Unreliable — showed 5 min during 30-min line | Cited unreliable estimates with the North Hall example | Relevant | Accurate |

**Retrieval quality:** Relevant / Partially relevant / Off-target  
**Response accuracy:** Accurate / Partially accurate / Inaccurate

---

## Failure Case Analysis

**Question that failed:** "Which dining hall has the shortest lunch wait?"

**What the system returned:** "According to south_hall_reviews.txt, lunch at South Hall is faster than North Hall, averaging 10-15 minutes."

**Root cause (tied to a specific pipeline stage):** Retrieval actually worked — the top chunk (distance 0.637) was from `north_hall_reviews.txt` and explicitly states "North Hall has the shortest lunch wait on campus if you go before 11:45." However, chunk #2 from `south_hall_reviews.txt` says "Lunch at South is faster than North… averaging 10-15 minutes." The documents contain contradictory student opinions, and the **generation stage** picked the South Hall claim over the higher-ranked North Hall chunk. The LLM blended conflicting sources instead of prioritizing the best-retrieved result or presenting the time-dependent nuance.

**What you would change to fix it:** (1) Add a distance threshold to filter chunks above 0.8 before sending to the LLM, which would have removed the conflicting South Hall chunk. (2) Instruct the LLM to prioritize higher-ranked sources when documents conflict. (3) Use larger chunks that keep a full review together so contradictory claims from different reviewers are in separate, more clearly attributed chunks.

---

## Spec Reflection

**One way the spec helped you during implementation:**

The chunking strategy section forced me to think about document structure before writing code. Knowing my corpus was short reviews rather than long guides led me to choose 400-character chunks with paragraph-aware splitting instead of a generic 500-character fixed split. The evaluation plan also gave me concrete test questions to debug against — I caught the lunch-wait failure because I had a specific expected answer to compare against.

**One way your implementation diverged from the spec, and why:**

The spec planned to verify retrieval with distance scores below 0.5, but several good matches scored 0.6–0.85. I kept top-k=5 without adding a distance cutoff because filtering at 0.5 would have removed valid results for broader questions like "late-night food options" (best match: 0.847). The tradeoff is that weaker chunks with contradictory content still reach the LLM.

---

## AI Usage

**Instance 1**

- *What I gave the AI:* The Chunking Strategy and Documents sections from `planning.md`, plus Milestone 3 assignment requirements. Asked it to implement `ingest.py` with paragraph-aware splitting at 400 characters and 80-character overlap.
- *What it produced:* A complete `ingest.py` with `load_documents()`, `clean_text()`, `chunk_text()`, and `build_chunks()`.
- *What I changed or overrode:* Added regex patterns for my specific boilerplate (cookie banners, "Share" buttons). Verified chunk count (34) was in the expected 50–2000 range and inspected 5 sample chunks for HTML artifacts.

**Instance 2**

- *What I gave the AI:* The Retrieval Approach section, architecture diagram, and assignment Milestone 5 grounding requirements. Asked for `generator.py`, `query.py`, and `app.py` with source attribution.
- *What it produced:* Full generation pipeline with Groq integration and a Gradio UI with separate answer and sources fields.
- *What I changed or overrode:* Tightened the system prompt to require exact refusal text for out-of-scope questions. Fixed a NumPy 2.x / PyTorch compatibility issue by pinning `numpy<2` in `requirements.txt` after the AI-generated dependency list caused import failures.
