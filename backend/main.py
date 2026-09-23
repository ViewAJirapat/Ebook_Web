import os
import re
import io
import datetime
from pathlib import Path
from typing import List, Optional, Union, Dict, Any
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Body
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field
import aiosqlite
from PIL import Image

try:
    import pymupdf as fitz  # PyMuPDF
except ImportError:
    try:
        import fitz
    except ImportError:
        fitz = None

# Base directories resolution
BASE_DIR = Path(__file__).resolve().parent
if BASE_DIR.name == "backend":
    BASE_DIR = BASE_DIR.parent

DATA_DIR = Path(os.environ.get("DATA_DIR", BASE_DIR / "data"))
LIBRARY_DIR = DATA_DIR / "library"
CACHE_DIR = DATA_DIR / "cache"
COVERS_DIR = CACHE_DIR / "covers"
PDF_PAGES_DIR = CACHE_DIR / "pdf_pages"
DATABASE_DIR = Path(os.environ.get("DATABASE_DIR", BASE_DIR / "database"))
DB_PATH = DATABASE_DIR / "manga_reader.db"
DIST_DIR = Path(os.environ.get("DIST_DIR", BASE_DIR / "dist"))
if not DIST_DIR.exists() and (BASE_DIR / "frontend" / "dist").exists():
    DIST_DIR = BASE_DIR / "frontend" / "dist"

# Ensure all working directories exist
for directory in [LIBRARY_DIR, COVERS_DIR, PDF_PAGES_DIR, DATABASE_DIR]:
    directory.mkdir(parents=True, exist_ok=True)

IMAGE_EXTENSIONS = {".webp", ".jpg", ".jpeg", ".png", ".bmp"}


# ---------------------------------------------------------------------------
# 1. SQLite Database Setup & Models
# ---------------------------------------------------------------------------
async def init_db():
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("""
            CREATE TABLE IF NOT EXISTS books (
                id TEXT PRIMARY KEY,
                title TEXT,
                type TEXT,
                total_pages INTEGER,
                cover_url TEXT,
                updated_at TIMESTAMP,
                category TEXT DEFAULT 'General',
                rel_path TEXT DEFAULT ''
            );
        """)
        await db.execute("""
            CREATE TABLE IF NOT EXISTS reading_progress (
                book_id TEXT PRIMARY KEY,
                last_page INTEGER,
                updated_at TIMESTAMP,
                FOREIGN KEY (book_id) REFERENCES books (id) ON DELETE CASCADE
            );
        """)

        # Migration: ensure category and rel_path columns exist on existing databases
        async with db.execute("PRAGMA table_info(books)") as cursor:
            cols = [row[1] for row in await cursor.fetchall()]
        if "category" not in cols:
            await db.execute("ALTER TABLE books ADD COLUMN category TEXT DEFAULT 'General'")
        if "rel_path" not in cols:
            await db.execute("ALTER TABLE books ADD COLUMN rel_path TEXT DEFAULT ''")

        await db.commit()


@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    yield


app = FastAPI(
    title="Local Manga & Document Reader API",
    version="1.0.0",
    lifespan=lifespan
)

# CORS setup for Vue 3 frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static routes for /covers, /library, and /pdf_pages
app.mount("/covers", StaticFiles(directory=COVERS_DIR), name="covers")
app.mount("/library", StaticFiles(directory=LIBRARY_DIR), name="library")
app.mount("/pdf_pages", StaticFiles(directory=PDF_PAGES_DIR), name="pdf_pages")


class ProgressPayload(BaseModel):
    page: int = Field(..., ge=0, description="0-indexed or 1-indexed current page number")


# ---------------------------------------------------------------------------
# 2. Helper Functions
# ---------------------------------------------------------------------------
def natural_sort_key(s: Any) -> list:
    """
    Support alphanumeric sorting (e.g., page 1, 2, 10).
    """
    return [int(text) if text.isdigit() else text.lower() for text in re.split(r'(\d+)', str(s))]


