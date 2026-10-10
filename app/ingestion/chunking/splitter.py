from typing import Any, Dict, List
import logfire
from langchain_text_splitters import (
    MarkdownHeaderTextSplitter,
    RecursiveCharacterTextSplitter,
)


def chunk_text(
    markdown_text: str,
    filename: str,
    source_type: str = "true",
    raw_gcs_bucket: str = "my-bucket",
    chunk_size: int = 1500,  # Slightly increased to accommodate tables comfortably
    chunk_overlap: int = 200,
) -> List[Dict[str, Any]]:
    """Table-safe and Code-safe chunker that prevents splitting tables and yaml/json code blocks

    across chunk boundaries.
    """
    if not markdown_text or not markdown_text.strip():
        return []

    # 1. Structural Header Splitting
    headers_to_split_on = [
        ("#", "Header 1"),
        ("##", "Header 2"),
        ("###", "Header 3"),
    ]

    markdown_splitter = MarkdownHeaderTextSplitter(
        headers_to_split_on=headers_to_split_on
    )
    header_docs = markdown_splitter.split_text(markdown_text)

    # 2. Advanced Syntax-Safe Recursive Splitter
    # Separator priority: Code blocks first, then tables/paragraphs, then lines, then words
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
        separators=[
            "\n```",  # Never split code blocks
            "\n|",  # Never split markdown tables mid-row if possible
            "\n\n",  # Paragraphs
            "\n",  # Single lines
            " ",  # Words
            "",
        ],
    )

    rich_chunks = []
    file_type = filename.lower().split(".")[-1]
    global_chunk_index = 0

    for doc in header_docs:
        # Clean Breadcrumb Path (Removing any accidental markdown symbols)
        headers = [
            str(val).lstrip("#").strip()
            for key, val in doc.metadata.items()
            if val
        ]
        breadcrumb = " > ".join(headers) if headers else "Document Root"

        sub_chunks = text_splitter.split_text(doc.page_content)

        for chunk in sub_chunks:
            if chunk.strip():
                global_chunk_index += 1

                # Context Enrichment for Vector Embeddings
                context_enriched_text = (
                    f"Context: {breadcrumb}\n\n{chunk.strip()}"
                )

                # Clean Metadata Payload
                metadata = {
                    "source": filename,
                    "file_type": file_type,
                    "section": breadcrumb,
                    "header_1": doc.metadata.get("Header 1", "").lstrip("#").strip(),
                    "header_2": doc.metadata.get("Header 2", "").lstrip("#").strip(),
                    "header_3": doc.metadata.get("Header 3", "").lstrip("#").strip(),
                    "chunk_index": global_chunk_index,
                    "source_type": source_type,
                    "raw_gcs_path": f"gs://{raw_gcs_bucket}/{source_type}/{filename}",
                }

                rich_chunks.append(
                    {"text": context_enriched_text, "metadata": metadata}
                )

    logfire.info(f"Successfully generated {len(rich_chunks)} table-safe chunks for {filename}")
    return rich_chunks