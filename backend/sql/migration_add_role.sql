-- Migration: Add role column to users table
-- Run this script to add role support to existing databases

-- Add role column if it doesn't exist
ALTER TABLE users ADD COLUMN IF NOT EXISTS role VARCHAR(50) DEFAULT 'user' CHECK (role IN ('admin', 'user'));

-- Set default role for existing users (if needed)
UPDATE users SET role = 'user' WHERE role IS NULL;
