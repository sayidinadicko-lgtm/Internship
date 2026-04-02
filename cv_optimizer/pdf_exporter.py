"""
Convertit un fichier .docx en .pdf.
- Windows : via docx2pdf (utilise Microsoft Word)
- Linux/Mac : via LibreOffice headless
"""
import subprocess
import shutil
import sys
import os
from pathlib import Path


def docx_to_pdf(docx_path: str, output_dir: str = None) -> str:
    """
    Convertit un .docx en .pdf.
    Retourne le chemin du .pdf généré, ou lève une exception si échec.
    """
    docx_path = Path(docx_path).resolve()
    if not docx_path.exists():
        raise FileNotFoundError(f"Fichier source introuvable : {docx_path}")

    out_dir = Path(output_dir).resolve() if output_dir else docx_path.parent
    pdf_path = out_dir / (docx_path.stem + ".pdf")

    # Windows : utiliser docx2pdf (passe par Microsoft Word COM)
    if sys.platform == "win32":
        try:
            from docx2pdf import convert
            convert(str(docx_path), str(pdf_path))
            if pdf_path.exists():
                return str(pdf_path)
            raise RuntimeError("docx2pdf n'a pas généré le fichier PDF.")
        except ImportError:
            raise FileNotFoundError(
                "docx2pdf non installé. Lancer : pip install docx2pdf"
            )

    # Linux/Mac : utiliser LibreOffice
    lo_bin = shutil.which("libreoffice") or shutil.which("soffice")
    if not lo_bin:
        raise FileNotFoundError(
            "LibreOffice introuvable. Installer avec : sudo apt install libreoffice"
        )

    result = subprocess.run(
        [lo_bin, "--headless", "--convert-to", "pdf", "--outdir", str(out_dir), str(docx_path)],
        capture_output=True, text=True, timeout=60,
    )

    if result.returncode != 0:
        raise RuntimeError(f"Échec LibreOffice :\n{result.stderr}")

    if not pdf_path.exists():
        raise RuntimeError(f"PDF attendu mais introuvable : {pdf_path}")

    return str(pdf_path)
