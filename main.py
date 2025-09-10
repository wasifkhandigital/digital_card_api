from fastapi import FastAPI, Form
from fastapi.responses import FileResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from fastapi.requests import Request
import qrcode
from pydantic import BaseModel
import os, zipfile

app = FastAPI()

templates = Jinja2Templates(directory="templates")
app.mount("/static", StaticFiles(directory="static"), name="static")


class CardData(BaseModel):
    name: str
    phone: str
    email: str
    job: str
    company: str
    website: str


def create_vcf(data: CardData, filename: str):
    vcf_content = f"""BEGIN:VCARD
VERSION:3.0
FN:{data.name}
TEL:{data.phone}
EMAIL:{data.email}
TITLE:{data.job}
ORG:{data.company}
URL:{data.website}
END:VCARD
"""
    with open(filename, "w", encoding="utf-8") as f:
        f.write(vcf_content)


def create_qr(data: CardData, filename: str):
    qr_data = f"Name: {data.name}\nPhone: {data.phone}\nEmail: {data.email}\nJob: {data.job}\nCompany: {data.company}\nWebsite: {data.website}"
    qr = qrcode.QRCode(box_size=10, border=4)
    qr.add_data(qr_data)
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white")
    img.save(filename)


@app.get("/")
async def form_page(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})


@app.post("/card")
async def generate_card(
    name: str = Form(...),
    phone: str = Form(...),
    email: str = Form(...),
    job: str = Form(...),
    company: str = Form(...),
    website: str = Form(...),
):
    data = CardData(name=name, phone=phone, email=email, job=job, company=company, website=website)

    # File paths
    vcf_file = "card.vcf"
    qr_file = "qrcode.png"
    zip_file = "card_package.zip"

    # Create files
    create_vcf(data, vcf_file)
    create_qr(data, qr_file)

    # Package into ZIP (only VCF + QR)
    with zipfile.ZipFile(zip_file, "w") as zipf:
        zipf.write(vcf_file)
        zipf.write(qr_file)

    return FileResponse(zip_file, media_type="application/zip", filename=zip_file)
