import io
import os
import csv
import base64
from typing import Dict, Any, List, Optional
from PIL import Image

try:
    import pypdf
    PYPDF_AVAILABLE = True
except ImportError:
    PYPDF_AVAILABLE = False

try:
    import docx
    DOCX_AVAILABLE = True
except ImportError:
    DOCX_AVAILABLE = False

try:
    import openpyxl
    OPENPYXL_AVAILABLE = True
except ImportError:
    OPENPYXL_AVAILABLE = False


class MultimediaParser:
    """
    Extractor y analizador multimedia para documentos, hojas de cálculo e imágenes del portapapeles.
    - Documentos: PDF (.pdf), Word (.docx), Texto plano (.txt, .md).
    - Hojas de cálculo: Excel (.xlsx), CSV (.csv) -> Conversión a tablas Markdown estructuradas.
    - Imágenes: Archivos y capturas de pantalla pegadas directamente (Ctrl+V) en Base64.
    """

    MAX_TEXT_CHARS = 100000  # Límite de seguridad por archivo para no saturar tokens
    MAX_IMAGE_DIM = 1280     # Dimensión máxima para imágenes de visión multimodal

    @classmethod
    def parse_pdf(cls, file_bytes: bytes, filename: str = "documento.pdf") -> str:
        if not PYPDF_AVAILABLE:
            return f"[Error: Módulo pypdf no disponible para procesar '{filename}']"

        try:
            reader = pypdf.PdfReader(io.BytesIO(file_bytes))
            pages_text = []
            for i, page in enumerate(reader.pages):
                text = page.extract_text() or ""
                if text.strip():
                    pages_text.append(f"--- [PÁGINA {i+1}] ---\n{text.strip()}")

            full_text = "\n\n".join(pages_text)
            if len(full_text) > cls.MAX_TEXT_CHARS:
                full_text = full_text[:cls.MAX_TEXT_CHARS] + f"\n\n[... Truncado por límite de caracteres: {filename}]"
            return full_text if full_text else f"[Documento PDF '{filename}' sin texto legible]"
        except Exception as e:
            return f"[Error al extraer texto del PDF '{filename}': {e}]"

    @classmethod
    def parse_docx(cls, file_bytes: bytes, filename: str = "documento.docx") -> str:
        if not DOCX_AVAILABLE:
            return f"[Error: Módulo python-docx no disponible para procesar '{filename}']"

        try:
            doc = docx.Document(io.BytesIO(file_bytes))
            paragraphs = [p.text for p in doc.paragraphs if p.text.strip()]

            # Extraer también tablas internas si existen
            tables_text = []
            for table in doc.tables:
                rows_data = []
                for row in table.rows:
                    row_cells = [cell.text.replace("\n", " ").strip() for cell in row.cells]
                    rows_data.append(" | ".join(row_cells))
                if rows_data:
                    tables_text.append("### Tabla en Documento:\n| " + " |\n| ".join(rows_data) + " |")

            full_text = "\n\n".join(paragraphs)
            if tables_text:
                full_text += "\n\n" + "\n\n".join(tables_text)

            if len(full_text) > cls.MAX_TEXT_CHARS:
                full_text = full_text[:cls.MAX_TEXT_CHARS] + f"\n\n[... Truncado: {filename}]"
            return full_text if full_text else f"[Documento Word '{filename}' vacío]"
        except Exception as e:
            return f"[Error al extraer texto del Word '{filename}': {e}]"

    @classmethod
    def parse_csv(cls, file_bytes: bytes, filename: str = "datos.csv") -> str:
        try:
            text_content = file_bytes.decode("utf-8", errors="ignore")
            reader = csv.reader(io.StringIO(text_content))
            rows = list(reader)

            if not rows:
                return f"[Archivo CSV '{filename}' vacío]"

            # Formatear a tabla Markdown
            md_lines = []
            header = rows[0]
            md_lines.append("| " + " | ".join(header) + " |")
            md_lines.append("| " + " | ".join(["---"] * len(header)) + " |")

            for row in rows[1:100]:  # Máximo 100 filas
                # Normalizar columnas
                padded = row + [""] * max(0, len(header) - len(row))
                md_lines.append("| " + " | ".join(padded[:len(header)]) + " |")

            if len(rows) > 100:
                md_lines.append(f"\n*... ({len(rows) - 100} filas adicionales omitidas por brevedad)*")

            return "\n".join(md_lines)
        except Exception as e:
            return f"[Error al procesar archivo CSV '{filename}': {e}]"

    @classmethod
    def parse_xlsx(cls, file_bytes: bytes, filename: str = "datos.xlsx") -> str:
        if not OPENPYXL_AVAILABLE:
            return f"[Error: Módulo openpyxl no disponible para procesar '{filename}']"

        try:
            wb = openpyxl.load_workbook(io.BytesIO(file_bytes), data_only=True)
            sheets_text = []

            for sheet_name in wb.sheetnames[:3]:  # Hasta 3 pestañas principales
                sheet = wb[sheet_name]
                rows = list(sheet.iter_rows(values_only=True))
                if not rows:
                    continue

                non_empty_rows = [r for r in rows if any(c is not None for c in r)]
                if not non_empty_rows:
                    continue

                header = [str(c or "").strip() for c in non_empty_rows[0]]
                md_lines = [f"#### Hoja: {sheet_name}", "| " + " | ".join(header) + " |", "| " + " | ".join(["---"] * len(header)) + " |"]

                for row in non_empty_rows[1:80]:  # Límite de 80 filas por hoja
                    str_row = [str(c if c is not None else "").replace("\n", " ").strip() for c in row]
                    padded = str_row + [""] * max(0, len(header) - len(str_row))
                    md_lines.append("| " + " | ".join(padded[:len(header)]) + " |")

                if len(non_empty_rows) > 80:
                    md_lines.append(f"*... ({len(non_empty_rows) - 80} filas adicionales omitidas)*")

                sheets_text.append("\n".join(md_lines))

            return "\n\n".join(sheets_text) if sheets_text else f"[Libro Excel '{filename}' sin datos]"
        except Exception as e:
            return f"[Error al procesar libro Excel '{filename}': {e}]"

    @classmethod
    def process_image_base64(cls, base64_str: str) -> Optional[str]:
        """
        Valida, redimensiona de forma segura y normaliza una imagen en Base64
        (compatible con capturas de pantalla de portapapeles y archivos locales).
        """
        try:
            # Limpiar prefijo data:image/...;base64, si existe
            clean_b64 = base64_str
            if "," in base64_str:
                clean_b64 = base64_str.split(",", 1)[1]

            image_data = base64.b64decode(clean_b64)
            img = Image.open(io.BytesIO(image_data))

            # Convertir a RGB si es necesario (ej. PNG con canal alfa o paleta)
            if img.mode in ("RGBA", "P"):
                img = img.convert("RGB")

            # Redimensionar proporcionalmente si supera la dimensión máxima
            w, h = img.size
            if w > cls.MAX_IMAGE_DIM or h > cls.MAX_IMAGE_DIM:
                if w > h:
                    new_w = cls.MAX_IMAGE_DIM
                    new_h = int(h * (cls.MAX_IMAGE_DIM / w))
                else:
                    new_h = cls.MAX_IMAGE_DIM
                    new_w = int(w * (cls.MAX_IMAGE_DIM / h))
                img = img.resize((new_w, new_h), Image.Resampling.LANCZOS)

            # Re-codificar a JPEG comprimido para optimizar memoria y transporte de red
            out_buf = io.BytesIO()
            img.save(out_buf, format="JPEG", quality=85)
            return base64.b64encode(out_buf.getvalue()).decode("utf-8")
        except Exception as e:
            print(f"[MultimediaParser] Error procesando imagen Base64: {e}")
            return None

    @classmethod
    def parse_uploaded_file(cls, filename: str, file_bytes: bytes) -> Dict[str, Any]:
        """
        Punto de entrada para analizar cualquier tipo de archivo multimedia subido.
        """
        ext = os.path.splitext(filename)[1].lower()
        size_kb = round(len(file_bytes) / 1024, 2)

        if ext == ".pdf":
            content = cls.parse_pdf(file_bytes, filename)
            return {"type": "document", "format": "pdf", "filename": filename, "size_kb": size_kb, "content": content}

        if ext in (".docx", ".doc"):
            content = cls.parse_docx(file_bytes, filename)
            return {"type": "document", "format": "docx", "filename": filename, "size_kb": size_kb, "content": content}

        if ext == ".csv":
            content = cls.parse_csv(file_bytes, filename)
            return {"type": "spreadsheet", "format": "csv", "filename": filename, "size_kb": size_kb, "content": content}

        if ext in (".xlsx", ".xls"):
            content = cls.parse_xlsx(file_bytes, filename)
            return {"type": "spreadsheet", "format": "xlsx", "filename": filename, "size_kb": size_kb, "content": content}

        if ext in (".txt", ".md", ".json", ".log", ".py", ".rs", ".js", ".html", ".css"):
            text = file_bytes.decode("utf-8", errors="ignore")
            if len(text) > cls.MAX_TEXT_CHARS:
                text = text[:cls.MAX_TEXT_CHARS] + f"\n\n[... Truncado por tamaño: {filename}]"
            return {"type": "text", "format": ext[1:], "filename": filename, "size_kb": size_kb, "content": text}

        if ext in (".png", ".jpg", ".jpeg", ".webp", ".bmp"):
            raw_b64 = base64.b64encode(file_bytes).decode("utf-8")
            processed_b64 = cls.process_image_base64(raw_b64)
            return {
                "type": "image",
                "format": ext[1:],
                "filename": filename,
                "size_kb": size_kb,
                "base64_image": processed_b64 or raw_b64
            }

        return {
            "type": "unsupported",
            "format": ext,
            "filename": filename,
            "size_kb": size_kb,
            "content": f"[Formato de archivo '{ext}' no soportado directamente. Formatos válidos: PDF, Word, Excel, CSV, Texto plano, Imágenes]"
        }

