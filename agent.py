"""
The FitFindr planning loop.

This is the file that makes FitFindr an agent rather than a script. It decides
which tool to run next based on what the last one returned.

If your loop calls all three tools no matter what comes back, you have a list
of function calls. A loop looks at the last result before it picks the next
step. **That branch is the graded part of this unit.**

Build and test your three tools in `tools.py` first. Then come here.

    python agent.py          runs both example paths below
"""

import re

import config
import trace
from tools import suggest_outfit, create_fit_card
from generate import ModelUnavailable
from mcp_client import call_tool, MCPError


# ── session state ─────────────────────────────────────────────────────────────

def new_session(query: str, wardrobe: dict) -> dict:
    """
    A fresh session for one user interaction.

    The session is the single source of truth for a run. Every tool result goes
    in here, and the next tool reads it back out.

    You could pass values straight from one call to the next. It would work,
    and you would not be able to test it — you can't print a variable you have
    already overwritten. Going through the session is what makes the state
    visible, and unit 4 has you write a criterion about exactly that.

    Add fields if you need them.
    """
    return {
        "query": query,              # what the user typed
        "parsed": {},                # description / size / max_price you pulled out of it
        "search_results": [],        # everything search_listings returned
        "selected_item": None,       # the one you chose — goes into suggest_outfit
        "wardrobe": wardrobe,        # the user's wardrobe
        "outfit_suggestion": None,   # what suggest_outfit returned
        "fit_card": None,            # what create_fit_card returned
        "error": None,               # set when the run ended early
    }


# ── planning loop ─────────────────────────────────────────────────────────────

