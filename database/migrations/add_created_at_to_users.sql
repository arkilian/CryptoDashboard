-- Migration: Add created_at column to t_users table
-- Date: 2025-11-03
-- Description: Adds created_at timestamp to track user registration date

-- Add created_at column if it doesn't exist
ALTER TABLE t_users 
ADD COLUMN IF NOT EXISTS created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP;

-- Set created_at for existing users (use current timestamp as fallback)
UPDATE t_users 
SET created_at = CURRENT_TIMESTAMP 
WHERE created_at IS NULL;

-- Make the column NOT NULL after setting values
ALTER TABLE t_users 
ALTER COLUMN created_at SET DEFAULT CURRENT_TIMESTAMP;
