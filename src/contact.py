"""Hoja de contacto de previsualizaciones (herramienta de desarrollo)."""
import glob, sys, os
import skia
files = sorted(glob.glob(sys.argv[1] + "/f_*.png"))
cols = 6; w, h = 360, 640
rows = (len(files) + cols - 1) // cols
s = skia.Surface(cols * w, rows * h); c = s.getCanvas()
for i, f in enumerate(files):
    img = skia.Image.open(f)
    c.drawImageRect(img, skia.Rect.MakeXYWH((i % cols) * w, (i // cols) * h, w, h), skia.SamplingOptions(skia.FilterMode.kLinear))
    c.drawString(os.path.basename(f)[2:-4], (i % cols) * w + 8, (i // cols) * h + 40, skia.Font(None, 36), skia.Paint(Color=skia.ColorRED))
s.makeImageSnapshot().save(sys.argv[2])
