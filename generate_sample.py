from PIL import Image, ImageDraw
import os

W, H = 1600, 1000
img = Image.new("RGBA", (W, H), (26, 29, 38, 255))
draw = ImageDraw.Draw(img)

# Outer card panel
draw.rectangle([40, 40, W-40, H-40], fill=(19, 21, 29, 255), outline=(43, 48, 64, 255), width=2)

# Top Spec Bar
draw.text((70, 75), "MIKO STUDIO SLICER // MODULAR ASSET DECONSTRUCTION KIT", fill=(148, 163, 184, 255))
draw.line([(70, 105), (W-70, 105)], fill=(43, 48, 64, 255), width=2)

# 1. Primary 3D Extruded Logo (x: 70, y: 140, w: 580, h: 260)
# Crimson bevel
draw.text((92, 172), "MIKO", fill=(239, 68, 68, 255))
# Violet shadow
draw.text((86, 166), "MIKO", fill=(99, 102, 241, 255))
# Cyan glow
draw.text((80, 160), "MIKO", fill=(6, 182, 212, 255))
# Gold primary face
draw.text((74, 154), "MIKO", fill=(245, 158, 11, 255))

draw.text((76, 260), "STUDIO SLICER", fill=(248, 250, 252, 255))
draw.text((76, 310), "MULTI-LAYER ASSET DECONSTRUCTION ENGINE", fill=(100, 116, 139, 255))

# 2. Slice Emblem / Diamond Aperture (x: 740, y: 140, w: 320, h: 320)
draw.polygon([(900, 150), (1030, 280), (900, 410), (770, 280)], fill=(15, 23, 42, 255), outline=(245, 158, 11, 255), width=6)
draw.polygon([(900, 185), (995, 280), (900, 375), (805, 280)], fill=(99, 102, 241, 255))
draw.polygon([(900, 220), (960, 280), (900, 340), (840, 280)], fill=(6, 182, 212, 255))
draw.polygon([(900, 255), (925, 280), (900, 305), (875, 280)], fill=(248, 250, 252, 255))
draw.line([(750, 220), (1050, 340)], fill=(239, 68, 68, 255), width=8)

# 3. Brand Swatches Column (x: 1180, y: 150)
swatches = [
    ("Studio Gold", (245, 158, 11)),
    ("Electric Cyan", (6, 182, 212)),
    ("Deep Violet", (99, 102, 241)),
    ("Crimson Bevel", (239, 68, 68)),
    ("Obsidian Core", (15, 23, 42)),
    ("Paper White", (248, 250, 252))
]

for idx, (name, col) in enumerate(swatches):
    sy = 150 + idx * 54
    draw.ellipse([1180, sy, 1220, sy + 40], fill=col, outline=(255, 255, 255, 60), width=2)
    draw.text((1240, sy + 12), name, fill=(226, 232, 240, 255))

# 4. Modular Broadcast Lower-Third Banner (x: 70, y: 560, w: 980, h: 180)
draw.rectangle([70, 620, 1040, 715], fill=(15, 23, 42, 255), outline=(99, 102, 241, 255), width=2)
draw.rectangle([70, 575, 480, 620], fill=(245, 158, 11, 255))
draw.text((95, 590), "LEAD PRODUCTION ARCHITECT", fill=(15, 23, 42, 255))
draw.text((95, 650), "ALEX RIVERS", fill=(248, 250, 252, 255))
draw.rectangle([70, 715, 1040, 720], fill=(6, 182, 212, 255))

img.save("sample_concept.png", "PNG")
print("[OK] sample_concept.png generated successfully.")
