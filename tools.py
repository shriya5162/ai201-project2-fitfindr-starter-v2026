"""
The three FitFindr tools.

Each one is a standalone function you can call and test on its own, before any
of them are wired into the loop. Build and test them one at a time — three
untested tools joined by a loop is one problem that looks like six, because you
can't tell which layer is lying to you.

    search_listings(description, size, max_price)  → list[dict]
    suggest_outfit(new_item, wardrobe)             → str
    create_fit_card(outfit, new_item)              → str

All three are stubs right now. They run and they do nothing — that's the
starting position and it's deliberate.

⚠️ Before you write any of them, fill in the **Tool Inventory** section of your
README (Milestone 2). Four lines per tool: what it does, each input with its
type, exactly what it returns, and what it returns when it has nothing to give.
That last line is what your loop branches on. "Returns a list" earns nothing —
the description has to say what is *in* the list.
"""

import re

import config
from generate import generate
from utils.data_loader import load_listings


# ── Tool 1: search_listings ───────────────────────────────────────────────────

def search_listings(
    description: str,
    size: str | None = None,
    max_price: float | None = None,
) -> list[dict]:
    """
    Search the listings data for items matching a description, and optionally a
    size and a price ceiling.

    This is the tool that doesn't call the model, which makes it the easiest one
    to test and the one to move onto MCP in unit 4.

    Args:
        description: keywords describing what the user wants
                     (e.g. "vintage graphic tee").
        size:        a size string to filter by, or None to skip size filtering.
                     Match case-insensitively — "M" should match "S/M".

                     ⚠️ Read the sizes in the data before you reach for a plain
                     substring test. `"s" in "us 9"` is True, and so is
                     `"l" in "xl"`. A filter that returns shoes when someone
                     asked for a small top reads like a broken search, and it
                     will quietly cost you in unit 4 when you test criterion 1.
                     What counts as a size match is part of your spec — decide
                     it and write it into your Tool Inventory.
        max_price:   maximum price, inclusive, or None to skip price filtering.

    Returns:
        A list of matching listing dicts, best match first.
        **Returns an empty list when nothing matches — an empty list, not None,
        and not an exception.** Your loop branches on this.

    Each listing dict has these fields:
        id, title, description, category, style_tags (list), size,
        condition, price (float), colors (list), brand (str or None), platform

    Note that `brand` is None for most listings. That is deliberate and
    realistic — thrift listings often have no brand. If something you write
    assumes a brand is always there, you will find out in unit 4.

    TODO:
        1. Load every listing with load_listings().
        2. Filter by max_price and by size, when each is provided.
        3. Score what's left by keyword overlap with `description`.
        4. Drop anything scoring zero.
        5. Sort by score, highest first, and return the listing dicts —
           at most config.SEARCH_RESULT_LIMIT of them.

    Test it from a terminal before you move on:
        python -c "from tools import search_listings; print(search_listings('graphic tee', max_price=30))"
    """
    results = []

    for listing in load_listings():
        if max_price is not None and listing["price"] > max_price:
            continue
        if size is not None and not _size_matches(size, listing["size"]):
            continue

        score = _keyword_score(description, listing)
        if score == 0:
            continue

        results.append((score, listing))

    results.sort(key=lambda pair: pair[0], reverse=True)
    return [listing for _score, listing in results[: config.SEARCH_RESULT_LIMIT]]


def _size_matches(wanted: str, listing_size: str) -> bool:
    """
    Whether a requested size matches a listing's size string.

    The data has 'M', 'S/M', 'XL (oversized)', 'W30 L30', 'US 8.5' and
    'One Size' in it, so a substring test is no good — 'L' is in 'XL' and 'S'
    is in 'US 9'. Instead: drop anything in parentheses, split on '/' and
    spaces, and require an exact match against one whole token.

        'M'  matches  M, S/M, M/L        but not  XL, W30 L30
        '8'  matches  US 8               but not  US 8.5

    A listing sized 'One Size' matches every request.
    """
    wanted = wanted.strip().upper()
    if not wanted:
        return True

    cleaned = re.sub(r"\(.*?\)", " ", listing_size.upper())
    tokens = [t for t in re.split(r"[/\s]+", cleaned) if t]

    if "ONE" in tokens and "SIZE" in tokens:
        return True

    return wanted in tokens


def _keyword_score(description: str, listing: dict) -> int:
    """
    How many of the query's words show up in this listing.

    Searches the title, the description and the style_tags together, because
    'vintage graphic tee' only finds lst_006 through its tags — its title
    never says 'vintage'. Words under three characters are dropped so 'a' and
    'in' don't score every listing in the file.
    """
    haystack = " ".join([
        listing["title"],
        listing["description"],
        " ".join(listing["style_tags"]),
    ]).lower()

    words = {w for w in re.split(r"[^a-z0-9]+", description.lower()) if len(w) >= 3}
    return sum(1 for word in words if word in haystack)


