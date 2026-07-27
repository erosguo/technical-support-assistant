import re

CHUNK_SIZE = 500
CHUNK_OVERLAP = 50


def chunk_text(
    text: str,
    chunk_size: int = CHUNK_SIZE,
    overlap: int = CHUNK_OVERLAP,
) -> list[dict]:
    if not text:
        return []

    paragraphs = re.split(r"\n\s*\n", text.strip())

    chunks = []
    current = ""
    for para in paragraphs:
        if len(current) + len(para) + 1 <= chunk_size:
            current = (current + "\n\n" + para).strip()
        else:
            if current:
                chunks.append(current)
            current = para

        while len(current) > chunk_size:
            chunks.append(current[:chunk_size])
            current = current[chunk_size - overlap :]

    if current:
        chunks.append(current)

    return [
        {"content": c.strip(), "chunk_index": i}
        for i, c in enumerate(chunks)
        if c.strip()
    ]
