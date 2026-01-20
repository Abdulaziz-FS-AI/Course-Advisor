-- KFUPM Chatbot - Supabase Database Schema
-- Copy and paste this into Supabase SQL Editor

-- Users table
CREATE TABLE IF NOT EXISTS users (
    id BIGSERIAL PRIMARY KEY,
    username TEXT UNIQUE NOT NULL,
    password_hash TEXT NOT NULL,
    role TEXT DEFAULT 'user',
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Create anonymous user
INSERT INTO users (username, password_hash, role)
VALUES ('anonymous_user', 'nopassword', 'user')
ON CONFLICT (username) DO NOTHING;

-- Chat sessions table
CREATE TABLE IF NOT EXISTS chat_sessions (
    id TEXT PRIMARY KEY,
    user_id BIGINT REFERENCES users(id),
    device_id TEXT,
    title TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Indexes for sessions
CREATE INDEX IF NOT EXISTS idx_sessions_device ON chat_sessions(device_id);
CREATE INDEX IF NOT EXISTS idx_sessions_updated ON chat_sessions(updated_at DESC);

-- Chat messages table
CREATE TABLE IF NOT EXISTS chat_messages (
    id BIGSERIAL PRIMARY KEY,
    session_id TEXT REFERENCES chat_sessions(id) ON DELETE CASCADE,
    role TEXT NOT NULL,
    content TEXT NOT NULL,
    timestamp TIMESTAMPTZ DEFAULT NOW()
);

-- Index for messages
CREATE INDEX IF NOT EXISTS idx_messages_session ON chat_messages(session_id);

-- Feedback table
CREATE TABLE IF NOT EXISTS feedback (
    id BIGSERIAL PRIMARY KEY,
    user_id BIGINT REFERENCES users(id),
    session_id TEXT,
    message_id BIGINT REFERENCES chat_messages(id) ON DELETE CASCADE,
    rating TEXT CHECK(rating IN ('up', 'down')),
    comment TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Indexes for feedback
CREATE INDEX IF NOT EXISTS idx_feedback_session ON feedback(session_id);
CREATE INDEX IF NOT EXISTS idx_feedback_created ON feedback(created_at DESC);

-- Database function to get sessions with message count
CREATE OR REPLACE FUNCTION get_device_sessions_with_count(p_device_id TEXT)
RETURNS TABLE (
    id TEXT,
    user_id BIGINT,
    device_id TEXT,
    title TEXT,
    created_at TIMESTAMPTZ,
    updated_at TIMESTAMPTZ,
    message_count BIGINT
) AS $$
BEGIN
    RETURN QUERY
    SELECT
        s.id,
        s.user_id,
        s.device_id,
        s.title,
        s.created_at,
        s.updated_at,
        COUNT(m.id) as message_count
    FROM chat_sessions s
    LEFT JOIN chat_messages m ON s.id = m.session_id
    WHERE s.device_id = p_device_id
    GROUP BY s.id, s.user_id, s.device_id, s.title, s.created_at, s.updated_at
    ORDER BY s.updated_at DESC;
END;
$$ LANGUAGE plpgsql;

-- Verify tables were created
SELECT
    table_name,
    (SELECT COUNT(*) FROM information_schema.columns WHERE table_name = t.table_name) as column_count
FROM information_schema.tables t
WHERE table_schema = 'public'
AND table_name IN ('users', 'chat_sessions', 'chat_messages', 'feedback')
ORDER BY table_name;
