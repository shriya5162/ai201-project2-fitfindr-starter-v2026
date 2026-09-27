# FitFindr

> ### 👋 Start here
>
> **New to this repo? Read [RUNNING.md](RUNNING.md) first** — setup, every
> command, and what to do when something breaks.
>
> Once `python test.py` passes:
>
> ```bash
> python app.py listings --full -n 6      # read the data (Milestone 1)
> python app.py fields                    # what you can filter on
> python app.py ask 'vintage graphic tee under $30'
> ```
>
> All three tools are stubs, so that last command will do nothing useful yet.
> That's the starting position.
>
> **The rest of this file is your submission.** Fill it in as you go.

---

<!-- ─────────────────────────────────────────────────────────────────────────
     HOW TO USE THIS FILE

     This is your submission. Fill each section in as you finish the milestone
     it belongs to — don't leave it all to the end.

     Unit 3 asks for the first five sections. Unit 4 adds the five below them.
     Leave the unit 4 sections alone until then; they're here so you know
     what's coming.

     Everything is pasted as TEXT. No screenshots, no images, no video links.
     A typed block of output gets full credit; a picture of the same output
     gets none.
     ───────────────────────────────────────────────────────────────────────── -->

<!-- ═══════════════════════ UNIT 3 — THE BUILD ═══════════════════════ -->

## What This Does

A user types one plain-language request — "vintage graphic tee under $30,
size M". FitFindr parses it into a description, a size and a price ceiling,
searches 40 thrift listings, and picks the best match. It then takes that item
and the user's saved wardrobe and suggests one or two outfits built from pieces
they already own, and writes a short caption for the find. If nothing in the
data matches, it stops after the search and says what to change instead of
inventing an item.


---

## Data Notes (Milestone 1)

**Listing:** `id`, `title`, `description`, `category`, `style_tags`, `size`,
`condition`, `price` (float), `colors`, `brand`, `platform`.
**Wardrobe item:** `id`, `name`, `category`, `colors`, `style_tags`, `notes`.

What `search_listings` has to handle:

- `size` has no single format — `M`, `S/M`, `XL (oversized)`, `W30 L30`.
  Exact matching drops most of the data.
- `brand` and `notes` can be `null`.
- Query words live in `title`, `description` **and** `style_tags`. "vintage
  graphic tee" only matches `lst_006` via its tags; its title never says
  "vintage".
- An empty wardrobe is `{"items": []}`, so check `wardrobe["items"]`, not
  `wardrobe`.

---

## Tool Inventory

<!-- Four lines per tool. This is worth 2 points and it's the single most
     common place students lose them.

     "Returns a list" earns NOTHING. The description has to say what is IN
     the list.

     The empty case isn't optional either — it's the thing your loop branches
     on, and if you don't decide it here you'll discover it as a crash in
     Milestone 5. -->

### `search_listings`

- **What it does:** Filters the 40 listings by size and price, scores what's
  left by keyword overlap with the description, and returns the best matches
  first. No model call.
- **Inputs:** `description` (str, required, e.g. `"vintage graphic tee"`);
  `size` (str or None, e.g. `"M"` — None skips the size filter);
  `max_price` (float or None, inclusive — None skips the price filter).
- **Returns:** `list[dict]`, at most `config.SEARCH_RESULT_LIMIT` (10), sorted
  by keyword score descending. Each dict is a whole listing record:
  `id` (str), `title` (str), `description` (str), `category` (str),
  `style_tags` (list[str]), `size` (str), `condition` (str), `price` (float),
  `colors` (list[str]), `brand` (str or None), `platform` (str).
- **When it has nothing:** `[]` — an empty list. Not `None`, not a string, no
  exception. This is what the loop branches on.

**Size match rule** (so someone else could build this): uppercase and strip
the requested size; uppercase the listing size, drop anything in parentheses,
and split it on `/` and spaces into tokens. It matches if the requested size
equals one token exactly. So `"M"` matches `M`, `S/M` and `M/L`, but not `XL`
or `W30 L30`. `"8"` matches `US 8` but not `US 8.5`. Any listing sized
`One Size` matches every requested size.

**Keyword score:** lowercase the description, split on whitespace, drop words
under 3 characters, and count how many appear in the listing's `title`,
`description` or `style_tags`. Zero-scoring listings are dropped.

