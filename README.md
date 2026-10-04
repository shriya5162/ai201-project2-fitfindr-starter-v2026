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
$ python app.py ask 'vintage graphic tee under $30, size M'

  Found:    Y2K Baby Tee — Butterfly Print — $18.0 on depop

  Outfit:   Pair Y2K Baby Tee — Butterfly Print with baggy straight-leg jeans,
            dark wash, finished with chunky white sneakers and the black
            crossbody bag.

            Layer the black cropped zip hoodie over Y2K Baby Tee — Butterfly
            Print, paired with wide-leg khaki trousers and black combat boots.

  Fit card: Found this dreamy little butterfly baby tee on depop for $18 and
            it's honestly giving peak early 2000s mall rat energy. I've been
            living for the pastel pink and purple print, especially thrown on
            with baggy denim and chunky sneakers. Such a cute nostalgic piece
            to have on rotation.
```

**The same query, with the session printed** — the item found is the item both
later tools received:

```
parsed:           {'description': 'vintage graphic tee', 'size': 'M', 'max_price': 30.0}
search_results:   10 -> first is lst_002
selected_item:    lst_002 Y2K Baby Tee — Butterfly Print
same object as search_results[0]? True
title in outfit_suggestion?       True
price in fit_card?                True
platform in fit_card?             True
error:            None
```

**The query the data can't match** — it stops at the branch:

```
$ python app.py ask 'designer ballgown size XXS under $5'

  Nothing in the 40 listings matches the words "designer ballgown", size XXS,
  a price under $5. Try raising the price, dropping the size, or using plainer
  words — the listings are tagged things like 'vintage', 'y2k', 'grunge',
  'streetwear' and 'graphic tee', so those find more than a brand name or a
  specific garment will.
