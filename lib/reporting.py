
import io
import pandas as pd
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.lib.units import mm
from reportlab.lib.utils import ImageReader

def to_excel(df: pd.DataFrame, summary: dict) -> bytes:
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        df.to_excel(writer, index=False, sheet_name="Movimentos")
        s = pd.DataFrame([summary])
        s.to_excel(writer, index=False, sheet_name="Resumo")
    return output.getvalue()

def to_pdf(df: pd.DataFrame, summary: dict, logo_bytes: bytes|None=None) -> bytes:
    buffer = io.BytesIO()
    c = canvas.Canvas(buffer, pagesize=A4)
    w, h = A4
    y = h - 30*mm
    if logo_bytes:
        c.drawImage(ImageReader(io.BytesIO(logo_bytes)), 15*mm, y, width=25*mm, height=25*mm, mask='auto')
    c.setFont("Helvetica-Bold", 16)
    c.drawString(50*mm, y+15, "Relatório Financeiro")
    c.setFont("Helvetica", 10)
    y -= 10*mm
    # summary
    for k,v in summary.items():
        c.drawString(15*mm, y, f"{k}: {v}")
        y -= 6*mm
    y -= 4*mm
    # table header
    cols = ["data","descricao","categoria","tipo","valor","forma_pagamento","status","vencimento","responsavel_nome"]
    x_positions = [10, 35, 70, 97, 117, 145, 170, 190, 215]
    c.setFont("Helvetica-Bold", 9)
    for x, col in zip(x_positions, cols):
        c.drawString(x*mm, y, col.capitalize())
    y -= 6*mm
    c.setFont("Helvetica", 9)
    for _, row in df[cols].iterrows():
        if y < 20*mm:
            c.showPage()
            y = h - 20*mm
        for x, col in zip(x_positions, cols):
            c.drawString(x*mm, y, str(row[col])[:28])
        y -= 6*mm
    c.showPage()
    c.save()
    return buffer.getvalue()
