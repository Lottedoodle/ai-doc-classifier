-- migrations/002_drop_legacy.sql
-- Safe cleanup for databases that ran the old slip/receipt schema.
DROP TABLE IF EXISTS files;
DROP TABLE IF EXISTS topics;
