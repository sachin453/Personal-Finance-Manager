import pdfplumber

with pdfplumber.open(r"C:\Users\sachi\OneDrive\Desktop\PersonalFinanceManager\data\sample.pdf") as pdf:
    text = "\n".join(page.extract_text() for page in pdf.pages)
print(text[:5000])  # Print first 500 characters of the extracted text
