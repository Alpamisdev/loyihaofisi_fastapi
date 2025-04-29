-- SQL script to add metadata columns to the uploaded_files table

-- Add title column if it doesn't exist
ALTER TABLE uploaded_files ADD COLUMN title VARCHAR;

-- Add language column if it doesn't exist
ALTER TABLE uploaded_files ADD COLUMN language VARCHAR;

-- Add info column if it doesn't exist
ALTER TABLE uploaded_files ADD COLUMN info TEXT;
