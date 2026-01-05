"""Text chunking logic for splitting long texts at sentence boundaries."""

import re


class TextChunker:
    """Splits text into chunks at sentence boundaries, respecting max length."""

    def __init__(self, max_chars: int = 750):
        self.max_chars = max_chars
        self.sentence_pattern = re.compile(r'(?<=[.!?])\s+')

    def chunk(self, text: str) -> list[str]:
        """Split text into chunks at sentence boundaries."""
        if len(text) <= self.max_chars:
            return [text.strip()]

        sentences = self._split_sentences(text)
        chunks = []
        current_chunk = []
        current_length = 0

        for sentence in sentences:
            sentence_length = len(sentence)

            if sentence_length > self.max_chars:
                if current_chunk:
                    chunks.append(' '.join(current_chunk))
                    current_chunk = []
                    current_length = 0

                sub_chunks = self._split_long_sentence(sentence)
                chunks.extend(sub_chunks)
                continue

            if current_length + sentence_length + 1 > self.max_chars:
                if current_chunk:
                    chunks.append(' '.join(current_chunk))
                current_chunk = [sentence]
                current_length = sentence_length
            else:
                current_chunk.append(sentence)
                current_length += sentence_length + 1

        if current_chunk:
            chunks.append(' '.join(current_chunk))

        return [chunk.strip() for chunk in chunks if chunk.strip()]

    def _split_sentences(self, text: str) -> list[str]:
        """Split text into sentences."""
        sentences = self.sentence_pattern.split(text)
        return [s.strip() for s in sentences if s.strip()]

    def _split_long_sentence(self, sentence: str) -> list[str]:
        """Split a sentence that's too long at comma or word boundaries."""
        if len(sentence) <= self.max_chars:
            return [sentence]

        chunks = []
        words = sentence.split()
        current_chunk = []
        current_length = 0

        for word in words:
            word_length = len(word)

            if current_length + word_length + 1 > self.max_chars:
                if current_chunk:
                    chunks.append(' '.join(current_chunk))
                current_chunk = [word]
                current_length = word_length
            else:
                current_chunk.append(word)
                current_length += word_length + 1

        if current_chunk:
            chunks.append(' '.join(current_chunk))

        return chunks
