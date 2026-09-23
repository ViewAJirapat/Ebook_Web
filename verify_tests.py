import os
import sys
import json
import glob
import re
from pathlib import Path

# Fix Windows console encoding if needed
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

# Add project root to sys.path
PROJECT_ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(PROJECT_ROOT))

print("=" * 60)
print("RUNNING VERIFICATION TESTS FOR LOCAL-MANGA-READER")
print("=" * 60)

# ==============================================================================
# TEST 1: Generate sample manga folder (webp images) & PDF using Pillow & PyMuPDF
# ==============================================================================
print("\n[TEST 1] Generating sample manga folder & PDF with Pillow & PyMuPDF...")

from PIL import Image, ImageDraw
try:
    import pymupdf as fitz
except ImportError:
    import fitz

LIBRARY_DIR = PROJECT_ROOT / "data" / "library"
LIBRARY_DIR.mkdir(parents=True, exist_ok=True)

# 1. Generate 1 sample manga folder with 3 dummy webp images in manga/
sample_manga_dir = LIBRARY_DIR / "manga" / "Solo Leveling - Chapter 01"
sample_manga_dir.mkdir(parents=True, exist_ok=True)

colors = [
    ((30, 41, 59), (99, 102, 241), "Solo Leveling - Cover"),
    ((15, 23, 42), (168, 85, 247), "Solo Leveling - Page 1"),
    ((2, 6, 23), (59, 130, 246), "Solo Leveling - Page 2")
]

for idx, (bg_color, fg_color, label) in enumerate(colors, start=1):
    img = Image.new("RGB", (400, 600), color=bg_color)
    draw = ImageDraw.Draw(img)
    # Draw shapes and borders
    draw.rectangle([20, 20, 380, 580], outline=fg_color, width=4)
    draw.rectangle([60, 200, 340, 400], fill=fg_color)
    webp_path = sample_manga_dir / f"page_{idx:02d}.webp"
    img.save(webp_path, "WEBP", quality=80)
    print(f"  -> Created WebP: {webp_path.relative_to(PROJECT_ROOT)} ({webp_path.stat().st_size} bytes)")

# 2. Generate 1 small sample PDF using PyMuPDF (fitz) in document/
doc_dir = LIBRARY_DIR / "document"
doc_dir.mkdir(parents=True, exist_ok=True)
pdf_path = doc_dir / "Manga_Reader_User_Guide.pdf"
doc = fitz.open()

# Page 1
page1 = doc.new_page(width=400, height=600)
page1.draw_rect(fitz.Rect(20, 20, 380, 580), color=(0.2, 0.4, 0.8), width=3)
page1.insert_text(fitz.Point(50, 150), "Local Manga Reader Guide", fontsize=18, color=(0.1, 0.1, 0.1))
page1.insert_text(fitz.Point(50, 200), "Page 1: Architecture & Features", fontsize=12, color=(0.3, 0.3, 0.3))

# Page 2
page2 = doc.new_page(width=400, height=600)
page2.draw_rect(fitz.Rect(20, 20, 380, 580), color=(0.8, 0.3, 0.2), width=3)
page2.insert_text(fitz.Point(50, 150), "Local Manga Reader Guide", fontsize=18, color=(0.1, 0.1, 0.1))
page2.insert_text(fitz.Point(50, 200), "Page 2: Keyboard Shortcuts & Modes", fontsize=12, color=(0.3, 0.3, 0.3))

doc.save(str(pdf_path))
doc.close()
print(f"  -> Created PDF: {pdf_path.relative_to(PROJECT_ROOT)} ({pdf_path.stat().st_size} bytes, 2 pages)")

print("[TEST 1 PASSED]: Successfully created sample WebP manga folder and PyMuPDF document.")


# ==============================================================================
# TEST 2 & 3: Verify Scan Endpoint, Database Population, Cover Generation & GET /api/books
# ==============================================================================
print("\n[TEST 2 & 3] Verifying Scan Endpoint, Database, Covers, and GET /api/books...")

from fastapi.testclient import TestClient
from backend.main import app, DB_PATH, COVERS_DIR