```

`session["fit_card"]` is still `None` here, and `suggest_outfit` was never
called.

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

**Moment 1 — the size filter**

- *What I asked for:* I gave Claude my `search_listings` spec and asked
  whether someone else could build the tool from it without asking me
  anything.
- *What came back:* It pointed at the size line. I'd written "match
  case-insensitively," which sounds specific but isn't — a substring test
  makes `"L"` match `XL`, and `"S"` match `US 9`, so asking for a small top
  returns shoes. It also found `One Size` and `XL (oversized)` in the data,
  which I hadn't decided anything about.
- *What I changed:* I replaced that line with an actual rule: drop
  parentheses, split the listing's size on `/` and spaces, and require an
  exact match against one whole token, with `One Size` matching everything.
  That's what `_size_matches` in `tools.py` implements, and my Milestone 4
  test confirms no `L`, `XL` or `W__` result comes back for size M.

**Moment 2 — a criterion I threw out**

- *What I asked for:* Candidates for my fifth acceptance criterion, built
  from things my code can actually be measured on.
- *What came back:* Four options. One was "every result is at or under the
  price ceiling — 5 of 5," which looked like the cleanest to score.
- *What I changed:* I dropped it. The price ceiling is one `if` on a float in
  code I'd already written, so it passes 5 of 5 by construction — the brief
  warns that a target you can't miss is the thing that costs points. I took
  the empty-wardrobe criterion instead, at 4 of 5, because whether the model
  invents clothes the user never entered depends on my prompt holding it back,
  and that can genuinely fail.

**Unit 4**

I used Claude Code for most of the hands-on work this unit.

**Moment 3 — scoring criterion 3**

- *What I asked for:* I asked Claude to score each of the five tries for
  criterion 3 against `criteria.md` exactly as written. Criterion 3 says the
  selected item's title has to appear in the outfit suggestion.
- *What came back:* It scored 1/5. The selected item was
  `90s Track Jacket — Navy/White Stripe`, but in tries 2–5 the outfit only
  said "Layer the 90s Track Jacket over the white ribbed tank top…". Claude
  pointed out that counting "90s Track Jacket" as the title would turn this
  into 5/5, but only by loosening the criterion after seeing the results. It
  also showed that the trace had the right item going into `suggest_outfit`
  all five times, so the session wasn't the problem.
- *What I changed:* I kept the verdict as MISSED (1/5). In `criteria.md` I
  added a revision under the original criterion 3, with the original left in
  place, that checks the item's id in the session and trace instead of the
  model's text. I used this miss as my one fix in Milestone 5.

**Moment 4 — checking the fix**

- *What I asked for:* After changing the `suggest_outfit` prompt to give the
  full title and say "do not shorten it", I asked Claude to re-run all five
  criteria and compare all 20 outfits from the after-run against the 20 from
  the before-run, not just the criterion 3 row.
- *What came back:* Criterion 3 went from 1/5 to 5/5. But the comparison found
  two things that weren't there before. Two outfits said "Layer **your** 90s
  Track Jacket — Navy/White Stripe…", treating the find like something the
  user already owns. Two slip-dress outfits had garbled words: "Toughin up"
  and "Tourenough for cooler weather", where the before-run said "Toughen up".
- *What I changed:* Instead of calling the fix a clean win, I wrote both
  problems up under "Did it help" and in What's Still Broken. I didn't make a
  second change to chase them, because then I couldn't tell which change
  caused what.

<!-- ═══════════════════════ UNIT 4 — THE TEST ═══════════════════════

     Don't fill these in during unit 3.
     ═══════════════════════════════════════════════════════════════════ -->

---

## Run Log — Before

`python run_eval.py --label before`: five tries per criterion, cache off
(40 real model calls, 0 from cache), temperature 0.9. The full output is in
[`results/run_2026-10-03_2250_before.md`](results/run_2026-10-03_2250_before.md). Scenarios are in `scenarios.py`, one per criterion.

| Criterion | Target | Try 1 | Try 2 | Try 3 | Try 4 | Try 5 | Verdict |
|---|---|---|---|---|---|---|---|
| 1. A matching query completes all three tools | 4 of 5 | PASS | PASS | PASS | PASS | PASS | MET (5/5) |
| 2. An impossible query stops before the second tool | 5 of 5 | PASS | PASS | PASS | PASS | PASS | MET (5/5) |
| 3. The item search found is the item the next tool got | 5 of 5 | PASS | FAIL | FAIL | FAIL | FAIL | MISSED (1/5) |
| 4. The fit card names price and platform, caption-length | 4 of 5 | PASS | PASS | PASS | PASS | PASS | MET (5/5) |
| 5. Empty wardrobe still produces a card, nothing invented | 4 of 5 | PASS | PASS | PASS | PASS | PASS | MET (5/5) |

**How each try was scored** (exactly as `criteria.md` is worded, without
loosening anything):

1. PASS if the run finished with `session["error"] is None` and a non-empty
   `fit_card`. Query: `vintage graphic tee under $30`.
2. PASS if the trace stops after `search_listings` (two steps, no
   `suggest_outfit`), `fit_card` is `None`, and the message names something to
   change. Query: `designer ballgown size XXS under $5`.
3. PASS if the selected item's **title**, `90s Track Jacket — Navy/White
   Stripe`, appears in `outfit_suggestion`. It's the only listing with that
   title (`lst_004`), so the title identifies the id. In tries 2–5 the outfit
   says only "90s Track Jacket". That is not the title, so I scored those
   FAIL. If I'd accepted the shortened name, it would be 5/5. I didn't,
   because that would loosen the criterion after seeing the result. The trace
   shows the right item reached `suggest_outfit` all five times, which is the
   lead for the diagnosis.
4. PASS if `$30` appears exactly once, the platform ("depop", any
   capitalisation) exactly once, and the card has 2–4 sentences. All five:
   1 × `$30`, 1 × depop, 3 sentences.
5. PASS if the fit card is non-empty and the **outfit suggestion** names no
   garment as one the user owns. All five outfits give general advice ("pair
   it with high-waisted wide-leg trousers…"). **Flag:** try 4's *fit card*
   says "about to live over every slip dress and high-waisted trouser **I
   own**". That's the invented-ownership failure this criterion exists to
   catch, but in the caption, which the criterion doesn't look at. It counts
   as PASS as written. I'm noting it rather than hiding it.

**Real output from one try per criterion**

Criterion 1, try 1. Fit card from `tools.py::create_fit_card`, called by
`agent.py::run_agent`:

```
Found this little butterfly baby tee on depop for just $18 and I’m so obsessed with the dreamy pink and purple print. It gives off the ultimate early 2000s mall-rat energy, especially styled with some baggy denim and chunky sneakers. Such a sweet little piece for summer.
```

Criterion 2, try 1. Trace and stop message from `agent.py::run_agent` (message
built by `agent.py::_nothing_found_message`):

```
[1] parse_query
      in:  designer ballgown size XXS under $5
      out: description='designer ballgown', size='XXS', max_price=5.0
