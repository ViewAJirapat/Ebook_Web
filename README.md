# Local Manga & Document Reader (`local-manga-reader`)

A lightweight, self-hosted Manga and Document reader built with **FastAPI**, **SQLite**, **PyMuPDF**, and **Vue 3 + Vite + Tailwind CSS**.

Packaged as a **single-container production image** with multi-stage Docker build, serving both the REST API and the frontend SPA on a single port.

---

## Quick Start (Docker Compose)

### 1. Start the Container

Run the following command in the project root:

```bash
docker compose up -d --build
```

### 2. Access the Application

Once launched, open your web browser:

- 📖 **Web App (Computer)**: [http://localhost:8085](http://localhost:8085)
- 📱 **Phone / Tablet**: `http://<YOUR_COMPUTER_IP>:8085` (e.g. `http://192.168.1.106:8085`) on the same Wi-Fi
  - *Tip*: Tap **"Add to Home Screen"** on your phone browser for a full-screen, native app-like experience!
- ⚡ **Interactive API Docs (Swagger UI)**: [http://localhost:8085/docs](http://localhost:8085/docs)
- 🩺 **Health Check**: [http://localhost:8085/api/health](http://localhost:8085/api/health)

### 3. Stop the Container

```bash
docker compose down
```

---

## 🚀 Adding Books to Your Library

You have two convenient ways to add books:

### Option A: Web Upload (Recommended)
1. Open the web app on your computer or phone.
2. Click the **"+ Add Book"** button in the header or next to "Your Books".
3. Choose your category, or create a new one on the fly.
4. Upload:
   - 📄 **PDF Document**: Single or multiple `.pdf` files (full Thai & Unicode filename support).
   - 📁 **Manga Folder**: Select an entire image directory from your computer.
   - 📦 **Comic Archive**: Upload `.zip` or `.cbz` files (automatically unpacked into a book).
5. The book is automatically indexed and appears immediately in **Your Books**!

### Option B: Direct Filesystem Copy


---

## Volume Mappings & Data Persistence

Your local folders are mounted directly into the container to ensure data is preserved across builds and updates:

| Host Directory | Container Path | Purpose |
|---|---|---|
| `./data/library` | `/app/data/library` | Put your manga folders and `.pdf` files here. |
| `./data/cache` | `/app/data/cache` | Generated book covers and rendered PDF pages cache. |
| `./database` | `/app/database` | SQLite database (`manga_reader.db`) storing metadata & reading progress. |

### Adding Books & Subdirectories to Your Library

You can organize your library into subdirectories like `manga/`, `document/`, or create new folders anytime (e.g. `comics/`, `novels/`, `tutorials/`):

```text
data/library/
├── manga/                     <-- Category 'manga'
│   ├── One Piece/             <-- Manga folder (with .jpg/.png/.webp)
│   └── Solo Leveling Ch 1/
├── document/                  <-- Category 'document'
│   ├── User_Guide.pdf         <-- PDF document
│   └── ลับสุดยอด1.pdf
└── any_new_folder/            <-- Automatically becomes a new category tab!
    └── story.pdf
```

1. Drop your manga folders or `.pdf` files into `./data/library/` or any subdirectory.
2. Open [http://localhost:8085](http://localhost:8085) in your browser.
3. Click the **Scan Library** button in the header. The reader will automatically detect new items, extract/generate covers, and create dynamic filter tabs for each folder.

---

## Architecture & Production Build

The production image uses a **multi-stage build** defined in [`Dockerfile`](Dockerfile):

- **Stage 1 (`node:20-alpine`)**: Installs frontend dependencies and compiles the Vue 3 + Tailwind CSS SPA into static production assets in `/app/frontend/dist`.
- **Stage 2 (`python:3.11-slim`)**: Installs PyMuPDF, Pillow, and backend dependencies, copies the backend code, and copies `/app/frontend/dist` into `/app/dist`.
- **FastAPI Unified Server**: FastAPI handles `/api/*` endpoints and `/covers/*`, `/library/*`, and `/pdf_pages/*` static routes, while transparently serving the compiled Vue 3 SPA with fallback to `index.html` for client-side routing on port `80` (mapped to host `8085`).

---

## Local Development (Without Docker)

If you prefer to run services locally outside Docker:

### 1. Backend

```bash
cd backend
python -m venv venv
# Windows:
.\venv\Scripts\activate
# Linux/macOS:
source venv/bin/activate

pip install -r requirements.txt
uvicorn main:app --reload --port 8000
```

### 2. Frontend

```bash
cd frontend
npm install
npm run dev
```

The Vite dev server runs at [http://localhost:5173](http://localhost:5173) and automatically proxies API and static requests to `http://localhost:8000`.

---

## Key Features

- 📖 **Universal Support**: Reads folder-based image collections, `.pdf` documents, and `.zip`/`.cbz` comic archives.
- 📤 **Web-Based Uploads**: Add books directly from the web UI with drag & drop, folder selection, and category organization.
- 📜 **Continuous Webtoon Reading**: Vertical infinite scroll with responsive lazy loading via `IntersectionObserver`.
- ⚡ **Zero-Gap Mode**: Seamless edge-to-edge manga reading with no borders or gaps.
- 🖼️ **On-Demand Page & Cover Caching**: PyMuPDF (`fitz`) and Pillow generate optimized WebP thumbnails and pages on the fly.
- 🇹🇭 **Full Thai & Unicode Support**: Seamlessly supports Thai (e.g. `ลับสุดยอด1.pdf`, `สวัสดี.pdf`) and other Unicode filenames.
- 📱 **Mobile & Tablet Optimized**: Responsive layout with touch navigation, fit-width toggling, and fullscreen reading.
- 💾 **Automatic Progress Syncing**: Automatically tracks reading progress to `localStorage` and continuously syncs with the SQLite database.
- 🌓 **Pure Dark Mode**: High-contrast, eye-friendly `slate-950` design for desktop and mobile reading.
