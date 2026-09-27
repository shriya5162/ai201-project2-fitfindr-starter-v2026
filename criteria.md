# Acceptance criteria — FitFindr

Five criteria that say what "working" means for this agent, written in unit 3
**before** any results existed.

An acceptance criterion names a target: a number, a count, a rate, or something
a person could plainly observe. *"The agent handles errors"* is an opinion.
*"When search returns nothing, the agent stops before calling the second tool,
in 5 of 5 tries"* is a criterion.

Under each one, write a sentence or two on **why that target** and not a
stricter one. A reason that says something about your tools, your loop, or the
data earns credit; *"80% seemed reasonable"* does not.

> Missing your own targets next unit costs you nothing. Setting a target so
> easy you can't miss it does.

**Two are written for you. You write three.**

---

## 1. A matching query completes all three tools

Given a query that matches at least one listing, the agent completes all three
tool calls and returns a fit card — in at least 4 of 5 tries.

**Why this target:** My search is plain keyword overlap against `title`,
`description` and `style_tags`, so some phrasings of a thing that *is* in the
data will score zero and stop the run early. 4 of 5 leaves room for that
without excusing a broken loop.

---

## 2. An impossible query stops before the second tool

Given a query that matches no listings, the agent stops before calling
`suggest_outfit` and returns a message naming what to change — 5 of 5 tries.

**Why this target:** No model runs on this path — it's one `if` on an empty
list. Nothing can vary between tries, so anything under 5 of 5 is a bug, not
variance.

---

## 3. The item search found is the item the next tool got

Across 5 runs with matching queries, the `id` in `session["selected_item"]` is
the `id` of the item whose title appears in `session["outfit_suggestion"]` —
5 of 5 tries.

**Why this target:** Nothing between those two points calls the model; it's a
dict handed from the session into `suggest_outfit`. A mismatch means I passed
the wrong item or rebuilt it instead of reading it back, so there's no
variance to allow for.


---

## 4. The fit card names the price and platform, and stays caption-length

Each fit card names the item's price and its platform exactly once and runs
2 to 4 sentences — in at least 4 of 5 tries.

**Why this target:** The words should change run to run, so I'm scoring what
has to be there rather than the wording. 4 of 5 because the model writes it:
one card in five drifting to a fifth sentence or dropping the platform is the
tool behaving normally. Price and platform are the two facts a caption is
useless without, and unlike `brand` they're never null.


---

## 5. An empty wardrobe still produces a card, with nothing invented

Run with `--empty-wardrobe`, the agent still returns a non-empty fit card and
the outfit suggestion names no specific garment as something the user already
owns — in at least 4 of 5 tries.

**Why this target:** With `wardrobe["items"]` empty there is nothing to style
against, and the obvious failure is the model confidently pairing the find
with jeans the user never entered. 4 of 5 rather than 5 of 5 because avoiding
that is down to my prompt holding the model back, not to an `if` statement.


---

<!-- ─────────────────────────────────────────────────────────────────────────
     UNIT 4 — read this before you change anything above.

     If a criterion turns out to be BROKEN rather than merely unmet, you can
     revise it, and that earns credit. But never delete or edit the original
     line. Add the revision underneath it, like this:

         ## 4. Something about the fit card

         The fit card is different every time.

         **Why this target:** ...

         > **Revised in unit 4:** For 5 different items, the 5 fit cards share
         > no opening sentence.
         >
         > **Why revised:** "different" wasn't checkable — two cards that
         > differed by one word still counted. The new version is something I
         > can actually score.

     That's a revision because the criterion couldn't be MEASURED.

     Lowering a target because you missed it is not a revision, and it costs
     you the point:

         ✗ "I said the empty search stops it 5 of 5 times, but I got 3 of 5,
            so 3 of 5 is more realistic."

     A number you missed stays where it is, gets diagnosed, and gets a fix
     attempted. That's where the points are.
     ───────────────────────────────────────────────────────────────────────── -->