[2] search_listings (via MCP)
      in:  description='designer ballgown', size='XXS', max_price=5.0
      out: [] (empty)
      →    branch: empty, stopping before suggest_outfit

Nothing in the 40 listings matches the words "designer ballgown", size XXS, a price under $5. Try raising the price, dropping the size, or using plainer words — the listings are tagged things like 'vintage', 'y2k', 'grunge', 'streetwear' and 'graphic tee', so those find more than a brand name or a specific garment will.
```

Criterion 3, try 2 (a FAIL). `selected_item` set by `agent.py::run_agent`,
outfit from `tools.py::suggest_outfit`:

```
selected_item: 90s Track Jacket — Navy/White Stripe ($45.0, poshmark)

Layer the 90s Track Jacket over the white ribbed tank top and pair it with baggy straight-leg jeans, dark wash. Finish this retro streetwear look with chunky white sneakers and the black crossbody bag.

Wear the 90s Track Jacket open over the black cropped zip hoodie tucked into the wide-leg khaki trousers. Ground the outfit with black combat boots and accent your waist with the brown leather belt.
```

For contrast, try 1 (the PASS) opens: "Pair the 90s Track Jacket — Navy/White Stripe with the white ribbed tank top and baggy straight-leg jeans, finished off with chunky white sneakers."

Criterion 4, try 1. Fit card from `tools.py::create_fit_card`:

```
Finally scored this dreamy 90s floral silk slip on Depop for $30 and I am obsessed with the soft ivory and dusty pink palette. It has the ultimate cottagecore romance, but I love toughening it up by layering an oversized grey crewneck right over top with some beat-up black combat boots. Such an easy piece to dress down for everyday.
```

Criterion 5, try 4. Outfit from `tools.py::suggest_outfit` (empty-wardrobe
prompt) and fit card from `tools.py::create_fit_card`:

```
Outfit: Balance the boxy, cropped silhouette of the jacket by pairing it with high-waisted wide-leg trousers or a fitted midi skirt to accentuate the waist. This light-wash vintage piece shines next to crisp whites, rich earth tones like olive and chocolate brown, or monochromatic denim for a bold Canadian tuxedo look.

Fit card: Nothing beats a properly broken-in Wrangler denim jacket with that perfect vintage fade. I scored this cropped light-wash beauty for $42 on poshmark and it’s about to live over every slip dress and high-waisted trouser I own. The boxy fit gives it such a good streetwear edge without trying too hard.
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
| 1 | A matching query completes all three tools | 4 of 5 | **MET (5/5)** | All five tries ended with `error = None` and a non-empty fit card. 5 ≥ 4. |
| 2 | An impossible query stops before the second tool | 5 of 5 | **MET (5/5)** | All five traces stop at step 2 (`search_listings`, `[] (empty)`) with no `suggest_outfit` step, `fit_card` is `None`, and the message names the words, size and price to change. |
| 3 | The item search found is the item the next tool got | 5 of 5 | **MISSED (1/5)** | The criterion requires the selected item's *title* in `outfit_suggestion`. The full title `90s Track Jacket — Navy/White Stripe` appears only in try 1. Tries 2–5 say "90s Track Jacket", which is not the title. 1 < 5. |
| 4 | The fit card names price and platform, caption-length | 4 of 5 | **MET (5/5)** | Each card: `$30` × 1, "depop" × 1 (any case), 3 sentences. Counted by script and by reading. 5 ≥ 4. |
| 5 | An empty wardrobe still produces a card, nothing invented | 4 of 5 | **MET (5/5)**, as written | Five non-empty cards. None of the five outfit suggestions names a garment as one the user owns. But try 4's *fit card* says "every slip dress and high-waisted trouser **I own**". The criterion only scores the outfit, so it passes as written. See the diagnosis below. |

