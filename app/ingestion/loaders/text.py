import os
import logfire


def parse_text(file_path: str) -> str:
    """Parses plain text files into Markdown format with source metadata tracking."""
    with logfire.span("Text Parsing", filename=file_path):
        try:
            with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                content = f.read()

            filename = os.path.basename(file_path)
            # Source header add karne se chunker ko context maintain rakhne me help milti hai
            markdown_content = f"# Source: {filename}\n\n{content}"

            logfire.info(
                f"Successfully parsed {len(markdown_content)} characters from {file_path}"
            )
            return markdown_content

        except Exception as e:
            logfire.error(f"Text Parse Failed for {file_path}: {e}")
            raise e
