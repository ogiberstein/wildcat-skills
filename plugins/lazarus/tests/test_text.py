"""Whether a string a person will read actually shows them something.

The invisible case is the one worth testing hardest. It has been recorded as a
lead twice in this marketplace and closed nowhere, because `str.strip` does not
treat U+200B as whitespace and every presence check ever written passes it.

The characters are written as escapes rather than pasted, so a reader of this
file can see which one each test means.
"""

import unittest

from lazarus_lib.text import INVISIBLE_CATEGORIES, visible

ZERO_WIDTH_SPACE = "​"
ZERO_WIDTH_NON_JOINER = "‌"
ZERO_WIDTH_JOINER = "‍"
WORD_JOINER = "⁠"
ZERO_WIDTH_NO_BREAK_SPACE = "﻿"
LEFT_TO_RIGHT_MARK = "‎"
RIGHT_TO_LEFT_MARK = "‏"
IDEOGRAPHIC_SPACE = "　"
NO_BREAK_SPACE = " "


class VisibleTests(unittest.TestCase):
    def test_ordinary_text_is_visible(self):
        for value in ("a", "plan.json", "a b", "dir one/file two", "0", "-"):
            with self.subTest(value=value):
                self.assertTrue(visible(value))

    def test_non_latin_text_is_visible(self):
        """Refusing anything unfamiliar would refuse most of the world's names."""
        for value in ("مرحبا", "日本語",
                      "Привет", "ἐλ"):
            with self.subTest(value=value):
                self.assertTrue(visible(value))

    def test_whitespace_alone_is_not_visible(self):
        for value in ("", " ", "   ", "\t", "\n", "\r\n",
                      NO_BREAK_SPACE, IDEOGRAPHIC_SPACE):
            with self.subTest(value=repr(value)):
                self.assertFalse(visible(value))

    def test_format_characters_alone_are_not_visible(self):
        """The quiet case. `str.strip` leaves these in place, so a name made of
        them passes every length and presence check and displays as empty."""
        for value in (
            ZERO_WIDTH_SPACE,
            ZERO_WIDTH_NON_JOINER,
            ZERO_WIDTH_JOINER,
            WORD_JOINER,
            ZERO_WIDTH_NO_BREAK_SPACE,
            LEFT_TO_RIGHT_MARK,
            ZERO_WIDTH_SPACE + WORD_JOINER + ZERO_WIDTH_NO_BREAK_SPACE,
            "\x00",
            "\x07",
        ):
            with self.subTest(value=repr(value)):
                self.assertFalse(visible(value))

    def test_two_names_that_look_identical_are_told_apart(self):
        """The reason this matters for a path. Both are visible, and they are
        different strings, so nothing here silently merges them; the point is
        that neither is invisible while looking like the other."""
        plain = "component"
        padded = "component" + ZERO_WIDTH_SPACE
        self.assertTrue(visible(plain))
        self.assertTrue(visible(padded))
        self.assertNotEqual(plain, padded)

    def test_one_visible_character_is_enough(self):
        """The question is whether anything shows, not whether the text is tidy.
        A name carrying a directionality mark beside real letters is a name."""
        for value in (
            "a" + ZERO_WIDTH_SPACE,
            ZERO_WIDTH_SPACE + "a",
            LEFT_TO_RIGHT_MARK + "a" + RIGHT_TO_LEFT_MARK,
            " a ",
            IDEOGRAPHIC_SPACE + "a",
        ):
            with self.subTest(value=repr(value)):
                self.assertTrue(visible(value))

    def test_anything_that_is_not_a_string_is_not_visible(self):
        for value in (None, 0, 1, True, False, [], {}, ["a"], object()):
            with self.subTest(value=repr(value)):
                self.assertFalse(visible(value))

    def test_the_refused_categories_are_named_rather_than_inline(self):
        """A reader should see which categories are refused without reading the
        loop, and `Zs` must not be among them: an ordinary space between two
        letters is legitimate."""
        self.assertIn("Cf", INVISIBLE_CATEGORIES)
        self.assertIn("Cc", INVISIBLE_CATEGORIES)
        self.assertNotIn("Zs", INVISIBLE_CATEGORIES)


if __name__ == "__main__":
    unittest.main()