**Diagnoses**

**Criterion 3, MISSED (1/5). Place: the model's output (in
`tools.py::suggest_outfit`), measured by a criterion that checks the wrong
thing.**

The session handoff worked all five times. In every trace, step 3
(`select_item`) and step 4 (`suggest_outfit`, `new_item=...`) carry the same
listing, `90s Track Jacket — Navy/White Stripe`. `agent.py::run_agent` passes
`session["selected_item"]` straight into `suggest_outfit` without rebuilding
it. So the loop and the session aren't where it broke.

What failed is the evidence the criterion relies on. It checks the handoff by
looking for the title in `outfit_suggestion`, which is text the model writes.
My prompt asks it to "name the find by its title", but nothing in the code
checks that it did. For this item the model shortened the title to the part
before the dash in 4 of 5 tries. It does this only for this item. Across every
example-wardrobe run, the full title appeared in 10 of 10 mentions for
`Y2K Baby Tee — Butterfly Print`, 9 of 9 for
`90s Silk Slip Dress — Floral, Midi Length`, and 2 of 10 for the track jacket.
My guess, which I haven't tested, is that "Navy/White Stripe" reads as a
colour note. It repeats the `Colours: navy, white` line just above it in the
prompt, so the model treats it as metadata rather than part of the name.

The underlying mistake is in how I wrote the criterion. My reason for 5 of 5
says "nothing between those two points calls the model". But the measurement
goes *through* a model call, so a 5-of-5 target on it was always exposed to
model variance. The criterion measured whether the model copies a string, not
whether the session passed the right item. See the revision in `criteria.md`.
The original line and its MISSED verdict stand.

**Pattern across the results.** The two findings that matter (the criterion 3
miss and the criterion 5 flag) are the same problem showing up in two places:
**the two tools that call the model return text that nothing in the code
checks.** The prompts say "name the find by its title" and "do not name or
assume any specific garment as something they already own". The model follows
both most of the time and drops them some of the time, and `tools.py` returns
whatever comes back. My criteria then point the wrong way. Criterion 3 checks
model text for something the code already guarantees, the item handoff.
Criterion 5 checks the outfit for invented ownership but not the fit card,
which is where invented ownership actually showed up. In try 4 the empty-
wardrobe prompt held in `suggest_outfit`, and then `create_fit_card`, which
has no empty-wardrobe instruction and writes in the first person, said "I
own".

**Met criteria: were the targets too low?**

- **Criterion 1: the target is fine, but my test of it was too narrow.** The 4
  of 5 allowance was for phrasings that keyword search can't match, but I ran
  one phrasing five times. Search is deterministic, so the only thing those
  five tries could catch was a model crash. A fairer test is five different
  phrasings of things that are in the data.
- **Criterion 2:** 5 of 5 was the right target. It's an `if` on an empty list
  and it held.
- **Criterion 4: this is the one I'd tighten.** All five cards came out at
  exactly 3 sentences with one price and one platform. The prompt spells out
  both rules, so the 4 of 5 allowance for drift wasn't needed. I'd raise it to
  5 of 5 and test it on more than one item. A single item can't show whether
  a missing or odd field (for example `brand: None`) breaks the format.
- **Criterion 5: met as written, but it checks the wrong output.** If it also
  scored the fit card, try 4 would fail. That's 4/5, which still meets the
  4-of-5 target, but only just, and it's the failure the criterion was written
  to catch. Revision proposed in `criteria.md`.

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
$ python app.py ask 'vintage graphic tee under $30, size M' --trace
[1] parse_query
      in:  vintage graphic tee under $30, size M
      out: description='vintage graphic tee', size='M', max_price=30.0
