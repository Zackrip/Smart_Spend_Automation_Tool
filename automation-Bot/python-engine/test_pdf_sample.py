from src.statement_pdf_report import generate_statement_pdf

sample = [
    {"date": "2026-11-01", "merchant": "Zudio", "amount": 499, "type": "debit", "category": "Shopping", "needs_review": False},
    {"date": "2026-11-02", "merchant": "Swiggy", "amount": 245, "type": "debit", "category": "Food", "needs_review": False},
    {"date": "2026-11-03", "merchant": "Rahul Sharma", "amount": 500, "type": "credit", "category": "Other", "needs_review": True},
]
pdf = generate_statement_pdf(sample, branding="Paisora")
with open("Paisora_Dark_Executive_Sample.pdf", "wb") as f:
    f.write(pdf.getvalue())
print("Created Paisora_Dark_Executive_Sample.pdf")
