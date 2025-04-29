-- SQL script to fix the uploaded_files table

-- Create a temporary table with the correct schema
CREATE TABLE uploaded_files_temp (
    id INTEGER PRIMARY KEY,
    filename VARCHAR NOT NULL,
    original_filename VARCHAR NOT NULL,
    file_path VARCHAR NOT NULL,
    file_url VARCHAR NOT NULL,
    file_size INTEGER,
    mime_type VARCHAR,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    uploaded_by INTEGER,
    FOREIGN KEY(uploaded_by) REFERENCES admin_users(id)
);

-- Copy data from the original table to the temporary table
INSERT INTO uploaded_files_temp (id, filename, original_filename, file_path, file_url, file_size, mime_type, created_at, uploaded_by)
SELECT id, filename, original_filename, file_path, file_url, file_size, mime_type, created_at, uploaded_by
FROM uploaded_files;

-- Drop the original table
DROP TABLE uploaded_files;

-- Rename the temporary table to the original table name
ALTER TABLE uploaded_files_temp RENAME TO uploaded_files;
