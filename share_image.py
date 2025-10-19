from PIL import Image, ImageDraw, ImageFont
from io import BytesIO

def make_share_card(quote: str, watermark: str = "@AIpsihologProBot") -> bytes:
    W, H = 1080, 1920
    img = Image.new("RGB", (W, H), (20, 22, 28))
    draw = ImageDraw.Draw(img)

    try:
        font_body = ImageFont.truetype("DejaVuSans.ttf", 72)
        font_mark = ImageFont.truetype("DejaVuSans.ttf", 40)
        font_title = ImageFont.truetype("DejaVuSans.ttf", 60)
    except:
        font_body = ImageFont.load_default()
        font_mark = ImageFont.load_default()
        font_title = ImageFont.load_default()

    title = "AI‑Психолог говорит:"
    tw, th = draw.textsize(title, font=font_title)
    draw.text(((W - tw)//2, 120), title, fill=(230, 230, 240), font=font_title)

    max_w = W - 160
    words = quote.split()
    lines = []
    line = ""
    for w in words:
        test = (line + " " + w).strip()
        if draw.textsize(test, font=font_body)[0] <= max_w:
            line = test
        else:
            lines.append(line)
            line = w
    if line:
        lines.append(line)

    y = 360
    for l in lines[:14]:
        lw, lh = draw.textsize(l, font=font_body)
        draw.text(((W - lw)//2, y), l, fill=(245, 245, 250), font=font_body)
        y += lh + 22

    mw, mh = draw.textsize(watermark, font=font_mark)
    draw.text((W - mw - 40, H - mh - 40), watermark, fill=(180, 180, 190), font=font_mark)

    bio = BytesIO()
    img.save(bio, format="PNG")
    return bio.getvalue()