def get_safe_id_from_path(item_path: Path) -> str:
    r"""
    Generate a URL-safe deterministic ID based on the relative path to library.
    Preserves Unicode characters (Thai, Japanese, etc.) while sanitizing
    filesystem-reserved characters (\ / : * ? " < > |).
    """
    try:
        rel = item_path.relative_to(LIBRARY_DIR).as_posix()
    except ValueError:
        rel = item_path.name
    # Replace illegal filesystem and path separators only, keeping full Unicode text intact
    safe_id = re.sub(r'[\\/:*?"<>|\x00-\x1f]', '_', rel).strip('. ')
    return safe_id


def extract_or_generate_cover(item_path: Union[str, Path], book_id: Optional[str] = None) -> Optional[str]:
    """
    Extract or generate book cover:
    - If folder: find first .webp/.jpg/.png, resize to max 400x600 WebP at 80% quality,
      save to data/cache/covers/{book_id}.webp.
    - If PDF: use fitz (PyMuPDF) to render page 0 as pixmap, resize and save to
      data/cache/covers/{book_id}.webp.
    """
    path = Path(item_path)
    if not path.exists():
        return None

    if not book_id:
        book_id = get_safe_id_from_path(path)

    cover_target = COVERS_DIR / f"{book_id}.webp"
    cover_url = f"/covers/{book_id}.webp"

    # Return cached cover if already generated
    if cover_target.exists() and cover_target.stat().st_size > 0:
        return cover_url

    try:
        if path.is_dir():
            # Find first valid image file using natural sort
            image_files = [
                f for f in path.iterdir()
                if f.is_file() and f.suffix.lower() in IMAGE_EXTENSIONS
            ]
            if not image_files:
                return None

            image_files.sort(key=lambda f: natural_sort_key(f.name))
            first_image = image_files[0]

            with Image.open(first_image) as img:
                img = img.convert("RGB")
                img.thumbnail((400, 600), Image.Resampling.LANCZOS)
                img.save(cover_target, format="WEBP", quality=80)
            return cover_url

        elif path.is_file() and path.suffix.lower() == ".pdf":
            if fitz is None:
                raise RuntimeError("PyMuPDF (fitz) is not installed.")

            doc = fitz.open(path)
            if doc.page_count == 0:
                doc.close()
                return None

            first_page = doc.load_page(0)
            # Render page at 150 DPI for sharp cover quality
            pix = first_page.get_pixmap(dpi=150)
            img_bytes = pix.tobytes("png")
            doc.close()

            with Image.open(io.BytesIO(img_bytes)) as img:
                img = img.convert("RGB")
                img.thumbnail((400, 600), Image.Resampling.LANCZOS)
                img.save(cover_target, format="WEBP", quality=80)
            return cover_url

    except Exception as e:
        print(f"Error generating cover for {path}: {e}")
        return None

    return None


def discover_library_items(root_dir: Path) -> List[Dict[str, Any]]:
    """
    Recursively discover all books and documents in data/library/ and any subdirectories.
    - PDF files anywhere are treated as books.
    - Folders containing images are treated as manga/comic books.
    - Top-level subfolder becomes the category (e.g. manga, document, comics, etc.).
    """
    discovered = []

    for current_root, dirs, files in os.walk(root_dir):
        current_path = Path(current_root)

        # Exclude hidden directories (.cache, .git, etc.)
        dirs[:] = [d for d in dirs if not d.startswith(".")]

        # 1. Any PDF file is a book
        for f in sorted(files, key=natural_sort_key):
            if f.startswith("."):
                continue
            file_path = current_path / f
            if file_path.suffix.lower() == ".pdf":
                rel = file_path.relative_to(root_dir)
                category = rel.parts[0] if len(rel.parts) > 1 else "General"
                discovered.append({
                    "path": file_path,
                    "rel_path": rel.as_posix(),
                    "type": "pdf",
                    "category": category,
                    "title": file_path.stem
                })

        # 2. Check if current folder contains image files
        image_files = [
            f for f in files 
            if Path(f).suffix.lower() in IMAGE_EXTENSIONS and not f.startswith(".")
        ]
        if image_files and current_path != root_dir:
            rel = current_path.relative_to(root_dir)
            category = rel.parts[0] if len(rel.parts) > 1 else "General"

            # If folder is nested (e.g. manga/One Piece/Ch 1), format clear title
            if len(rel.parts) > 2:
                title = f"{rel.parts[-2]} - {current_path.name}"
            else:
                title = current_path.name

            discovered.append({
                "path": current_path,
                "rel_path": rel.as_posix(),
                "type": "folder",
                "category": category,
                "title": title
            })

    # Sort items naturally by category then title
    discovered.sort(key=lambda item: (natural_sort_key(item["category"]), natural_sort_key(item["title"])))
    return discovered


