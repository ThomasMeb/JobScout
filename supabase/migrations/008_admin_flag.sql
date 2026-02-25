-- Add is_admin flag to profiles (replaces hardcoded admin IDs in backend)
ALTER TABLE profiles ADD COLUMN IF NOT EXISTS is_admin boolean NOT NULL DEFAULT false;

-- Set existing admin
UPDATE profiles SET is_admin = true WHERE id = 'e47109a9-0ea6-4fa6-83dd-478bb15f01e4';