def run_agent(query: str, wardrobe: dict) -> dict:
    """
    Run the loop once and return the finished session.

    Args:
        query:    what the user asked for, in plain language
                  (e.g. "vintage graphic tee under $30, size M").
        wardrobe: a wardrobe dict — get_example_wardrobe() or
                  get_empty_wardrobe() from utils/data_loader.py.

    Returns:
        The session dict. **Check session["error"] first** — if it isn't None,
        the run ended early and the later fields will still be None.

    ─────────────────────────────────────────────────────────────────────────
    TODO — build this, following the branch rule you wrote in Milestone 2.

      1. Start a session with new_session().

      2. Count the times round the loop, and call trace.check_iterations(count)
         on each one before you go again. It raises when the count passes
         MAX_ITERATIONS in config.py — see trace.py.

      3. Parse the query into a description, a size, and a max_price. Regex,
         string splitting, or asking the model are all fine — say which you
         chose in your README. Put the result in session["parsed"].

      4. Call search_listings() with what you parsed.
         Put the results in session["search_results"].

         ⚠️ THIS IS THE BRANCH. If nothing came back:
              - put a message in session["error"] saying what the user could
                change — "No results" is not that message
              - return the session
              - do NOT call suggest_outfit with nothing

      5. Choose an item — the first result is fine. Put it in
         session["selected_item"].

      6. Call suggest_outfit() with the selected item and the wardrobe.
         Put the result in session["outfit_suggestion"].

      7. Call create_fit_card() with the outfit and the item.
         Put the result in session["fit_card"].

      8. Return the session.

    ─────────────────────────────────────────────────────────────────────────
    IN UNIT 4 you come back and add two things:

      • Trace calls. One per step. `trace.step("search_listings", inputs=...,
        returned=...)` — see trace.py. Your README needs the output.

      • A handler for ModelUnavailable, so a bad key produces a message rather
        than a stack trace. The import is already at the top of this file.
    """
    session = new_session(query, wardrobe)

    # What to do next. Each pass through the loop reads the session, does one
    # step, and decides what the next step is — that decision is what makes
    # this a loop rather than three calls in a row.
    next_step = "parse"
    count = 0

    while next_step != "done":
        count += 1
        trace.check_iterations(count)

        if next_step == "parse":
            session["parsed"] = parse_query(session["query"])
            trace.step("parse_query", inputs=session["query"],
                       returned=_kv(session["parsed"]))
            next_step = "search"

        elif next_step == "search":
            parsed = session["parsed"]
            # search_listings now goes through the MCP server (mcp_server.py)
            # rather than being imported from tools.py. Same inputs, same list
            # of dicts back.
            try:
                session["search_results"] = call_tool("search_listings", {
                    "description": parsed["description"],
                    "size": parsed["size"],
                    "max_price": parsed["max_price"],
                })
            except MCPError as exc:
                session["error"] = _search_unreachable_message(exc)
                trace.step("search_listings (via MCP)", inputs=_kv(parsed),
                           returned=f"MCPError: {exc}",
                           note="branch: server unreachable, stopping")
                next_step = "done"
                continue

            # ── THE BRANCH ───────────────────────────────────────────────────
            # Read the results back out of the session, not out of a local
            # variable, so what the branch sees is what the session holds.
            if not session["search_results"]:
                session["error"] = _nothing_found_message(parsed)
                note = "branch: empty, stopping before suggest_outfit"
                next_step = "done"
            else:
                note = "branch: results found, continuing"
                next_step = "select"
            trace.step("search_listings (via MCP)", inputs=_kv(parsed),
                       returned=session["search_results"], note=note)

        elif next_step == "select":
            session["selected_item"] = session["search_results"][0]
            trace.step("select_item",
                       inputs=f"{len(session['search_results'])} results",
                       returned=session["selected_item"],
                       note="first result = highest keyword score")
            next_step = "outfit"

        elif next_step == "outfit":
            wardrobe_items = session["wardrobe"].get("items") or []
            try:
                session["outfit_suggestion"] = suggest_outfit(
                    new_item=session["selected_item"],
                    wardrobe=session["wardrobe"],
                )
            except ModelUnavailable as exc:
                session["error"] = _model_down_message(
                    session["selected_item"], "suggest an outfit", exc)
                trace.step("suggest_outfit",
                           inputs=_kv({"new_item": session["selected_item"]["title"],
                                       "wardrobe_items": len(wardrobe_items)}),
                           returned=f"ModelUnavailable: {exc}",
                           note="model unreachable, stopping")
                next_step = "done"
                continue
            trace.step("suggest_outfit",
                       inputs=_kv({"new_item": session["selected_item"]["title"],
                                   "wardrobe_items": len(wardrobe_items)}),
                       returned=session["outfit_suggestion"],
                       note="" if wardrobe_items else "empty wardrobe: general advice")
            next_step = "fit_card"

        elif next_step == "fit_card":
            try:
                session["fit_card"] = create_fit_card(
                    outfit=session["outfit_suggestion"],
                    new_item=session["selected_item"],
                )
            except ModelUnavailable as exc:
                session["error"] = _model_down_message(
                    session["selected_item"], "write the fit card", exc)
                trace.step("create_fit_card",
                           inputs=_kv({"new_item": session["selected_item"]["title"],
                                       "outfit": session["outfit_suggestion"]}),
                           returned=f"ModelUnavailable: {exc}",
                           note="model unreachable, stopping")
                next_step = "done"
                continue
            trace.step("create_fit_card",
                       inputs=_kv({"new_item": session["selected_item"]["title"],
                                   "outfit": session["outfit_suggestion"]}),
                       returned=session["fit_card"])
            next_step = "done"

    return session


# ── parsing the query ─────────────────────────────────────────────────────────