def resolve_book_path(book_id: str, rel_path: Optional[str] = None) -> Optional[Path]:
    """
    Resolve item path from book_id and rel_path within data/library/.
    """
    if rel_path:
        direct = LIBRARY_DIR / rel_path
        if direct.exists():
            return direct

    # Try direct match
    for entry in LIBRARY_DIR.iterdir():
        if get_safe_id_from_path(entry) == book_id or entry.name == book_id:
            return entry

    # Check recursive subdirectories
    for entry in LIBRARY_DIR.rglob("*"):
        if get_safe_id_from_path(entry) == book_id or entry.name == book_id:
            return entry

    return None


# ---------------------------------------------------------------------------
# 3. API Endpoints
# ---------------------------------------------------------------------------
@app.get("/api/health")
async def health_check():
    return {
        "status": "ok",
        "service": "local-manga-reader",
        "timestamp": datetime.datetime.now(datetime.timezone.utc).isoformat()
    }


@app.post("/api/admin/scan")
async def scan_library():
    """
    Scan data/library/ recursively for subdirectories and .pdf files.
    Extracts categories from top-level folders (manga, document, etc.).
    Upserts into database and generates missing covers.
    """
    if not LIBRARY_DIR.exists():
        LIBRARY_DIR.mkdir(parents=True, exist_ok=True)

    scanned_items = []
    now = datetime.datetime.now(datetime.timezone.utc).isoformat()

    candidates = discover_library_items(LIBRARY_DIR)

    async with aiosqlite.connect(DB_PATH) as db:
        for item in candidates:
            item_path = item["path"]
            book_id = get_safe_id_from_path(item_path)
            title = item["title"]
            book_type = item["type"]
            category = item["category"]
            rel_path = item["rel_path"]
            total_pages = 0

            if book_type == "folder":
                images = [
                    f for f in item_path.iterdir()
                    if f.is_file() and f.suffix.lower() in IMAGE_EXTENSIONS
                ]
                total_pages = len(images)
            elif book_type == "pdf":
                if fitz is not None:
                    try:
                        doc = fitz.open(item_path)
                        total_pages = doc.page_count
                        doc.close()
                    except Exception as e:
                        print(f"Failed to read PDF {item_path}: {e}")
                        total_pages = 0

            cover_url = extract_or_generate_cover(item_path, book_id=book_id) or ""

            # Upsert into books table with category and rel_path
            await db.execute("""
                INSERT INTO books (id, title, type, total_pages, cover_url, updated_at, category, rel_path)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(id) DO UPDATE SET
                    title = excluded.title,
                    type = excluded.type,
                    total_pages = excluded.total_pages,
                    cover_url = excluded.cover_url,
                    updated_at = excluded.updated_at,
                    category = excluded.category,
                    rel_path = excluded.rel_path
            """, (book_id, title, book_type, total_pages, cover_url, now, category, rel_path))

            scanned_items.append({
                "id": book_id,
                "title": title,
                "type": book_type,
                "category": category,
                "rel_path": rel_path,
                "total_pages": total_pages,
                "cover_url": cover_url
            })

        # Remove orphaned books that are no longer present in library
        scanned_ids = [item["id"] for item in scanned_items]
        if scanned_ids:
            placeholders = ",".join("?" for _ in scanned_ids)
            await db.execute(f"DELETE FROM books WHERE id NOT IN ({placeholders})", scanned_ids)

        await db.commit()

    return {
        "message": f"Successfully scanned {len(scanned_items)} items across library subdirectories.",
        "count": len(scanned_items),
        "items": scanned_items
    }


