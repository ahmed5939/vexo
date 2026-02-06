-- New table for tracking song additions to the library
CREATE TABLE IF NOT EXISTS song_library_entries (
    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
    song_id INTEGER REFERENCES songs(id) ON DELETE CASCADE,
    source TEXT CHECK(source IN ('request', 'like', 'import')),
    added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (user_id, song_id, source)
);

-- Index for library queries
CREATE INDEX IF NOT EXISTS idx_library_song ON song_library_entries(song_id);
CREATE INDEX IF NOT EXISTS idx_library_user ON song_library_entries(user_id);
