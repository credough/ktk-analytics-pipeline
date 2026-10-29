# Versioned warehouse SQL

Apply these files in order using the Supabase SQL editor:

1. Open `001_schema.sql` and run the complete file to create the warehouse tables.
2. Open `002_seed_platforms.sql` and run the complete file to insert the platform rows.
3. Open `003_enable_rls.sql` and run the complete file to enable row-level security on all five tables. No policies are created, so `anon` and `authenticated` are denied by default.

These files are safe to run again: table creation uses `IF NOT EXISTS`, platform inserts ignore conflicts, and enabling RLS on an already-protected table is a no-op.

**Never edit an applied SQL file.** To make a schema or data change, add a new, next-numbered SQL file and apply it after the existing files.

## Verify

Run this query in the Supabase SQL editor to verify RLS is enabled on the public tables:

```sql
select c.relname, c.relrowsecurity from pg_class c
join pg_namespace n on n.oid = c.relnamespace
where n.nspname = 'public' and c.relkind = 'r' order by 1;
```

An anon REST call to each of the five tables should return `[]`.