### `suggest_outfit`

- **What it does:** Asks the model how to wear one found item with the clothes
  the user already owns.
- **Inputs:** `new_item` (dict — one listing dict from `search_listings`);
  `wardrobe` (dict with an `"items"` key holding `list[dict]`, each with
  `id`, `name`, `category`, `colors`, `style_tags`, `notes`).
- **Returns:** A non-empty `str` — one or two outfit ideas in prose, each
  naming specific wardrobe pieces by their `name`.
- **When it has nothing:** If `wardrobe["items"]` is empty it still returns a
  non-empty `str`, but general styling advice for the item instead of named
  pieces. It never returns `""` and never raises.

### `create_fit_card`

- **What it does:** Writes a short caption the user could actually post about
  the find.
- **Inputs:** `outfit` (str — the return value of `suggest_outfit`);
  `new_item` (dict — the same listing dict).
- **Returns:** A `str` of two to four sentences that names the item, its price
  and its platform once each, and reads like a post rather than a product
  description. Different items produce different captions.
- **When it has nothing:** If `outfit` is empty or whitespace-only, it returns
  a descriptive message (`"Can't write a fit card without an outfit."`) rather
  than calling the model or raising.

---

## Planning Loop

<!-- Your branch rule, stated as a rule — the condition AND both paths — plus
     the file and function that holds it.

     Like this:
       "If search_listings returns an empty list, put a message in the session
        and stop. Otherwise take the first result and go to suggest_outfit."
        — agent.py::run_agent

     The grader checks your code against what you claim here, so the file and
     function have to be real. -->

**Branch rule:** If `search_listings` returns an empty list, write a message
into `session["error"]` naming what the user could change — the price ceiling,
the size, or the wording — and return the session immediately, leaving
`selected_item`, `outfit_suggestion` and `fit_card` as `None`. Otherwise put
the first result in `session["selected_item"]` and continue to
`suggest_outfit`.

**Where it lives:** `agent.py::run_agent`

**How the query is parsed:** Regex, in `run_agent`. `under $30` / `$30` →
`max_price` (float); `size M` / `size 8` → `size` (str); those matched spans
are stripped out and what remains is the `description`.

**What moves through the session:** `query` → `parsed` (description, size,
max_price) → `search_results` → `selected_item` → `outfit_suggestion` →
`fit_card`. `wardrobe` is set at the start and read by `suggest_outfit`. The
user never re-types the item: `selected_item` is what `search_listings` put in
the session, and both later tools read it from there.

---

## Sample Run

<!-- Two things go here.

     1. One FULL query and its output, pasted as text.
     2. Your three per-tool terminal tests — the command and what it printed. -->

**One full query**

```
$ python app.py ask '...'

```

**The three tools, tested one at a time**

**1. `search_listings` — a match, and the empty case**

```
$ python -c "from tools import search_listings; r = search_listings('vintage graphic tee', size='M', max_price=30.0); print(len(r), 'results'); [print(x['id'], x['title'], x['size'], x['price']) for x in r]; print('empty case:', search_listings('designer ballgown', size='XXS', max_price=5.0))"

10 results
lst_002 Y2K Baby Tee — Butterfly Print S/M 18.0
lst_017 Mesh Long-Sleeve Top — Black S/M 15.0
lst_013 90s Silk Slip Dress — Floral, Midi Length M 30.0
lst_014 Leather Belt — Brown, Braided One Size (adjustable) 12.0
lst_020 Henley Long Sleeve — Washed Burgundy M 16.0
lst_024 Vintage Polo Shirt — Forest Green M 18.0
lst_029 Silk Button-Down — Sage Green M 28.0
lst_030 Vintage Knit Vest — Argyle Brown/Cream M 25.0
lst_034 Bucket Hat — Reversible, Brown Plaid One Size 14.0
lst_038 Denim Vest — Medium Wash, Studded M 27.0
empty case: []
```

Every price is at or under 30, no result is sized `L`, `XL` or a `W__` waist,
and the two `One Size` items came through as the size rule says they should.
The empty case is `[]`, which is what the loop branches on.

**2. `suggest_outfit` — the example wardrobe, then an empty one**

