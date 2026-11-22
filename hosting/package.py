from hashlib import sha256
from html.parser import HTMLParser
from pathlib import Path
import json
import sys
import zipfile

hosting = Path(__file__).resolve().parent
public = hosting.parent / "dist"
name = sys.argv[1]
archive_path = hosting / f"{name}.zip"

class Robots(HTMLParser):
    def __init__(self):
        super().__init__()
        self.noindex = False

    def handle_starttag(self, tag, attributes):
        attrs = dict(attributes)
        if tag == "meta" and attrs.get("name", "").lower() == "robots":
            self.noindex |= "noindex" in {v.strip().lower() for v in attrs.get("content", "").split(",")}

assets = {}
for path in sorted(public.rglob("*")):
    relative = path.relative_to(public)
    if any(part.startswith(".") for part in relative.parts) or path.is_symlink():
        raise ValueError(f"Unexpected hidden path or symlink: {relative}")
    if path.is_file():
        assets[str(relative)] = path
for needed in ("index.html", "es/index.html"):
    if needed not in assets:
        raise ValueError(f"Missing locale homepage: {needed}")
for special in ("_worker.js", "_headers"):
    if special in assets:
        raise ValueError(f"Conflicting deployment config in dist: {special}")
    assets[special] = hosting / special
assets.setdefault("404.html", hosting / "404.html")
manifest = {}
with zipfile.ZipFile(archive_path.with_suffix(".partial"), "w", compression=zipfile.ZIP_DEFLATED) as archive:
    for relative, local in sorted(assets.items()):
        data = local.read_bytes()
        if len(data) > 25 * 1024 * 1024:
            raise ValueError(f"Exceeds dashboard asset limit: {relative}")
        if relative.lower().endswith(".html"):
            parser = Robots()
            parser.feed(data.decode("utf-8"))
            if not parser.noindex:
                raise ValueError(f"Missing robots meta noindex: {relative}")
        # Fix archive metadata so packaging identical files reproduces the upload.
        member = zipfile.ZipInfo(relative, date_time=(1980, 1, 1, 0, 0, 0))
        member.create_system = 3
        member.external_attr = 0o100644 << 16
        archive.writestr(member, data, compress_type=zipfile.ZIP_DEFLATED)
        manifest[relative] = {"bytes": len(data), "sha256": sha256(data).hexdigest()}
archive_path.with_suffix(".partial").replace(archive_path)
(hosting / f"{name}-manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")
print(f"{len(manifest)} files, {archive_path.stat().st_size:,} compressed bytes, SHA-256 {sha256(archive_path.read_bytes()).hexdigest()}")
