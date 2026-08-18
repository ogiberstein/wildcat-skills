"""The catalogue, rendered for a reader.

`docs/catalogue.md` describes itself as a rendering rather than a second source.
That was a claim about intent until this existed: the document was written once
by hand and a test checked the two agreed, which catches drift and offers no way
to fix it. A reader who added a law was told the document was wrong and left to
work out what it should have said.

So the rendering has a renderer, the renderer is the only thing that writes that
file, and a test compares the committed bytes with what this produces. Drift is
then a one-line fix rather than a transcription exercise.
"""

FAMILY_BLURB = {
    "conservation": (
        "What the system holds, owes and has promised in one state. The sums agree\n"
        "or they do not; no history is needed."
    ),
    "accrual": (
        "How debt and claims move with time. The violation is in a transition, not\n"
        "one state."
    ),
    "claims": (
        "What a recorded withdrawal claim is owed and in what order. These laws need\n"
        "the withdrawal-queue extension; a target without one reverts on the read."
    ),
}

#: Spelled out to twelve, past which the numeral reads better than the word. A
#: corpus with more laws than this has a bigger problem than its preamble.
WORDS = (
    "No", "One", "Two", "Three", "Four", "Five", "Six",
    "Seven", "Eight", "Nine", "Ten", "Eleven", "Twelve",
)


def counted(number, singular, plural, capitalised=False):
    """A spelled-out count, capitalised only where a sentence starts."""
    word = WORDS[number] if number < len(WORDS) else str(number)
    if not capitalised:
        word = word.lower() if word[0].isupper() and not word.isdigit() else word
    return "%s %s" % (word, singular if number == 1 else plural)


PREAMBLE = """# The catalogue

Pandects supplies executable laws for credit contracts, each paired with a
deliberately broken specimen and a reduced counterexample. Use Fizz to generate
a protocol-specific harness. The corpus holds %s; broader families remain in
the planning specification.

%s in %s, rendered from `catalogue/pandects.json`. Regenerate it with
`python3 scripts/pandects.py render`; a byte comparison rejects hand edits.

Every law executes, catches a broken specimen, has a reduced replay, states its
applicability, justifies its bounds and judges without reverting.
`python3 scripts/pandects.py check` refuses anything with fewer than six parts.
"""


def bounds_text(bounds):
    if bounds == "exact":
        return "exact"
    if not isinstance(bounds, dict):
        return str(bounds)
    return "%s (%s)" % (bounds.get("tolerance"), bounds.get("arithmetic"))


def families_in(catalogue):
    """Every family that has a law filed under it, in catalogue order.

    Driven by the catalogue rather than by the blurbs above. A renderer that
    looped over its own vocabulary would silently drop every law filed under a
    family it had not been told about, and the drift test cannot see that: it
    compares the document against this renderer, so both would be wrong the same
    way.
    """
    seen = []
    for law in catalogue.laws:
        family = law.get("family")
        if family is not None and family not in seen:
            seen.append(family)
    return seen


def render(catalogue):
    """The whole document, as a string ending in one newline."""
    families = families_in(catalogue)
    # Both counts are derived. An earlier round fixed the second and left the
    # first, which is how a document ends up disagreeing with itself three lines
    # apart while every test passes.
    preamble = PREAMBLE % (
        counted(len(catalogue.laws), "law", "laws"),
        counted(len(catalogue.laws), "law", "laws", capitalised=True),
        counted(len(families), "family", "families"),
    )
    lines = preamble.rstrip("\n").split("\n") + [""]

    for family in families:
        laws = [law for law in catalogue.laws if law.get("family") == family]
        blurb = FAMILY_BLURB.get(family)
        lines += ["## %s" % family.capitalize(), ""]
        if blurb:
            lines += [blurb, ""]
        for law in laws:
            applicability = law.get("applicability") or {}
            lines += ["### `%s`" % law.id, "", "> %s" % law.get("statement"), ""]
            lines += ["- Component: `%s`" % law.get("component")]
            lines += ["- Specimen: `%s`" % law.get("specimen")]
            lines += ["- Counterexample: `%s`" % law.get("counterexample")]
            lines += ["- Bounds: %s" % bounds_text(law.get("bounds"))]
            lines += [
                "- Reads: %s"
                % ", ".join("`%s`" % name for name in applicability.get("requires", []))
            ]
            lines += [
                "",
                "Applies to %s. Assuming:" % applicability.get("accounting_model"),
                "",
            ]
            lines += ["- %s" % assumption for assumption in applicability.get("assumes", [])]
            lines += [""]

    # A family the catalogue declares and files nothing under never appears,
    # because the headings come from the laws rather than from the declarations.
    # A heading with nothing beneath it reads as a section somebody deleted.
    return "\n".join(lines).rstrip("\n") + "\n"
