from fastapi import FastAPI, Form
from fastapi.responses import FileResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from fastapi.requests import Request
import qrcode
from qrcode.image.pil import PilImage
from pydantic import BaseModel
import os, zipfile
from PIL import Image, ImageDraw, ImageFont

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


def create_card_image(data: CardData, filename: str):
    # Image size
    width, height = 800, 400
    img = Image.new("RGB", (width, height), "#E6F2FA")  # Light Sky Blue BG
    draw = ImageDraw.Draw(img)

    # Border
    border_color = "#1E3A8A"  # Dark Blue
    border_width = 8
    draw.rectangle([0, 0, width, height], outline=border_color, width=border_width)

    # Fonts (safe defaults)
    font_bold = ImageFont.load_default()
    font_regular = ImageFont.load_default()

    # Start position
    x_start, y_start = 60, 80
    line_spacing = 50

    info = [
        ("Name:", data.name),
        ("Phone:", data.phone),
        ("Email:", data.email),
        ("Job Title:", data.job),
        ("Company:", data.company),
        ("Website:", data.website),
    ]

    for i, (label, value) in enumerate(info):
        y = y_start + i * line_spacing
        draw.text((x_start, y), label, font=font_bold, fill="black")
        draw.text((x_start + 180, y), value, font=font_regular, fill="black")

    img.save(filename)


@app.get("/")
async def form_page(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})


@app.post("/card")
async def generate_card(
    name: str = Form(...),
    phone: str = Form(...),
    email: str = Form(...),
    job: str = Form(""),
    company: str = Form(""),
    website: str = Form(""),
):
    data = CardData(name=name, phone=phone, email=email, job=job, company=company, website=website)

    # File paths
    vcf_file = "card.vcf"
    qr_file = "qrcode.png"
    img_file = "business_card.png"
    zip_file = "card_package.zip"

    # Create files
    create_vcf(data, vcf_file)
    create_qr(data, qr_file)
    create_card_image(data, img_file)

    # Package into ZIP
    with zipfile.ZipFile(zip_file, "w") as zipf:
        zipf.write(vcf_file)
        zipf.write(qr_file)
        zipf.write(img_file)

    return FileResponse(zip_file, media_type="application/zip", filename=zip_file)
