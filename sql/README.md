# Versioned warehouse SQL

Apply these files in order using the Supabase SQL editor:

1. Open `001_schema.sql` and run the complete file to create the warehouse tables.
2. Open `002_seed_platforms.sql` and run the complete file to insert the platform rows.

Both files are safe to run again: table creation uses `IF NOT EXISTS`, and platform inserts ignore conflicts.

**Never edit an applied SQL file.** To make a schema or data change, add a new, next-numbered SQL file and apply it after the existing files.