```
$ python -c "from tools import suggest_outfit; from utils.data_loader import get_example_wardrobe, load_listings; print(suggest_outfit(load_listings()[0], get_example_wardrobe()))"

Pair the Vintage Levi's 501 Jeans — Medium Wash with the white ribbed tank top
tucked in, layered under the vintage black denim jacket, and finished with the
chunky white sneakers. Add a brown leather belt to pull the casual look together.

For a cozier street style vibe, style the Vintage Levi's 501 Jeans — Medium Wash
with the oversized grey crewneck sweatshirt and the black combat boots. Cinch the
waist with the brown leather belt and wear the black crossbody bag to complete
the outfit.
```

Every piece named is one of the ten wardrobe items.

```
$ python -c "from tools import suggest_outfit; from utils.data_loader import get_empty_wardrobe, load_listings; print(suggest_outfit(load_listings()[0], get_empty_wardrobe()))"

These mid-rise, straight-leg classics create a balanced silhouette that looks
best paired with an oversized, boxy top to contrast the fitted waist. The
versatile medium indigo wash acts as a neutral, sitting effortlessly next to
earthy tones like olive and cream, as well as crisp bright whites. Elevate the
streetwear edge by finishing the look with saturated jewel tones like cherry red
or emerald green for a sharp pop of contrast.
```

Non-empty, and it describes silhouettes and colours instead of claiming the
user owns anything — criterion 5.

**3. `create_fit_card` — the empty case, then three runs on one item**

```
$ python -c "from tools import create_fit_card; from utils.data_loader import load_listings; print(repr(create_fit_card('   ', load_listings()[0])))"

"Can't write a fit card without an outfit."
```

Three runs on the same item with the cache off (`AI201_CACHE=0`), to check the
cards aren't a template:

```
$ AI201_CACHE=0 python -c "from tools import create_fit_card; from utils.data_loader import load_listings; i=load_listings()[0]
for n in range(3): print(create_fit_card('jeans and white sneakers', i))"

--- run 1 ---
Finally tracked down the holy grail vintage Levi's 501 jeans in that perfect
medium wash. They've got that ideal broken-in indigo look that only comes with
real age. Just wearing them with crisp white sneakers for that effortless
streetwear vibe. Snagged them for $38 on depop.

--- run 2 ---
Nothing beats a classic pair of vintage Levi's that actually hold their shape.
Scored these medium wash ones on depop for $38 and they are the ultimate everyday
straight leg. Just throwing them on with crisp white sneakers for that effortless,
broken-in 90s look.

--- run 3 ---
Finally found the holy grail of slouchy vintage denim in the absolute best medium
wash. Got these on depop for $38 and I'm honestly never taking them off. They look
so good worn low with crisp white sneakers for that effortless 90s streetwear look.
```

Three different cards, no shared opening sentence, and each names `$38` and
`depop` once — criterion 4.

---

## How I Used AI

<!-- Two specific moments. What you asked, what came back, what you changed.

     "I used Claude to help me code" is not enough.

     "I gave Claude my search_listings spec. It returned None on no match
     instead of an empty list, so I changed it" is the level we want. -->

**Moment 1**

- *What I asked for:*
- *What came back:*
- *What I changed:*

**Moment 2**

- *What I asked for:*
- *What came back:*
- *What I changed:*

<!-- ═══════════════════════ UNIT 4 — THE TEST ═══════════════════════

     Don't fill these in during unit 3.
     ═══════════════════════════════════════════════════════════════════ -->

---

## Run Log — Before

<!-- Five criteria, five tries each, in this exact format.

     Five, because your criteria are written out of five. Mark each try PASS
     or FAIL, count the passes, and read that count against your target — a
     row targeting 4 of 5 with three PASS cells is MISSED (3/5).

     `python run_eval.py --label before` runs everything and writes the table
     into results/. Paste it here and fill in the verdicts. -->

| Criterion | Target | Try 1 | Try 2 | Try 3 | Try 4 | Try 5 | Verdict |
|---|---|---|---|---|---|---|---|
| 1.  |  |  |  |  |  |  |  |
| 2.  |  |  |  |  |  |  |  |
| 3.  |  |  |  |  |  |  |  |
| 4.  |  |  |  |  |  |  |  |
| 5.  |  |  |  |  |  |  |  |

