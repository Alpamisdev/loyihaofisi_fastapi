-- SQL script to create the refresh_tokens table
CREATE TABLE IF NOT EXISTS refresh_tokens (
    id INTEGER PRIMARY KEY,
    token VARCHAR NOT NULL UNIQUE,
    user_id INTEGER NOT NULL,
    expires_at TIMESTAMP NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    revoked BOOLEAN DEFAULT 0,
    revoked_at TIMESTAMP,
    FOREIGN KEY(user_id) REFERENCES admin_users(id)
);

-- Create an index on the token column for faster lookups
CREATE INDEX IF NOT EXISTS ix_refresh_tokens_token ON refresh_tokens(token);
