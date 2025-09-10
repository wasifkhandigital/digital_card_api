from fastapi import FastAPI, Request, Form, HTTPException, BackgroundTasks
from fastapi.responses import FileResponse, HTMLResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
import qrcode
from qrcode.image.styledpil import StyledPilImage
from qrcode.image.styles.moduledrawers import RoundedModuleDrawer
from qrcode.image.styles.colormasks import SolidFillColorMask
from PIL import Image, ImageDraw, ImageFont
from zipfile import ZipFile
import os

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
    info_image_path = "info_image.png"
    zip_path = "card_package.zip"

    try:
        # --------- vCard Content ----------
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

        # --------- QR Code ----------
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_H,
            box_size=10,
            border=4
        )
        qr.add_data(vcard_content)
        qr.make(fit=True)

        qr_img = qr.make_image(
            image_factory=StyledPilImage,
            module_drawer=RoundedModuleDrawer(),
            color_mask=SolidFillColorMask(front_color=(30,60,114), back_color=(224,255,255))
        )

        # Add logo if exists
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

        # --------- Info Image ----------
        # Create blank white image
        width, height = 500, 300
        info_img = Image.new("RGB", (width, height), color=(255,255,255))
        draw = ImageDraw.Draw(info_img)

        # Load default font
        try:
            font = ImageFont.truetype("arial.ttf", 20)
        except:
            font = ImageFont.load_default()

        # Prepare text
        lines = [
            f"Full Name: {full_name}",
            f"Phone: {phone}",
            f"Email: {email}",
            f"Job Title: {job_title}",
            f"Company: {company}",
            f"Website: {website}"
        ]

        # Write text
        y_text = 20
        for line in lines:
            draw.text((20, y_text), line, fill=(30,30,30), font=font)
            y_text += 35

        info_img.save(info_image_path)

        # --------- Create ZIP ----------
        with ZipFile(zip_path, "w") as zipf:
            zipf.write(vcard_path, arcname="card.vcf")
            zipf.write(qr_path, arcname="qrcode.png")
            zipf.write(info_image_path, arcname="info_image.png")

        # Schedule cleanup
        background_tasks.add_task(cleanup_files, [vcard_path, qr_path, info_image_path, zip_path])

        return FileResponse(zip_path, media_type="application/zip", filename="digital_card.zip")

    except Exception as e:
        print("Error generating card:", str(e))
        raise HTTPException(status_code=500, detail=f"Failed to generate card: {str(e)}")
