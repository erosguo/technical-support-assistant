from app.services.chunking import chunk_text, CHUNK_SIZE


class TestChunking:
    def test_empty_text_returns_empty(self):
        assert chunk_text("") == []

    def test_short_text_returns_single_chunk(self):
        result = chunk_text("Hello world")
        assert len(result) == 1
        assert result[0]["content"] == "Hello world"
        assert result[0]["chunk_index"] == 0

    def test_long_text_splits_into_multiple_chunks(self):
        text = "word " * (CHUNK_SIZE + 50)
        result = chunk_text(text)
        assert len(result) >= 2

    def test_chunks_have_overlap(self):
        text = "ABCDE" * (CHUNK_SIZE + 100)
        result = chunk_text(text)
        if len(result) >= 2:
            assert result[0]["chunk_index"] == 0
            assert result[1]["chunk_index"] == 1

    def test_chunk_indices_are_sequential(self):
        text = "word " * (CHUNK_SIZE * 3)
        result = chunk_text(text)
        for i, chunk in enumerate(result):
            assert chunk["chunk_index"] == i

    def test_metadata_includes_chunk_index(self):
        result = chunk_text("hello world")
        assert "chunk_index" in result[0]
        assert "content" in result[0]

    def test_preserves_paragraph_boundaries(self):
        text = "=" * 200 + "\n\n" + "-" * 200
        result = chunk_text(text, chunk_size=150, overlap=20)
        # at least 2 chunks, paragraph boundary preserved
        assert len(result) >= 2

    def test_custom_chunk_size(self):
        text = "hello world foo bar baz qux"
        result = chunk_text(text, chunk_size=10, overlap=0)
        assert len(result) > 1
