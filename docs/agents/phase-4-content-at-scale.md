# Phase 4 — Content at Scale (AI Visual Asset Generation)

## Scope

- Brief-driven AI image generation (Imagen 4.0 fast)
- Brief-driven AI video generation (Veo 3.1 lite) with operation polling
- Grounding prompts with retrieved org context from unified KB
- Image-to-video reference animation flow
- Supabase storage for assets (`content-assets` bucket) and DB logging
- Autoregistration of generated metadata into RAG Memory
- Content Studio gallery workspace UI with lightboxes and download triggers

## Exit criteria

- [x] Create content asset record -> dispatch Celery task
- [x] Prompt enriches using Knowledge Base retrieval + linked campaigns
- [x] Generated files upload to private storage, and records update
- [x] Assets are logged back to unified KB with kind `content_asset`
- [x] Frontend Content Studio workspace UI complete

## Key files

- `supabase/migrations/20260709000000_content_assets.sql`
- `services/core/src/stoa_core/content/generate_image.py`
- `services/core/src/stoa_core/content/generate_video.py`
- `services/core/src/stoa_core/content/enrich.py`
- `services/api/app/tasks/content.py`
- `services/api/app/routers/content.py`
- `apps/web/src/app/(app)/content/`

## Future

- Audio layer (voiceovers, background music)
- Video extensions and image inpainting/editing
- Dynamic template branding overlay