def parse_query(query: str) -> dict:
    """
    Pull a description, a size and a price ceiling out of what the user typed.

    Regex, not the model — this runs before any tool call, and spending a
    request to find a dollar sign would double the cost of every run.

        "vintage graphic tee under $30, size M"
        → {"description": "vintage graphic tee", "size": "M", "max_price": 30.0}

    Whatever the two patterns match is cut out of the string; what's left is
    the description.
    """
    remaining = query

    # Either a dollar sign — "$30" — or a price word in front of a number —
    # "under 30". A bare number on its own is left alone, because "size 8"
    # and "90s" are numbers too.
    max_price = None
    price_match = (
        re.search(r"(?:under|below|less than|max|up to)?\s*\$\s*(\d+(?:\.\d+)?)", remaining, re.I)
        or re.search(r"(?:under|below|less than|max|up to)\s+(\d+(?:\.\d+)?)\s*(?:dollars|bucks)?", remaining, re.I)
    )
    if price_match:
        max_price = float(price_match.group(1))
        remaining = remaining[: price_match.start()] + " " + remaining[price_match.end():]

    size = None
    size_match = re.search(r"\bsize\s+([a-z0-9./]+)", remaining, re.I)
    if size_match:
        size = size_match.group(1).strip(".,").upper()
        remaining = remaining[: size_match.start()] + " " + remaining[size_match.end():]

    # Words that describe the request rather than the garment. Left in, they
    # score nothing and just add noise to the description.
    filler = {"looking", "for", "a", "an", "the", "some", "want", "need",
              "find", "me", "in", "i", "im", "am", "my"}
    words = [w for w in re.split(r"[\s,]+", remaining) if w]
    description = " ".join(w for w in words if w.lower().strip(".,") not in filler)

    return {
        "description": description.strip(),
        "size": size,
        "max_price": max_price,
    }


def _nothing_found_message(parsed: dict) -> str:
    """
    What to say when the search comes back empty.

    "No results" tells someone nothing about what to do next, so this names
    the three filters back to them — the two they set and the words they used
    — because those are the only things they can actually change.
    """
    tried = [f'the words "{parsed["description"]}"']
    if parsed["size"]:
        tried.append(f'size {parsed["size"]}')
    if parsed["max_price"] is not None:
        tried.append(f'a price under ${parsed["max_price"]:.0f}')

    return (
        "Nothing in the 40 listings matches " + ", ".join(tried) + ". "
        "Try raising the price, dropping the size, or using plainer words — "
        "the listings are tagged things like 'vintage', 'y2k', 'grunge', "
        "'streetwear' and 'graphic tee', so those find more than a brand name "
        "or a specific garment will."
    )


def _model_down_message(item: dict, task: str, exc: Exception) -> str:
    """
    What to say when suggest_outfit or create_fit_card can't reach the model.

    The search already worked by this point, so the find is still worth
    showing — the message leads with it, then says which step broke and why.
    `exc` is generate.py's explanation (bad key, no network, bad model name),
    which already names the thing to check.
    """
    return (
        f"Found {item['title']} — ${item['price']:.0f} on {item['platform']} — "
        f"but couldn't {task}: the model couldn't be reached. {exc} "
        "Once that's fixed, ask again; the search itself worked."
    )


def _search_unreachable_message(exc: Exception) -> str:
    """What to say when the MCP server holding search_listings won't answer."""
    return (
        "Couldn't search the listings: the search server (mcp_server.py) "
        "didn't respond, so nothing was searched. Run `python mcp_server.py` "
        "on its own to see why it won't start, fix that, then ask again."
    )


def _kv(d: dict) -> str:
    """One-line key=value rendering for the trace, which otherwise only shows a dict's keys."""
    return ", ".join(f"{k}={v!r}" for k, v in d.items())


# ── running it directly ───────────────────────────────────────────────────────

def _show(session: dict) -> None:
    if session["error"]:
        print(f"  stopped: {session['error']}")
        print(f"  fit_card is {session['fit_card']!r} — it should still be None here")
        return

    item = session["selected_item"] or {}
    print(f"  found:    {item.get('title')} — ${item.get('price')} on {item.get('platform')}")
    print(f"  outfit:   {session['outfit_suggestion']}")
    print(f"  fit card: {session['fit_card']}")


if __name__ == "__main__":
    from utils.data_loader import get_example_wardrobe

    print("=== A query the data can match ===")
    _show(run_agent(
        query="looking for a vintage graphic tee under $30",
        wardrobe=get_example_wardrobe(),
    ))

    print("\n=== A query it can't ===")
    _show(run_agent(
        query="designer ballgown size XXS under $5",
        wardrobe=get_example_wardrobe(),
    ))

    print(
        "\nThe second one should stop before the fit card. If both paths look "
        "the same,\nthe branch isn't doing anything yet."
    )
