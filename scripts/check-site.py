"""Validate the static site's local links, images and binary download targets."""

from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urlsplit

ROOT = Path(__file__).resolve().parents[1]
SITE = ROOT / "site"


class Page(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.links = []
        self.ids = set()
        self.images = []

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if "id" in attrs:
            assert attrs["id"] not in self.ids, f"Duplicate ID: {attrs['id']}"
            self.ids.add(attrs["id"])
        for attribute in ("href", "src"):
            if attribute in attrs:
                self.links.append(attrs[attribute])
        if tag == "img":
            assert "alt" in attrs, "Image needs an alt attribute"
            self.images.append(attrs["src"])


def main():
    page = Page()
    page.feed((SITE / "index.html").read_text())
    for link in page.links:
        url = urlsplit(link)
        if url.scheme or url.netloc:
            assert url.scheme == "https", f"Expected HTTPS: {link}"
            continue
        if url.path:
            target = (SITE / url.path).resolve()
            assert target.is_relative_to(SITE), f"Link escapes site: {link}"
            assert target.is_file() and target.stat().st_size, f"Missing asset: {link}"
        if url.fragment and not url.path:
            assert url.fragment in page.ids, f"Missing anchor: {link}"
    base = "https://github.com/Evilchuck666/QuakeDock/releases/latest/download/"
    for package in ("linux-x64.tar.gz", "windows-x64.zip", "macos-x64.zip", "macos-arm64.zip"):
        assert base + "QuakeDock-" + package in page.links, f"Missing download: {package}"
    assert "https://github.com/Evilchuck666/QuakeDock" in page.links
    for channel in (
        "https://aur.archlinux.org/packages/quakedock-bin",
        "https://pypi.org/project/quakedock/",
    ):
        assert channel in page.links, f"Missing install channel: {channel}"
    for capture in ("campaign", "multiplayer"):
        path = f"assets/screenshots/{capture}.png"
        assert path in page.images, f"Missing screenshot: {capture}"
        assert (SITE / path).read_bytes().startswith(b"\x89PNG\r\n\x1a\n")
    assert (SITE / ".nojekyll").is_file()
    print(f"Site OK: {len(page.links)} links, {len(page.images)} images, 4 binary downloads.")


if __name__ == "__main__":
    main()
