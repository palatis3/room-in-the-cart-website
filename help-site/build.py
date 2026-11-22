"""Package the two public help pages as a static Vercel build."""
import argparse
from pathlib import Path
from shutil import copyfile

source = Path(__file__).resolve().parent
parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument("output", type=Path, help="New Vercel Build Output directory")
output = parser.parse_args().output
output.mkdir(parents=True, exist_ok=False)

copyfile(source / "config.json", output / "config.json")
for topic in ("privacy", "support"):
    relative = Path(topic) / "index.html"
    destination = output / "static" / relative
    destination.parent.mkdir(parents=True)
    copyfile(source / "public" / relative, destination)
