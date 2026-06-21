"""
AYA vesica-animated.gif encoder
Reads gif-frames/frame-*.png and encodes to vesica-animated.gif using Pillow.
Run: python3 brand-assets/make-gif.py
"""
import os, glob, sys
from PIL import Image

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
FRAMES_DIR = os.path.join(SCRIPT_DIR, "gif-frames")
OUTPUT = os.path.join(SCRIPT_DIR, "vesica-animated.gif")
FPS = 15

frames_paths = sorted(glob.glob(os.path.join(FRAMES_DIR, "frame-*.png")))
if not frames_paths:
    print("No frames found in gif-frames/. Run render-gif.js first.")
    sys.exit(1)

print(f"Loading {len(frames_paths)} frames...")
frames = [Image.open(f).convert("P", palette=Image.ADAPTIVE, colors=32) for f in frames_paths]

duration_ms = int(1000 / FPS)  # 33ms per frame

print(f"Encoding GIF ({len(frames)} frames, {duration_ms}ms/frame)...")
frames[0].save(
    OUTPUT,
    save_all=True,
    append_images=frames[1:],
    optimize=True,
    loop=0,          # infinite loop
    duration=duration_ms,
    disposal=2,
)

size_kb = os.path.getsize(OUTPUT) / 1024
print(f"vesica-animated.gif written: {size_kb:.0f}KB")

if size_kb > 500:
    print(f"WARNING: GIF is {size_kb:.0f}KB — over 500KB budget.")
    print("Tip: reduce to 15fps by re-running with FPS=15, or use --quality 80 with gifski.")
