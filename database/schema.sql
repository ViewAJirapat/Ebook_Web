-- Schema for local-manga-reader SQLite database

CREATE TABLE IF NOT EXISTS books (
    id TEXT PRIMARY KEY,
    title TEXT NOT NULL,
    type TEXT NOT NULL CHECK(type IN ('folder', 'pdf')),
    total_pages INTEGER NOT NULL DEFAULT 0,
    cover_url TEXT,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    category TEXT DEFAULT 'General',
    rel_path TEXT DEFAULT ''
);

CREATE TABLE IF NOT EXISTS reading_progress (
    book_id TEXT PRIMARY KEY,
    last_page INTEGER NOT NULL DEFAULT 0,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (book_id) REFERENCES books (id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_books_title ON books(title);
CREATE INDEX IF NOT EXISTS idx_books_category ON books(category);