[2] search_listings (via MCP)
      in:  description='vintage graphic tee', size='M', max_price=30.0
      out: 10 items: Y2K Baby Tee — Butterfly Print, Mesh Long-Sleeve Top — Black, 90s Silk Slip Dress — Floral, Midi Length … +7 more
      →    branch: results found, continuing
[3] select_item
      in:  10 results
      out: Y2K Baby Tee — Butterfly Print ($18.0, depop)
      →    first result = highest keyword score
[4] suggest_outfit
      in:  new_item='Y2K Baby Tee — Butterfly Print', wardrobe_items=10
      out: Pair Y2K Baby Tee — Butterfly Print with baggy straight-leg jeans, dark wash, finished with chunky white sneak…
[5] create_fit_card
      in:  new_item='Y2K Baby Tee — Butterfly Print', outfit='Pair Y2K Baby Tee — Butterfly Print with baggy straight-leg…
      out: Found this dreamy little butterfly baby tee on depop for $18 and it’s honestly giving peak early 2000s mall ra…

  Found:    Y2K Baby Tee — Butterfly Print — $18.0 on depop
  ...
0 model calls this session, 2 served from cache
```

Step 2 is the MCP call: `search_listings` runs in `mcp_server.py` and is
called through `mcp_client.call_tool`. Both model calls in this run were
served from the build cache, because I had run the same query before. The
trace shows the same steps either way.

One thing the trace shows that the final output doesn't: result 3 for
"vintage graphic tee" is a silk slip dress. The keyword score counts any
matching word, so "vintage" alone is enough to get a listing in.

**Empty search**

```
$ python app.py ask 'designer ballgown size XXS under $5' --trace
[1] parse_query
      in:  designer ballgown size XXS under $5
      out: description='designer ballgown', size='XXS', max_price=5.0
[2] search_listings (via MCP)
      in:  description='designer ballgown', size='XXS', max_price=5.0
      out: [] (empty)
      →    branch: empty, stopping before suggest_outfit

  Nothing in the 40 listings matches the words "designer ballgown", size XXS, a price under $5. Try raising the price, dropping the size, or using plainer words — ...

0 model calls this session
```

Two steps instead of five, and no model calls: the branch stops before
`suggest_outfit`.

**On the MCP move:** <!-- what changed in your code, and whether anything
behaved differently afterwards. If the rewire didn't work, say exactly where it
broke — the error text and the last thing that worked. That earns the point in
full. -->

`search_listings` now runs behind MCP. In `mcp_server.py` it's registered with
FastMCP under the same name and typed inputs as the Tool Inventory
(`description: str`, `size: str | None`, `max_price: float | None`). Its
description states units (US dollars, inclusive), the size-match rule, and the
empty case (`[]`, never null or an error). In `agent.py` the direct
`search_listings(...)` call in the `search` step is now
`call_tool("search_listings", {...})`. `suggest_outfit` and `create_fit_card`
are still called directly.

Nothing behaved differently. I checked that by calling it both ways on three
inputs (`vintage graphic tee`/M/$30, `vintage graphic tee`/no size/$30,
`designer ballgown`/XXS/$5). Direct and MCP gave `==`-identical lists (10, 10,
0 items). The empty case came back as an empty `list`, not `None` or a string,
so the branch in the loop still fires. The one visible change is speed: each
search now starts the server process, so the search step is noticeably slower.

The move also created a new way for the search to fail: if `mcp_server.py`
can't start, `call_tool` raises `MCPError`. Before Milestone 2 nothing caught
that, so the run would have crashed. The search step now catches it and stops
with a message (see Failure Modes, "MCP server unreachable").


---

## Failure Modes

I triggered each failure on purpose, one at a time, and recorded what the agent
said **before** adding any handlers, then again after.

**1. Empty search.** Already handled by the branch from the previous unit.

```
$ python app.py ask 'sequined opera gloves size XXS under $3'

  Nothing in the 40 listings matches the words "sequined opera gloves", size XXS, a price under $3. Try raising the price, dropping the size, or using plainer words — the listings are tagged things like 'vintage', 'y2k', 'grunge', 'streetwear' and 'graphic tee', so those find more than a brand name or a specific garment will.
