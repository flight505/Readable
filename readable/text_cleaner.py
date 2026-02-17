"""Lightweight text cleaning for TTS output."""

import re
from .logger import get_logger

logger = get_logger("readable.text_cleaner")


def clean_text_for_tts(text: str) -> str:
    """
    Clean text for better TTS output.

    Applies lightweight cleaning optimized for clipboard text:
    - Removes URLs
    - Simplifies long file paths
    - Converts markdown links to plain text
    - Naturalizes inline code (camelCase → words)
    - Normalizes whitespace

    Args:
        text: Raw text to clean

    Returns:
        Cleaned text suitable for TTS
    """
    if not text:
        return text

    original_length = len(text)

    # 1. Remove URLs (http/https)
    text = re.sub(r'https?://[^\s<>\[\]()]+', '', text)

    # 2. Remove www. URLs without protocol
    text = re.sub(r'\bwww\.[^\s<>\[\]()]+', '', text)

    # 3. Simplify long file paths (4+ directory levels → basename)
    # Matches paths like /foo/bar/baz/qux/file.txt → file.txt
    text = re.sub(
        r'(?:^|[\s"\'(])(/[^/\s]+){4,}/([^/\s]+)',
        r' \2',
        text
    )

    # 4. Convert markdown links: [text](url) → text
    text = re.sub(r'\[([^\]]+)\]\([^)]*\)', r'\1', text)

    # 5. Naturalize inline code: `getUserData()` → get user data
    text = re.sub(r'`([^`]+)`', _naturalize_code, text)

    # 6. Clean up markdown emphasis that might sound weird
    # Remove ** and __ (bold markers) but keep the text
    text = re.sub(r'\*\*([^*]+)\*\*', r'\1', text)
    text = re.sub(r'__([^_]+)__', r'\1', text)

    # 7. Remove single * and _ (italic markers) but keep text
    text = re.sub(r'(?<!\*)\*([^*]+)\*(?!\*)', r'\1', text)
    text = re.sub(r'(?<!_)_([^_]+)_(?!_)', r'\1', text)

    # 8. Clean up multiple spaces (but preserve intentional newlines)
    text = re.sub(r'[ \t]{2,}', ' ', text)

    # 9. Clean up excessive newlines (more than 2 → 2)
    text = re.sub(r'\n{3,}', '\n\n', text)

    # 10. Strip leading/trailing whitespace from each line
    lines = [line.strip() for line in text.split('\n')]
    text = '\n'.join(lines)

    cleaned_length = len(text)
    if original_length != cleaned_length:
        logger.debug(
            f"Text cleaned: {original_length} → {cleaned_length} chars "
            f"({original_length - cleaned_length} removed)"
        )

    return text.strip()


def _naturalize_code(match: re.Match) -> str:
    """
    Convert code-style text to natural speech.

    Examples:
        getUserData() → get user data
        MAX_RETRY_COUNT → max retry count
        someVariable → some variable

    Args:
        match: Regex match object with code in group 1

    Returns:
        Naturalized text
    """
    code = match.group(1)

    # Skip very long code snippets (likely actual code, not identifiers)
    if len(code) > 50:
        return code

    # Skip if it looks like a path or URL
    if '/' in code or '\\' in code or '://' in code:
        return code

    # Replace underscores with spaces
    result = code.replace('_', ' ')

    # Insert spaces before uppercase letters (camelCase/PascalCase)
    result = re.sub(r'([a-z])([A-Z])', r'\1 \2', result)

    # Handle consecutive uppercase (acronyms): XMLParser → XML Parser
    result = re.sub(r'([A-Z]+)([A-Z][a-z])', r'\1 \2', result)

    # Remove function call parentheses
    result = re.sub(r'\(\s*\)', '', result)
    result = re.sub(r'\([^)]*\)', '', result)  # Also remove params

    # Convert to lowercase for natural speech
    result = result.lower()

    # Clean up any double spaces created
    result = re.sub(r'\s+', ' ', result)

    return result.strip()


def clean_text_aggressive(text: str) -> str:
    """
    More aggressive text cleaning for TTS.

    In addition to standard cleaning, this:
    - Removes code blocks entirely
    - Removes LaTeX math expressions
    - Removes HTML tags
    - Expands common abbreviations

    Use with caution - may remove desired content.

    Args:
        text: Raw text to clean

    Returns:
        Aggressively cleaned text
    """
    if not text:
        return text

    # Remove fenced code blocks FIRST (before standard cleaning modifies backticks)
    # Match ```...``` including any language identifier
    text = re.sub(r'```[\s\S]*?```', '', text)

    # Remove indented code blocks (4 spaces or tab at start)
    text = re.sub(r'^(?:    |\t)[^\n]*$', '', text, flags=re.MULTILINE)

    # Remove LaTeX math expressions
    text = re.sub(r'\$\$[^$]+\$\$', '', text)  # Display math
    text = re.sub(r'\$[^$]+\$', '', text)  # Inline math

    # Remove HTML tags
    text = re.sub(r'<[^>]+>', '', text)

    # Expand common abbreviations
    abbreviations = {
        r'\be\.g\.': 'for example',
        r'\bi\.e\.': 'that is',
        r'\betc\.': 'etcetera',
        r'\bvs\.': 'versus',
        r'\bw/': 'with',
        r'\bw/o': 'without',
    }
    for pattern, replacement in abbreviations.items():
        text = re.sub(pattern, replacement, text, flags=re.IGNORECASE)

    # Apply standard cleaning after removing code blocks
    text = clean_text_for_tts(text)

    return text.strip()