with TestClient(app) as client:
    # 1. Trigger scan endpoint
    scan_response = client.post("/api/admin/scan")
    assert scan_response.status_code == 200, f"Scan failed: {scan_response.status_code} {scan_response.text}"
    scan_data = scan_response.json()
    print(f"  -> Scan response status: {scan_response.status_code}")
    print(f"  -> Scanned item count: {scan_data.get('count')}")
    assert scan_data.get("count", 0) >= 2, "Expected at least 2 scanned items"

    # 2. Check generated covers in data/cache/covers/
    covers = list(COVERS_DIR.glob("*.webp"))
    print(f"  -> Found {len(covers)} generated cover(s) in {COVERS_DIR.relative_to(PROJECT_ROOT)}")
    assert len(covers) >= 2, "Expected at least 2 covers to be generated"
    for c in covers:
        assert c.stat().st_size > 0, f"Cover {c.name} is empty!"
        print(f"     * {c.name} ({c.stat().st_size} bytes)")

    # 3. Check GET /api/books returns valid JSON and items
    books_response = client.get("/api/books")
    assert books_response.status_code == 200, f"GET /api/books failed: {books_response.status_code}"
    books = books_response.json()
    assert isinstance(books, list), "Expected books to be a JSON list"
    assert len(books) >= 2, "Expected at least 2 books in response"
    print(f"  -> GET /api/books returned {len(books)} books:")
    for b in books:
        print(f"     * [{b.get('category')}] ID: {b['id']} | Title: '{b['title']}' | Type: {b['type']} | Pages: {b['total_pages']} | Cover: {b['cover_url']}")
        assert "id" in b and "title" in b and "type" in b and "total_pages" in b and "cover_url" in b and "category" in b and "rel_path" in b
        assert b["total_pages"] > 0, f"Book {b['title']} has 0 pages"

    # 4. Check GET /api/books/{book_id}/pages
    target_book = books[0]
    pages_response = client.get(f"/api/books/{target_book['id']}/pages")
    assert pages_response.status_code == 200, f"GET pages failed: {pages_response.status_code}"
    pages_data = pages_response.json()
    print(f"  -> GET /api/books/{target_book['id']}/pages returned {pages_data.get('total_pages')} page URLs")
    assert len(pages_data.get("pages", [])) > 0, "Pages list should not be empty"

    # 5. Check POST /api/books/{book_id}/progress
    progress_response = client.post(
        f"/api/books/{target_book['id']}/progress",
        json={"page": 2}
    )
    assert progress_response.status_code == 200
    prog_data = progress_response.json()
    assert prog_data.get("last_page") == 2
    print(f"  -> Saved reading progress: page {prog_data.get('last_page')}")

    # Re-fetch books to verify progress is persisted in the database
    updated_books = client.get("/api/books").json()
    matching = next(b for b in updated_books if b["id"] == target_book["id"])
    assert matching["last_page"] == 2, f"Expected last_page 2, got {matching['last_page']}"
    print(f"  -> Verified progress persistence in DB: {matching['title']} last_page={matching['last_page']}")

print("[TEST 2 & 3 PASSED]: Scan endpoint, DB upsert, covers generation, and JSON APIs verified.")


# ==============================================================================
# TEST 4: Ensure no broken imports or missing packages in backend and frontend
# ==============================================================================
print("\n[TEST 4] Verifying imports and dependencies across backend and frontend...")

# A. Backend imports check
backend_modules = [
    "fastapi",
    "uvicorn",
    "fitz",
    "PIL",
    "PIL.Image",
    "pydantic",
    "aiosqlite",
    "multipart"
]
for mod in backend_modules:
    __import__(mod)
    print(f"  -> Backend module '{mod}': OK")

# B. Frontend package and file integrity check
pkg_json_path = PROJECT_ROOT / "frontend" / "package.json"
assert pkg_json_path.exists(), "frontend/package.json missing"
with open(pkg_json_path, "r", encoding="utf-8") as f:
    pkg = json.load(f)

print(f"  -> Frontend dependencies:")
for dep, ver in pkg.get("dependencies", {}).items():
    print(f"     * {dep}: {ver}")
assert "vue" in pkg.get("dependencies", {})
assert "lucide-vue-next" in pkg.get("dependencies", {})
assert "tailwindcss" in pkg.get("devDependencies", {})
assert "vite" in pkg.get("devDependencies", {})

# Check all Vue components and verify internal imports
vue_files = list((PROJECT_ROOT / "frontend" / "src").rglob("*.vue"))
print(f"  -> Checking {len(vue_files)} Vue components for valid relative imports...")
for vf in vue_files:
    content = vf.read_text(encoding="utf-8")
    # Find relative imports like from './components/Navbar.vue'
    imports = re.findall(r"from\s+['\"](\.[^'\"]+)['\"]", content)
    for imp in imports:
        resolved = (vf.parent / imp).resolve()
        if not resolved.suffix:
            possible = [resolved.with_suffix(".vue"), resolved.with_suffix(".js")]
            assert any(p.exists() for p in possible), f"Broken relative import '{imp}' in {vf.name}"
        else:
            assert resolved.exists(), f"Broken relative import '{imp}' in {vf.name}"
    print(f"     * {vf.relative_to(PROJECT_ROOT)}: imports valid")

print("[TEST 4 PASSED]: All backend and frontend imports and packages are complete and unbroken.")

print("\n" + "=" * 60)
print("ALL VERIFICATION TESTS COMPLETED SUCCESSFULLY!")
print("=" * 60)