@app.get("/api/books")
async def get_books():
    """
    Return all books with category and reading progress.
    """
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute("""
            SELECT 
                b.id,
                b.title,
                b.type,
                b.total_pages,
                b.cover_url,
                b.updated_at,
                COALESCE(b.category, 'General') as category,
                COALESCE(b.rel_path, '') as rel_path,
                COALESCE(rp.last_page, 0) as last_page,
                rp.updated_at as progress_updated_at
            FROM books b
            LEFT JOIN reading_progress rp ON b.id = rp.book_id
            ORDER BY b.category COLLATE NOCASE ASC, b.title COLLATE NOCASE ASC
        """) as cursor:
            rows = await cursor.fetchall()
            books = [dict(row) for row in rows]

    return books


@app.get("/api/categories")
async def get_categories():
    """
    Return all available categories with book counts.
    """
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute("""
            SELECT COALESCE(category, 'General') as cat, COUNT(*) as count
            FROM books
            GROUP BY cat
            ORDER BY cat COLLATE NOCASE ASC
        """) as cursor:
            rows = await cursor.fetchall()
            return [{"category": row[0], "count": row[1]} for row in rows]


@app.get("/api/books/{book_id}")
async def get_book_by_id(book_id: str):
    """
    Return a single book with reading progress and category.
    """
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute("""
            SELECT 
                b.id,
                b.title,
                b.type,
                b.total_pages,
                b.cover_url,
                b.updated_at,
                COALESCE(b.category, 'General') as category,
                COALESCE(b.rel_path, '') as rel_path,
                COALESCE(rp.last_page, 0) as last_page,
                rp.updated_at as progress_updated_at
            FROM books b
            LEFT JOIN reading_progress rp ON b.id = rp.book_id
            WHERE b.id = ?
        """, (book_id,)) as cursor:
            row = await cursor.fetchone()
            if not row:
                raise HTTPException(status_code=404, detail="Book not found")
            return dict(row)


@app.get("/api/books/{book_id}/pages")
async def get_book_pages(book_id: str):
    """
    Return an ordered list of image URLs for reading.
    - If folder: return URLs pointing to static mounted files.
    - If PDF: extract/cache pages on-demand as WebP images via PyMuPDF and return their URLs.
    """
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute("SELECT * FROM books WHERE id = ?", (book_id,)) as cursor:
            book = await cursor.fetchone()

    if not book:
        item_path = resolve_book_path(book_id)
        if not item_path:
            raise HTTPException(status_code=404, detail="Book not found")
        book_type = "pdf" if item_path.is_file() and item_path.suffix.lower() == ".pdf" else "folder"
    else:
        book_type = book["type"]
        rel_path = book["rel_path"] if "rel_path" in book.keys() else None
        item_path = resolve_book_path(book_id, rel_path=rel_path)
        if not item_path:
            raise HTTPException(status_code=404, detail="Book source files not found on disk")

    page_urls: List[str] = []

    # 1. Folder of images
    if book_type == "folder":
        if not item_path.is_dir():
            raise HTTPException(status_code=400, detail="Expected directory for folder book type")

        image_files = [
            f for f in item_path.iterdir()
            if f.is_file() and f.suffix.lower() in IMAGE_EXTENSIONS
        ]
        image_files.sort(key=lambda f: natural_sort_key(f.name))

        for img in image_files:
            rel_path = img.relative_to(LIBRARY_DIR).as_posix()
            page_urls.append(f"/library/{rel_path}")

    # 2. PDF Document
    elif book_type == "pdf":
        if fitz is None:
            raise HTTPException(status_code=500, detail="PyMuPDF (fitz) is not installed on the server.")

        total_pages = 0
        if book and "total_pages" in book.keys() and book["total_pages"] and book["total_pages"] > 0:
            total_pages = book["total_pages"]
        else:
            try:
                doc = fitz.open(item_path)
                total_pages = doc.page_count
                doc.close()
            except Exception as e:
                raise HTTPException(status_code=500, detail=f"Error reading PDF: {str(e)}")

        page_urls = [f"/api/books/{book_id}/pages/{page_idx}" for page_idx in range(total_pages)]

    return {
        "book_id": book_id,
        "type": book_type,
        "total_pages": len(page_urls),
        "pages": page_urls
    }


