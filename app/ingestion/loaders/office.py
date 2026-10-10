import os
import logfire
from docx import Document


def parse_docx(file_path: str) -> str:
    """
    Parses Office Word documents (.docx) preserving Markdown formatting and code blocks,
    tracked via Logfire.
    """
    with logfire.span("Word Document Parsing", filename=file_path):
        try:
            doc = Document(file_path)
            filename = os.path.basename(file_path)
            markdown_text = f"# Source: {filename}\n\n"
            
            for para in doc.paragraphs:
                text = para.text.strip()
                if not text:
                    continue
                
                # Check for Code / Manifest Syntax
                if (text.startswith("apiVersion:") or 
                    text.startswith("kind:") or 
                    text.startswith("metadata:") or 
                    text.startswith("spec:")):

                    markdown_text += f"```yaml\n{text}\n```\n\n"
                    
                elif text.startswith("kubectl ") or text.startswith("minikube ") or text.startswith("psql "):
                    markdown_text += f"```bash\n{text}\n```\n\n"
                    
                else:
                    markdown_text += f"{text}\n\n"

            if not markdown_text.strip():
                logfire.warning(f"DOCX parser returned empty text for {file_path}")
            else:
                logfire.info(f"Successfully parsed {len(markdown_text)} characters from {file_path}")

            return markdown_text

        except Exception as e:
            logfire.error(f"DOCX Parse Failed for {file_path}: {e}")
            raise e