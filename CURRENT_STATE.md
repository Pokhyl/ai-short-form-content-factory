# Current State

Clean rebuild baseline.

## Runtime
- PostgreSQL 18 (project-local)
- n8n 2.37.10 (project-local)
- short-video-maker tiny image

## Working flows
- WF01 Render Short Video: POST `/webhook/short-video/render`
- WF02 Video Status: GET `/webhook/short-video/status?videoId=...`

## Proof
- First successful render ID: `cmtxegw35000001mo19c30yze`
- Output: H.264/AAC, 1080x1920, 25 fps, 4.246 s

## Not implemented yet
- topic -> script generation
- multilingual TTS
- durable job table / idempotency
- public review/download surface
- TikTok draft upload
