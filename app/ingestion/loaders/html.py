import os
import re
from bs4 import BeautifulSoup
import html2text
import logfire


def parse_html(file_path: str) -> str:
    """Production-grade HTML Parser tailored for Kubernetes/Databricks docs.

    Cleans junk tags, protects code/pre blocks from fake header injection,
    and formats clean markdown headings for downstream MarkdownHeaderTextSplitter.
    """
    with logfire.span("HTML Document Parsing", filename=file_path):
        try:
            # 1. Encoding-safe Read
            try:
                with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                    html_content = f.read()
            except Exception:
                with open(file_path, "r", encoding="latin-1", errors="ignore") as f:
                    html_content = f.read()

            soup = BeautifulSoup(html_content, "html.parser")
            filename = os.path.basename(file_path)

            # 2. Decompose Junk Elements (Scripts, styles, SVGs, metadata)
            for element in soup(["script", "style", "meta", "noscript", "svg"]):
                element.decompose()

            # 3. Protect Code & Pre blocks so their inner '#' don't become markdown headers
            for pre in soup.find_all(["pre", "code"]):
                # Escape hash signs inside code tags temporarily or wrap cleanly
                pre_text = pre.get_text()
                # Replace markdown header symbols inside code blocks to prevent splitter confusion
                safe_pre_text = pre_text.replace("#", "&#35;")
                pre.string = safe_pre_text

            # 4. Handle Authenticated Headers Safely
            for h1 in soup.find_all("h1"):
                text = h1.get_text().strip()
                h1.replace_with(soup.new_string(f"\n# {text}\n"))

            for h2 in soup.find_all("h2"):
                text = h2.get_text().strip()
                h2.replace_with(soup.new_string(f"\n## {text}\n"))

            for h3 in soup.find_all(["h3", "h4", "h5", "h6"]):
                text = h3.get_text().strip()
                if text.lower() in ["example", "note", "steps"]:
                    h3.replace_with(soup.new_string(f"\n**{text}:**\n"))
                else:
                    h3.replace_with(soup.new_string(f"\n### {text}\n"))

            # 5. html2text Markdown Conversion Configuration
            h2t = html2text.HTML2Text()
            h2t.ignore_links = False
            h2t.ignore_images = True
            h2t.body_width = 0  # Disable line wrapping so code blocks stay intact

            raw_markdown = h2t.handle(str(soup))

            # Restore escaped hash signs back to normal inside code blocks
            raw_markdown = raw_markdown.replace("&#35;", "#")

            # 6. Post-processing cleanup and line filtering
            clean_lines = []
            for line in raw_markdown.splitlines():
                stripped = line.strip()

                # Filter out raw line dividers
                if stripped.startswith("\\---") or stripped.startswith("---"):
                    continue

                # Pattern detection for plain text steps -> Convert to clean ## Headings
                if re.match(
                    r"^(STEP\s+\d+:|OVERVIEW OF STEPS|BEFORE YOU BEGIN|ALTERNATIVES)",
                    stripped,
                    re.IGNORECASE,
                ):
                    clean_lines.append(f"\n## {stripped}\n")
                else:
                    clean_lines.append(line)

            final_markdown = f"# Source: {filename}\n\n" + "\n".join(clean_lines)

            logfire.info(
                f"Successfully parsed {len(final_markdown)} characters from {file_path}"
            )
            return final_markdown

        except Exception as e:
            logfire.error(f"HTML Parsing Failed for {file_path}: {e}")
            raise e