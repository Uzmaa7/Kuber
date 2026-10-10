import os
import logfire
from pptx import Presentation

def parse_pptx(file_path: str) -> str:
    """
    Custom PPTX Parser tailored specifically for Kubernetes Architecture slides.
    Preserves YAML code snippets, nested bullet structures, and notes architecture diagrams.
    """
    with logfire.span("K8s PPTX Parsing", filename=file_path):
        try:
            prs = Presentation(file_path)
            filename = os.path.basename(file_path)
            markdown_text = f"# Source: {filename}\n\n"

            for idx, slide in enumerate(prs.slides, start=1):
                slide_title = f"Slide {idx}"
                slide_blocks = []
                has_images = False

                # Check for shapes, text, and images
                for shape in slide.shapes:
                    # Detect pictures/diagrams in the slide
                    if shape.shape_type == 13:  # 13 represents Picture/Media
                        has_images = True

                    if not shape.has_text_frame:
                        continue

                    shape_text = shape.text.strip()
                    if not shape_text:
                        continue

                    # Case A: If text box contains YAML manifest
                    if "apiVersion:" in shape_text or "kind:" in shape_text:
                        slide_blocks.append(f"```yaml\n{shape_text}\n```")
                    
                    # Case B: Standard text and bullets
                    else:
                        bullet_lines = []
                        for para in shape.text_frame.paragraphs:
                            text = para.text.strip()
                            if not text:
                                continue
                            
                            # First top-level text is treated as slide title if not set
                            if para.level == 0 and slide_title == f"Slide {idx}":
                                slide_title = text
                            else:
                                indent = "  " * para.level
                                bullet_lines.append(f"{indent}- {text}")
                        
                        if bullet_lines:
                            slide_blocks.append("\n".join(bullet_lines))

                # Build Markdown output for the slide
                markdown_text += f"## {slide_title}\n\n"
                
                if slide_blocks:
                    markdown_text += "\n\n".join(slide_blocks) + "\n\n"
                
                if has_images:
                    markdown_text += "*[Note: This slide contains visual architecture diagrams or flowcharts]*\n\n"

            logfire.info(f"Successfully parsed {len(prs.slides)} slides from {file_path}")
            return markdown_text

        except Exception as e:
            logfire.error(f"PPTX Parsing Failed for {file_path}: {e}")
            raise e