# ── Tool 2: suggest_outfit ────────────────────────────────────────────────────

def suggest_outfit(new_item: dict, wardrobe: dict) -> str:
    """
    Given a thrifted item and the user's wardrobe, suggest one or two outfits.

    This one calls the model, through `generate()`. You don't need to think
    about rate limits — the adapter handles pacing for you.

    Args:
        new_item: a listing dict — the item the user is considering.
        wardrobe: a wardrobe dict with an 'items' key holding a list of items.
                  **It may be empty.** Handle that.

    Returns:
        A non-empty string with outfit suggestions.
        With an empty wardrobe, return general styling advice rather than
        raising or returning "". Unit 4 has you trigger the empty wardrobe on
        purpose, so decide now what it should do.

    TODO:
        1. Check whether wardrobe['items'] is empty.
        2. If it is, ask the model for general styling ideas for this item.
        3. If it isn't, format the wardrobe items into the prompt and ask for
           specific combinations naming pieces the user already owns.
        4. Return the model's response.

    Test it from a terminal before you move on:
        python -c "from tools import suggest_outfit; from utils.data_loader import get_example_wardrobe, load_listings; print(suggest_outfit(load_listings()[0], get_example_wardrobe()))"
    """
    item = _describe_item(new_item)
    items = wardrobe.get("items") or []

    system = (
        "You are a thrift stylist. Be concrete and brief. Two or three "
        "sentences per outfit, no bullet points, no headings."
    )

    if not items:
        # Empty wardrobe: there is nothing to name, so the prompt says so
        # explicitly. Criterion 5 is about the model not inventing pieces the
        # user never entered.
        prompt = (
            f"Someone is considering this secondhand find:\n{item}\n\n"
            "They have not entered any of their own clothes yet, so you do "
            "not know what they own. Give general styling advice for this "
            "piece in two or three sentences: the silhouette it works with "
            "and the colours it sits next to. Do not name or assume any "
            "specific garment as something they already own."
        )
    else:
        closet = "\n".join(
            f"- {w['name']} ({w['category']}; {', '.join(w['colors'])})"
            for w in items
        )
        prompt = (
            f"Someone is considering this secondhand find:\n{item}\n\n"
            f"Here is everything in their wardrobe:\n{closet}\n\n"
            "Suggest one or two outfits pairing the find with pieces from "
            "that list. Name each piece exactly as it is written above, and "
            "name the find by its title. Use only pieces from the list."
        )

    return generate(prompt, system=system)


def _describe_item(item: dict) -> str:
    """Flatten a listing dict into the lines a prompt needs."""
    lines = [
        f"Title: {item['title']}",
        f"Category: {item['category']}",
        f"Colours: {', '.join(item['colors'])}",
        f"Style: {', '.join(item['style_tags'])}",
        f"Size: {item['size']}, condition {item['condition']}",
        f"Price: ${item['price']:.0f} on {item['platform']}",
    ]
    if item.get("brand"):  # brand is None on most listings
        lines.append(f"Brand: {item['brand']}")
    return "\n".join(lines)


# ── Tool 3: create_fit_card ───────────────────────────────────────────────────

def create_fit_card(outfit: str, new_item: dict) -> str:
    """
    Write a short caption someone would actually post about the find.

    This calls the model too.

    Args:
        outfit:   the outfit suggestion string from suggest_outfit().
        new_item: the listing dict for the item.

    Returns:
        A two-to-four sentence caption.
        If `outfit` is empty or whitespace, return a descriptive message rather
        than raising.

    The caption should read like a real post rather than a product description,
    mention the item and its price and platform once each, and be specific about
    the vibe.

    It should also come out **differently for different inputs**. If you run
    this three times on the same item and get three word-for-word identical
    strings, it's one of two things, and both are near the top of `config.py`:

        • CACHE_ENABLED — the adapter handed back an answer it already had
        • TEMPERATURE   — at 0.0 the model gives the same words every time

    TODO:
        1. Guard against an empty or whitespace-only `outfit`.
        2. Build a prompt with the item details and the outfit.
        3. Call generate() and return the response.

    Test it from a terminal before you move on:
        python -c "from tools import create_fit_card; from utils.data_loader import load_listings; print(create_fit_card('jeans and white sneakers', load_listings()[0]))"
    """
    if not outfit or not outfit.strip():
        return "Can't write a fit card without an outfit."

    system = (
        "You write short captions for secondhand fashion posts. Sound like a "
        "person posting a find, not like a product listing."
    )
    prompt = (
        f"The find:\n{_describe_item(new_item)}\n\n"
        f"How they are wearing it:\n{outfit.strip()}\n\n"
        "Write a caption of two to four sentences. Mention the price once and "
        "the platform once, both exactly as given above. Be specific about the "
        "vibe of the piece. No hashtags, no headings."
    )

    return generate(prompt, system=system)