@app.get("/api/books/{book_id}/pages/{page_index}")
async def get_book_single_page(book_id: str, page_index: int):
    """
    Serve a single page of a PDF book.
    If cached in data/cache/pdf_pages/{book_id}/page_{page_index}.webp, return immediately.
    Otherwise extract with PyMuPDF, save to cache as WebP, and return.
    """
    book_cache_dir = PDF_PAGES_DIR / book_id
    page_filename = f"page_{page_index}.webp"
    page_cache_path = book_cache_dir / page_filename

    # If cached file exists and is valid, return immediately
    if page_cache_path.exists() and page_cache_path.stat().st_size > 0:
        return FileResponse(page_cache_path, media_type="image/webp")

    # Find the book source path
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute("SELECT * FROM books WHERE id = ?", (book_id,)) as cursor:
            book = await cursor.fetchone()

    rel_path = book["rel_path"] if book and "rel_path" in book.keys() else None
    item_path = resolve_book_path(book_id, rel_path=rel_path)

    if not item_path or not item_path.exists():
        raise HTTPException(status_code=404, detail="Book source file not found")

    if fitz is None:
        raise HTTPException(status_code=500, detail="PyMuPDF (fitz) is not installed on the server.")

    try:
        book_cache_dir.mkdir(parents=True, exist_ok=True)
        doc = fitz.open(item_path)
        if page_index < 0 or page_index >= doc.page_count:
            doc.close()
            raise HTTPException(status_code=404, detail=f"Page {page_index} out of range (total: {doc.page_count})")

        page = doc.load_page(page_index)
        pix = page.get_pixmap(dpi=150)
        img_bytes = pix.tobytes("png")
        doc.close()

        with Image.open(io.BytesIO(img_bytes)) as img:
            img = img.convert("RGB")
            temp_cache_path = book_cache_dir / f"temp_{page_index}_{os.getpid()}.webp"
            img.save(temp_cache_path, format="WEBP", quality=85)
            temp_cache_path.replace(page_cache_path)

        return FileResponse(page_cache_path, media_type="image/webp")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error rendering page {page_index}: {str(e)}")


@app.post("/api/books/{book_id}/progress")
async def save_reading_progress(book_id: str, payload: ProgressPayload = Body(...)):
    """
    Save current page progress { page: int }.
    """
    async with aiosqlite.connect(DB_PATH) as db:
        # Verify book exists
        async with db.execute("SELECT id FROM books WHERE id = ?", (book_id,)) as cursor:
            book = await cursor.fetchone()

        if not book:
            raise HTTPException(status_code=404, detail="Book not found")

        now = datetime.datetime.now(datetime.timezone.utc).isoformat()
        await db.execute("""
            INSERT INTO reading_progress (book_id, last_page, updated_at)
            VALUES (?, ?, ?)
            ON CONFLICT(book_id) DO UPDATE SET
                last_page = excluded.last_page,
                updated_at = excluded.updated_at
        """, (book_id, payload.page, now))
        await db.commit()

    return {
        "status": "success",
        "book_id": book_id,
        "last_page": payload.page,
        "updated_at": now
    }


# ---------------------------------------------------------------------------
# 4. Frontend SPA Serving & Fallback Routing
# ---------------------------------------------------------------------------
@app.get("/{full_path:path}")
async def serve_spa(full_path: str):
    """
    Serve frontend static files or fallback to index.html for SPA client-side routing.
    """
    if DIST_DIR.exists():
        # Check if the requested file exists in DIST_DIR
        target_file = (DIST_DIR / full_path).resolve()
        try:
            # Secure check: ensure target_file is within DIST_DIR
            target_file.relative_to(DIST_DIR.resolve())
            if full_path and target_file.is_file():
                return FileResponse(target_file)
        except ValueError:
            pass

        # Fallback to index.html for SPA routing
        index_file = DIST_DIR / "index.html"
        if index_file.is_file():
            return FileResponse(index_file)

    return {
        "service": "local-manga-reader",
        "status": "running",
        "docs": "/docs",
        "health": "/api/health",
        "message": "Frontend dist not found. Please build the frontend or run via Docker."
    }