```

It stops before any model call and names the three things the user can change.
No handler needed.

**2. Empty wardrobe.** Already handled inside `suggest_outfit` (`tools.py`),
which has a separate prompt for `wardrobe["items"] == []`.

```
$ python app.py ask 'corduroy jacket under $60' --empty-wardrobe
(running with an empty wardrobe)

  Found:    90s Track Jacket — Navy/White Stripe — $45.0 on poshmark

  Outfit:   Balance the sporty volume of this Champion jacket with a slim-fitting bottom, like a straight-cut skirt or tailored trousers, to create a sharp contrast in silhouettes. The classic navy and white palette anchors effortlessly next to neutral earth tones like olive and beige, or you can lean into the retro streetwear vibe with vibrant accents like cherry red.

  Fit card: Found this absolute gem of a 90s Champion track jacket on Poshmark for $45 ...
```

General advice, no crash, no empty string, and it doesn't claim the user owns
anything. No handler needed. A side effect showed up, though: I asked for a
*corduroy* jacket and got a *track* jacket. "corduroy" matched nothing, but
"jacket" did, and one matching word is enough to make the cut. That's a
`search_listings` scoring issue, not an empty-wardrobe one. I'm noting it here
for the diagnosis.

**3. Model unavailable.** Triggered by running with `GEMINI_API_KEY` one
character off, on a query not in the cache. **Before** a handler, the
`ModelUnavailable` exception escaped `run_agent()` and was caught only by
`app.py`'s catch-all:

```
$ python app.py ask 'olive cargo pants under $45'

ModelUnavailable: The model rejected your API key. Check GEMINI_API_KEY in your .env file, or create a fresh key at aistudio.google.com.

1 model calls this session          (exit code 1)
```

It didn't hang and there was no stack trace, so that part was fine. But the
search had already found a listing, and the crash threw it away. The user also
couldn't tell which step broke. I added a handler in `agent.py::run_agent`
around both `suggest_outfit` and `create_fit_card`. It catches
`ModelUnavailable`, puts a message in `session["error"]` and stops the loop.
**After:**

```
$ python app.py ask 'olive cargo pants under $45' --trace
...
[4] suggest_outfit
      in:  new_item='Low-Rise Cargo Pants — Khaki', wardrobe_items=10
      out: ModelUnavailable: The model rejected your API key. Check GEMINI_API_KEY in your .env file, or create a fresh k…
      →    model unreachable, stopping

  Found Low-Rise Cargo Pants — Khaki — $27 on poshmark — but couldn't suggest an outfit: the model couldn't be reached. The model rejected your API key. Check GEMINI_API_KEY in your .env file, or create a fresh key at aistudio.google.com. Once that's fixed, ask again; the search itself worked.
```

(exit code 0). It names what broke (the model, at the outfit step), why (the
key), and what to do. It also keeps the find.

**Extra: MCP server unreachable.** Moving the search onto MCP added a new way
for it to fail, so I forced that one too by renaming `mcp_server.py` for one
run. A handler in the `search` step now catches `MCPError`:

```
[2] search_listings (via MCP)
      in:  description='denim jacket', size=None, max_price=50.0
      out: MCPError: Couldn't call 'search_listings' over MCP: unhandled errors in a TaskGroup (1 sub-exception) Check th…
      →    branch: server unreachable, stopping

  Couldn't search the listings: the search server (mcp_server.py) didn't respond, so nothing was searched. Run `python mcp_server.py` on its own to see why it won't start, fix that, then ask again.