**Real output from one try**, pasted as text, naming the file and function
that produced it:

```

```

---

## Verdicts and Diagnoses

<!-- MET or MISSED per criterion against LAST UNIT's target, plus a sentence on
     how you decided.

     Then, for every miss: which of the four places it happened — a tool, the
     loop's branch, the session, or the model's output — AND the mechanism.

     Not a diagnosis:  "The fit card was bad."
     A diagnosis:      "The fit card criterion missed on 2 of 5 items. Both had
                        an empty brand field. My prompt puts the brand in the
                        first sentence, so the card opened with a blank and read
                        like a fragment. The tool worked; the prompt assumed a
                        field that isn't always there."

     Look for a pattern. Three misses on the same tool is one problem, not
     three. -->

| # | Criterion | Target | Verdict | How I decided |
|---|---|---|---|---|
| 1 |  |  |  |  |
| 2 |  |  |  |  |
| 3 |  |  |  |  |
| 4 |  |  |  |  |
| 5 |  |  |  |  |

**Diagnoses**



---

## Loop Trace

<!-- One full run, printed step by step, with the MCP call visible in it.

     `python app.py ask '...' --trace` once you've added the trace.step()
     calls in Milestone 2.

     Worth pasting BOTH the happy path and the empty-search path. The empty
     one should be visibly shorter, because it stops. If your two traces are
     the same length, your branch isn't working — and this is the fastest way
     anyone will ever find that out. -->

**Happy path**

```

```

**Empty search**

```

```

**On the MCP move:** <!-- what changed in your code, and whether anything
behaved differently afterwards. If the rewire didn't work, say exactly where it
broke — the error text and the last thing that worked. That earns the point in
full. -->



---

## The Improvement

<!-- What you changed, why your diagnosis pointed at it, and the after-run in
     the same table format. One change, measured properly.

     `python run_eval.py --label after` -->

**What I changed:**

**Which failure it was meant to fix:**

### Run Log — After

| Criterion | Target | Try 1 | Try 2 | Try 3 | Try 4 | Try 5 | Verdict |
|---|---|---|---|---|---|---|---|
| 1.  |  |  |  |  |  |  |  |
| 2.  |  |  |  |  |  |  |  |
| 3.  |  |  |  |  |  |  |  |
| 4.  |  |  |  |  |  |  |  |
| 5.  |  |  |  |  |  |  |  |

**Did it help, and how do I know:**

<!-- If it made things worse, say that. Honestly reported, that earns full
     credit and is more interesting than one that worked. -->



---

## What's Still Broken

<!-- For each criterion still missed: what you'd do, and why you stopped where
     you did. "I ran out of time" is fine if it's true. Pretending nothing is
     left is not. -->



<!-- ═════════════════════════════════════════════════════════════════════

     SUBMISSION CHECKLIST — unit 3

       [ ] criteria.md has five numbered criteria, each with a target
       [ ] Each criterion has a reason underneath it
       [ ] All five unit 3 sections above have real content
       [ ] Tool Inventory: all three tools, inputs WITH TYPES, a specific
           return value, and the empty case
       [ ] Planning Loop names the branch rule and agent.py::run_agent
       [ ] Sample Run: one full query plus the three per-tool tests, as text
       [ ] At least four new commits
       [ ] Repository URL submitted — WRITE IT DOWN, you submit the same one
           next unit

     SUBMISSION CHECKLIST — unit 4

       [ ] mcp_server.py exists with one tool registered
           (or a written record of exactly where the rewire broke)
       [ ] Run Log — Before, five criteria, five tries each
       [ ] Real output pasted underneath, naming file and function
       [ ] A verdict on every criterion
       [ ] A diagnosis for every miss, naming a place AND a mechanism
       [ ] Loop Trace, with the MCP call visible in it
       [ ] All three failure modes triggered and handled
       [ ] One improvement, with Run Log — After in the same format
       [ ] What's Still Broken
       [ ] At least four new commits
       [ ] The SAME repository URL as last unit

     Do not delete and recreate this repository. Your commit history is what
     shows your criteria existed before your results did.
     ═════════════════════════════════════════════════════════════════════ -->

---

📖 **How to run this project: [RUNNING.md](RUNNING.md)**
