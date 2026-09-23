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

- 📖 **Manga Reader Web App**: [http://localhost:8085](http://localhost:8085)
- ⚡ **Interactive API Docs (Swagger UI)**: [http://localhost:8085/docs](http://localhost:8085/docs)
- 🩺 **Health Check**: [http://localhost:8085/api/health](http://localhost:8085/api/health)

### 3. Stop the Container

```bash
docker compose down
```

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

- 📖 **Universal Support**: Reads folder-based image collections and `.pdf` files.
- 📜 **Continuous Webtoon Reading**: Vertical infinite scroll with responsive lazy loading via `IntersectionObserver`.
- ⚡ **Zero-Gap Mode**: Seamless edge-to-edge manga reading with no borders or gaps.
- 🖼️ **On-Demand Page & Cover Caching**: PyMuPDF (`fitz`) and Pillow generate optimized WebP thumbnails and pages on the fly.
- 💾 **Automatic Progress Syncing**: Automatically tracks reading progress to `localStorage` and continuously syncs with the SQLite database.
- 🌓 **Pure Dark Mode**: High-contrast, eye-friendly `slate-950` design for desktop and mobile reading.
