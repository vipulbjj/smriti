import shutil
from pathlib import Path

src = Path(r"C:\Users\bajaj\AppData\Local\Temp\cursor\screenshots")
dest = Path(__file__).resolve().parent / "screenshots"
dest.mkdir(parents=True, exist_ok=True)
names = (
    "01-health-endpoint.png",
    "02-swagger-docs.png",
    "03-transcribe-language-hi.png",
    "03-transcribe-error.png",
    "03-transcribe-test.png",
)
for name in names:
    s = src / name
    if s.exists():
        shutil.copy2(s, dest / name)
        print(f"OK {name} -> {(dest / name).stat().st_size} bytes")
    else:
        print(f"MISSING {name}")
print("dest:", sorted(p.name for p in dest.iterdir()))
