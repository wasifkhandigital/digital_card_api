from fastapi import FastAPI, Request, Form, HTTPException, BackgroundTasks
from fastapi.responses import FileResponse, StreamingResponse, HTMLResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
import qrcode
from qrcode.image.styledpil import StyledPilImage
from qrcode.image.styles.moduledrawers import RoundedModuleDrawer
from qrcode.image.styles.colormasks import SolidFillColorMask
from PIL import Image, ImageDraw, ImageFont
from zipfile import ZipFile
import os
import io
import urllib.parse

app = FastAPI()

# Static files
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

# Cleanup function for background task
def cleanup_files(files):
    for f in files:
        if os.path.exists(f):
            os.remove(f)

# -------- Info Image endpoint --------
@app.get("/info_image")
def info_image(full_name: str, phone: str, email: str, job_title: str = "", company: str = "", website: str = ""):
    width, height = 700, 400
    img = Image.new("RGB", (width, height), color=(255, 255, 255))  # white bg
    draw = ImageDraw.Draw(img)

    # Fonts
    try:
        title_font = ImageFont.truetype("arial.ttf", 28)
        font = ImageFont.truetype("arial.ttf", 20)
    except:
        title_font = ImageFont.load_default()
        font = ImageFont.load_default()

    # Card border
    border_color = (30, 60, 114)  # deep blue
    draw.rounded_rectangle([(20, 20), (width - 20, height - 20)], radius=20, outline=border_color, width=4)

    # Name (highlighted on top)
    draw.text((50, 50), f"Name: {full_name}", fill=(20, 40, 90), font=title_font)

    # Other details
    y_text = 120
    details = [
        f"Job Title: {job_title}" if job_title else "",
        f"Company: {company}" if company else "",
        f"Phone: {phone}",
        f"Email: {email}",
        f"Website: {website}" if website else ""
    ]
    for line in details:
        if line.strip():
            draw.text((50, y_text), line, fill=(40, 40, 40), font=font)
            y_text += 40

    # Serve image directly using StreamingResponse
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    buf.seek(0)
    return StreamingResponse(buf, media_type="image/png")

# -------- Generate Card endpoint --------
@app.post("/card")
async def generate_card(
    background_tasks: BackgroundTasks,
    full_name: str = Form(...),
    phone: str = Form(...),
    email: str = Form(...),
    job_title: str = Form(""),
    company: str = Form(""),
    website: str = Form("")
):
    vcard_path = "card.vcf"
    qr_path = "qrcode.png"
    zip_path = "card_package.zip"

    try:
        # vCard content
        vcard_content = f"""BEGIN:VCARD
VERSION:3.0
FN:{full_name}
ORG:{company}
TITLE:{job_title}
TEL;TYPE=CELL:{phone}
EMAIL:{email}
URL:{website}
END:VCARD
"""
        with open(vcard_path, "w") as f:
            f.write(vcard_content)

        # Encode info_image URL with query params
        query_params = urllib.parse.urlencode({
            "full_name": full_name,
            "phone": phone,
            "email": email,
            "job_title": job_title,
            "company": company,
            "website": website
        })
        info_url = f"https://digital-card-api.onrender.com/info_image?{query_params}"

        # QR Code
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_H,
            box_size=10,
            border=4
        )
        qr.add_data(info_url)
        qr.make(fit=True)

        qr_img = qr.make_image(
            image_factory=StyledPilImage,
            module_drawer=RoundedModuleDrawer(),
            color_mask=SolidFillColorMask(front_color=(30, 60, 114), back_color=(224, 255, 255))
        )

        # Optional logo in QR center
        logo_path = "logo.png"
        if os.path.exists(logo_path):
            logo = Image.open(logo_path)
            basewidth = int(qr_img.size[0] * 0.2)
            wpercent = (basewidth / float(logo.size[0]))
            hsize = int((float(logo.size[1]) * float(wpercent)))
            logo = logo.resize((basewidth, hsize), Image.Resampling.LANCZOS)
            pos = ((qr_img.size[0] - logo.size[0]) // 2, (qr_img.size[1] - logo.size[1]) // 2)
            if logo.mode == "RGBA":
                qr_img.paste(logo, pos, mask=logo.split()[3])
            else:
                qr_img.paste(logo, pos)

        qr_img.save(qr_path)

        # Create ZIP
        with ZipFile(zip_path, "w") as zipf:
            zipf.write(vcard_path, arcname="card.vcf")
            zipf.write(qr_path, arcname="qrcode.png")

        # Cleanup
        background_tasks.add_task(cleanup_files, [vcard_path, qr_path, zip_path])

        return FileResponse(zip_path, media_type="application/zip", filename="digital_card.zip")

    except Exception as e:
        print("Error generating card:", str(e))
        raise HTTPException(status_code=500, detail=f"Failed to generate card: {str(e)}")
