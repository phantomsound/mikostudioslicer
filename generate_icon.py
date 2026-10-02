from PIL import Image, ImageDraw
import os

sizes = [(256, 256), (64, 64), (48, 48), (32, 32), (16, 16)]
images = []

for s in sizes:
    w, h = s
    img = Image.new("RGBA", s, (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    rad = max(2, int(w * 0.22))
    
    # Dark slate rounded box
    draw.rounded_rectangle([0, 0, w-1, h-1], radius=rad, fill=(18, 20, 26, 255), outline=(245, 158, 11, 230), width=max(1, int(w*0.04)))
    
    if w >= 32:
        # Golden M
        draw.polygon([(w*0.2, h*0.78), (w*0.2, h*0.24), (w*0.35, h*0.24), (w*0.35, h*0.78)], fill=(245, 158, 11, 255))
        draw.polygon([(w*0.65, h*0.78), (w*0.65, h*0.24), (w*0.8, h*0.24), (w*0.8, h*0.78)], fill=(245, 158, 11, 255))
        draw.polygon([(w*0.35, h*0.24), (w*0.5, h*0.56), (w*0.65, h*0.24), (w*0.5, h*0.42)], fill=(251, 191, 36, 255))
        # Cyan slice blade line
        draw.line([(w*0.12, h*0.72), (w*0.88, h*0.28)], fill=(6, 182, 212, 255), width=max(1, int(w*0.06)))
    else:
        draw.rectangle([w*0.25, h*0.25, w*0.75, h*0.75], fill=(245, 158, 11, 255))
    
    images.append(img)

images[0].save("icon.ico", format="ICO", sizes=[(im.width, im.height) for im in images])
print("[OK] icon.ico generated successfully.")
