"""Tests for text_cleaner module."""

import pytest
from readable.text_cleaner import clean_text_for_tts, _naturalize_code, clean_text_aggressive


class TestCleanTextForTTS:
    """Tests for clean_text_for_tts function."""

    def test_empty_text(self):
        """Empty text returns empty."""
        assert clean_text_for_tts("") == ""
        assert clean_text_for_tts(None) is None

    def test_removes_http_urls(self):
        """HTTP URLs are removed."""
        text = "Check out https://example.com/foo for details"
        result = clean_text_for_tts(text)
        assert "https://" not in result
        assert "example.com" not in result
        assert "Check out" in result
        assert "for details" in result

    def test_removes_www_urls(self):
        """www URLs are removed."""
        text = "Visit www.example.com/page for more info"
        result = clean_text_for_tts(text)
        assert "www." not in result
        assert "example.com" not in result

    def test_simplifies_long_paths(self):
        """Long file paths are simplified to basename."""
        text = "Edit /Users/jesper/Projects/Dev/Tools/Readable/src/main.py"
        result = clean_text_for_tts(text)
        assert "main.py" in result
        # The long path should be simplified
        assert "/Users/jesper/Projects/Dev/Tools" not in result

    def test_converts_markdown_links(self):
        """Markdown links become plain text."""
        text = "See [the documentation](https://docs.example.com) for help"
        result = clean_text_for_tts(text)
        assert result == "See the documentation for help"

    def test_naturalizes_inline_code(self):
        """Inline code is naturalized."""
        text = "Call `getUserData()` to fetch the data"
        result = clean_text_for_tts(text)
        assert "get user data" in result
        assert "`" not in result
        assert "()" not in result

    def test_removes_bold_markdown(self):
        """Bold markdown is removed but text kept."""
        text = "This is **important** text"
        result = clean_text_for_tts(text)
        assert result == "This is important text"

    def test_removes_italic_markdown(self):
        """Italic markdown is removed but text kept."""
        text = "This is *emphasized* text"
        result = clean_text_for_tts(text)
        assert result == "This is emphasized text"

    def test_normalizes_multiple_spaces(self):
        """Multiple spaces become single space."""
        text = "Too    many   spaces"
        result = clean_text_for_tts(text)
        assert "  " not in result
        assert "Too many spaces" in result

    def test_normalizes_excessive_newlines(self):
        """More than 2 newlines become 2."""
        text = "Para 1\n\n\n\n\nPara 2"
        result = clean_text_for_tts(text)
        assert "\n\n\n" not in result
        assert "Para 1" in result
        assert "Para 2" in result

    def test_preserves_normal_text(self):
        """Normal text without special content is preserved."""
        text = "This is a normal sentence without URLs or code."
        result = clean_text_for_tts(text)
        assert result == text

    def test_combined_cleaning(self):
        """Multiple cleaning operations work together."""
        text = """Check the docs at https://example.com/docs.

        Call `fetchUserProfile()` to get user data.

        See [API Reference](https://api.example.com) for details."""

        result = clean_text_for_tts(text)

        # URLs removed
        assert "https://" not in result
        # Code naturalized
        assert "fetch user profile" in result.lower()
        # Link converted
        assert "API Reference" in result
        # No URL in link
        assert "api.example.com" not in result


class TestNaturalizeCode:
    """Tests for _naturalize_code helper function."""

    def test_camel_case(self):
        """camelCase becomes words."""
        import re
        match = re.match(r'`([^`]+)`', '`getUserData`')
        result = _naturalize_code(match)
        assert result == "get user data"

    def test_pascal_case(self):
        """PascalCase becomes words."""
        import re
        match = re.match(r'`([^`]+)`', '`UserProfile`')
        result = _naturalize_code(match)
        assert result == "user profile"

    def test_snake_case(self):
        """snake_case becomes words."""
        import re
        match = re.match(r'`([^`]+)`', '`get_user_data`')
        result = _naturalize_code(match)
        assert result == "get user data"

    def test_removes_parentheses(self):
        """Function call parentheses are removed."""
        import re
        match = re.match(r'`([^`]+)`', '`getData()`')
        result = _naturalize_code(match)
        assert "()" not in result
        assert "get data" in result

    def test_removes_params(self):
        """Function parameters are removed."""
        import re
        match = re.match(r'`([^`]+)`', '`getData(userId, options)`')
        result = _naturalize_code(match)
        assert "userId" not in result
        assert "get data" in result

    def test_acronyms(self):
        """Acronyms are handled."""
        import re
        match = re.match(r'`([^`]+)`', '`XMLParser`')
        result = _naturalize_code(match)
        assert "xml parser" in result

    def test_skips_long_code(self):
        """Code over 50 chars is returned as-is."""
        import re
        long_code = "a" * 60
        match = re.match(r'`([^`]+)`', f'`{long_code}`')
        result = _naturalize_code(match)
        assert result == long_code

    def test_skips_paths(self):
        """Paths with slashes are returned as-is."""
        import re
        match = re.match(r'`([^`]+)`', '`/path/to/file`')
        result = _naturalize_code(match)
        assert result == "/path/to/file"


class TestCleanTextAggressive:
    """Tests for clean_text_aggressive function."""

    def test_removes_code_blocks(self):
        """Fenced code blocks are removed."""
        text = """Some text
```python
def foo():
    pass
```
More text"""
        result = clean_text_aggressive(text)
        assert "def foo" not in result
        assert "Some text" in result
        assert "More text" in result

    def test_removes_html_tags(self):
        """HTML tags are removed."""
        text = "This is <b>bold</b> and <em>italic</em>"
        result = clean_text_aggressive(text)
        assert "<b>" not in result
        assert "</b>" not in result
        assert "bold" in result

    def test_removes_latex_math(self):
        """LaTeX math expressions are removed."""
        text = "The equation $x^2 + y^2 = z^2$ is famous"
        result = clean_text_aggressive(text)
        assert "$" not in result
        assert "x^2" not in result
        assert "famous" in result

    def test_expands_abbreviations(self):
        """Common abbreviations are expanded."""
        text = "e.g. this example, i.e. meaning"
        result = clean_text_aggressive(text)
        assert "for example" in result
        assert "that is" in result
