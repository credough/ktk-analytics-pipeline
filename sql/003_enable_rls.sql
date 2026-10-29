-- The live database already has RLS enabled on all five tables, verified by query;
-- this file makes new environments match that existing security state.
-- RLS is bypassed by service_role and the postgres role.
-- Verification date: 2026-10-30
--
-- Rollback:
-- ALTER TABLE public.dim_platform DISABLE ROW LEVEL SECURITY;
-- ALTER TABLE public.dim_follower_count DISABLE ROW LEVEL SECURITY;
-- ALTER TABLE public.dim_posts DISABLE ROW LEVEL SECURITY;
-- ALTER TABLE public.fact_daily_metrics DISABLE ROW LEVEL SECURITY;
-- ALTER TABLE public.fact_post_metrics DISABLE ROW LEVEL SECURITY;

ALTER TABLE public.dim_platform ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.dim_follower_count ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.dim_posts ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.fact_daily_metrics ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.fact_post_metrics ENABLE ROW LEVEL SECURITY;