```

The raw MCP error ("unhandled errors in a TaskGroup") stays in the trace but
not in the user message, because it tells a user nothing they can act on.

---

## The Improvement

<!-- What you changed, why your diagnosis pointed at it, and the after-run in
     the same table format. One change, measured properly.

     `python run_eval.py --label after` -->

**What I changed:** One line of the prompt in `tools.py::suggest_outfit`,
in the branch for a non-empty wardrobe. It used to say:

```
...Name each piece exactly as it is written above, and name the find by its title. Use only pieces from the list.
```

Now the prompt states the title itself and says not to shorten it:

```
...Name each piece exactly as it is written above. Every time you mention the find, write its full title
exactly as "{new_item["title"]}" — including the part after the dash; do not shorten it. Use only pieces from the list.
```

Nothing else changed. The empty-wardrobe prompt, `create_fit_card`, the loop,
the scenarios and the criteria are all exactly as they were in the before-run.

**Which failure it was meant to fix:** Criterion 3, MISSED (1/5). The
diagnosis found the session handoff was correct every time. The miss came from
the model shortening `90s Track Jacket — Navy/White Stripe` to "90s Track
Jacket" in 4 of 5 outfits, because the prompt said "its title" without saying
what the title was or forbidding a short form.

### Run Log — After

`python run_eval.py --label after`: same five scenarios, five tries each, cache
off, 40 real model calls, temperature 0.9. Raw output:
[`results/run_2026-10-03_2327_after.md`](results/run_2026-10-03_2327_after.md).
Scored with the same rules as the before-run, against the **original**
criteria.

| Criterion | Target | Try 1 | Try 2 | Try 3 | Try 4 | Try 5 | Verdict |
|---|---|---|---|---|---|---|---|
| 1. A matching query completes all three tools | 4 of 5 | PASS | PASS | PASS | PASS | PASS | MET (5/5) |
| 2. An impossible query stops before the second tool | 5 of 5 | PASS | PASS | PASS | PASS | PASS | MET (5/5) |
| 3. The item search found is the item the next tool got | 5 of 5 | PASS | PASS | PASS | PASS | PASS | MET (5/5) |
| 4. The fit card names price and platform, caption-length | 4 of 5 | PASS | PASS | PASS | PASS | PASS | MET (5/5) |
| 5. Empty wardrobe still produces a card, nothing invented | 4 of 5 | PASS | PASS | PASS | PASS | PASS | MET (5/5) |

**Side by side**

| Criterion | Target | Before | After |
|---|---|---|---|
| 1 | 4 of 5 | MET (5/5) | MET (5/5) |
| 2 | 5 of 5 | MET (5/5) | MET (5/5) |
| 3 | 5 of 5 | **MISSED (1/5)** | **MET (5/5)** |
| 4 | 4 of 5 | MET (5/5) | MET (5/5) |
| 5 | 4 of 5 | MET (5/5) | MET (5/5) |
| 3, revised (id from session/trace) | 5 of 5 | 5/5 | 5/5 |
| 5, revised (outfit **and** fit card) | 4 of 5 | 4/5 (try 4: "…trouser I own") | 4/5 (try 5: "I love throwing it over olive trousers") |

Real output, criterion 3, after-run try 2. Outfit from
`tools.py::suggest_outfit`:

```
Layer your 90s Track Jacket — Navy/White Stripe over the white ribbed tank top, paired with baggy straight-leg jeans, dark wash and chunky white sneakers for an effortless athletic look. For a colder day, wear the 90s Track Jacket — Navy/White Stripe over the oversized grey crewneck sweatshirt with wide-leg khaki trousers and black combat boots.
```

**Did it help, and how do I know:** Yes, for the criterion it targeted. The
full title appeared in 2 of 2 mentions in all five track-jacket outfits, up
from 2 of 10 mentions before. It also held for the other two items (10 of 10
and 10 of 10). Criterion 3 went from MISSED (1/5) to MET (5/5), with the same
scenario, scoring rule and target. Every other criterion stayed where it was.

What it didn't fix, and what it may have made worse. I read all 20 after-run
outfits against the 20 before-run ones:

- **The fix was to the evidence, not the agent.** The item handoff was
  already right 5/5 before the change. The revised criterion 3 scores 5/5 in
  both runs. What improved is that the model now writes the full name, which
  makes the outfit easier to match to the listing. It isn't a bug in the loop
  being fixed.
- **New: the model sometimes calls the find "your".** "Layer **your** 90s
  Track Jacket — Navy/White Stripe" appears in 2 of 20 outfits after, and 0 of
  20 before. Writing the title in full seems to make the model treat the find
  like a wardrobe piece, which is exactly what the wardrobe pieces are named
  like. That's a small step toward the invented-ownership problem from
  criterion 5.
- **New: two garbled words in the slip-dress outfits.** "Toughin up" (try 3)
  and "Tourenough for cooler weather" (try 5). There were none in the
  before-run, where the same sentence said "Toughen up". 2 in 20 at
  temperature 0.9 is too few for me to say whether the change caused them or
  they're chance. I'm reporting them because they're new.
- **Criterion 5 under the revised wording is unchanged at 4/5.** The change
  didn't touch `create_fit_card`, which is where that failure lives. The
  after-run miss is softer than the before-run one: it implies ownership ("I
  love throwing it over olive trousers") rather than saying "I own". I scored
  it FAIL to stay consistent with the before-run.

---

## What's Still Broken

<!-- For each criterion still missed: what you'd do, and why you stopped where
     you did. "I ran out of time" is fine if it's true. Pretending nothing is
     left is not. -->

**No original criterion is still missed.** After the one change, all five
are MET (5/5). That doesn't mean nothing is broken. It means my five criteria
don't catch the problems below. In order of how much they matter:

1. **The fit card can still invent clothes the user owns (revised criterion
   5: 4/5 before, 4/5 after).** Before try 4: "every slip dress and
   high-waisted trouser I own". After try 5: "I love throwing it over olive
   trousers". The cause is in `tools.py::create_fit_card`. It's written in the
   first person, it never sees the wardrobe, and it has no empty-wardrobe
   instruction, so it invents a closet to make the caption sound real. **What
   I'd do:** pass `create_fit_card` whether the wardrobe is empty and, if it
   is, tell it not to mention owning other pieces. Then re-run revised
   criterion 5. **Why I stopped:** the brief allows one change per re-run, and
   my one change went to the only criterion that was actually MISSED
   (criterion 3). This one still meets its 4-of-5 target, but only just.

2. **The fix for criterion 3 had side effects I haven't resolved.** After the
   prompt change, 2 of 20 outfits call the find "**your** 90s Track Jacket", so
   the model is treating it like a wardrobe piece. Two outfits also have
   garbled words ("Toughin up", "Tourenough"). Neither showed up in the
   before-run. **What I'd do:** reword the line to "the find, called
   \"<title>\"" so it reads as the new item rather than one of theirs. Then
   run 10 tries instead of 5 to see whether the garbled words are tied to the
   change or are just noise at temperature 0.9. **Why I stopped:** that would
   be a second change, and with only 2 garbled words in 20 outfits I can't yet
   say what's causing them.

3. **Keyword search accepts one-word matches.** "corduroy jacket" returned a
   *track* jacket, and "vintage graphic tee" ranks a silk slip dress third,
   because `_keyword_score` counts any single matching word (Failure Modes
   §2, Loop Trace). Criterion 1 can't catch this. It only checks that the run
   completes, and I tested it on one phrasing that's in the data. **What I'd
   do:** require a match on the garment noun (tee, jacket, dress…) before the
   style words count, and re-test criterion 1 on five *different* phrasings,
   which is what its 4-of-5 reason was actually about. **Why I stopped:** no
   criterion failed on it, so I couldn't justify spending the one change here.

4. **Two criteria were met too easily to tell me much.** Criterion 4 was 5/5
   in both runs, with exactly 3 sentences every time, on one item. I'd raise
   it to 5 of 5 and run it on several items, including one with
   `brand: None`. Criterion 1, as above, needs varied phrasings. Neither one
   would have failed in this unit, so I'm noting them rather than counting
   them as fixed.



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
