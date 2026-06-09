-- Greenfield reset: drop legacy GTM/marketing tables, preserve auth.users
-- Apply only when migrating from the old schema.

drop table if exists public.report_exports cascade;
drop table if exists public.gtm_reports cascade;
drop table if exists public.run_events cascade;
drop table if exists public.agent_artifacts cascade;
drop table if exists public.research_sources cascade;
drop table if exists public.agent_tasks cascade;
drop table if exists public.gtm_runs cascade;
drop table if exists public.gtm_plan_messages cascade;
drop table if exists public.company_gtm_plans cascade;
drop table if exists public.marketing_artifacts cascade;
drop table if exists public.marketing_tasks cascade;
drop table if exists public.marketing_messages cascade;
drop table if exists public.marketing_chats cascade;
drop table if exists public.company_competitors cascade;
drop table if exists public.company_knowledge cascade;
drop table if exists public.companies cascade;

-- Keep waitlist if exists
-- Keep auth.users untouched
