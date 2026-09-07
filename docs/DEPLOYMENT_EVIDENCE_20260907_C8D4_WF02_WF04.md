# Deployment Evidence — 2026-09-07 — c8d4 WF02/WF04

Source checkpoint: `c8d4da01d725821055467245cfa9dbfb7da54064`, exact tree `54b8d2da3d127f5722fa7061a50e9550095ee952`.

Production predeploy active/new/running/waiting executions: `0`.

Rollback capture:
`/opt/ai-short-form-content-factory-runtime-backups/wf02-wf04-c8d4-20260907T203827Z`

Only these workflows were imported/published:
- WF02 `TJfA4ZYUEKSTad6k`
- WF04 `M6VisualSourcing1`

Both imports matched the verified source before publication:
- WF02 source/current core SHA256 `35cefa8c34966502ef1a26725cb7a147374029f9e52e365b83940b88540e4f8f`, 34 nodes.
- WF04 source/current core SHA256 `f22209977b74883bdac6c4d2e0a35b354f3575d0a9b4044eedeb42962d676d9a`, 19 nodes.

Both `n8n publish:workflow` commands explicitly required restart. Exactly one n8n restart was performed after both publications. `/healthz` returned HTTP 200 `{"status":"ok"}`.

Postdeploy:
- WF02 active/current/activeVersionId: `6aca8273-d618-49d0-93fc-bbe3502b09e4`.
- WF02 source/current parity PASS; source/published nodes+connections parity PASS. Published core SHA256 `8e1b987db261e509f7b9212437a3c8341428ba11e354517c83f375c65fb80498`.
- WF04 active/current/activeVersionId: `c4cdb776-1c63-4cce-a810-03013dadc5cd`.
- WF04 source/current parity PASS; source/published nodes+connections parity PASS. Published core SHA256 `c22c81f0d0b974acf1aa8afeeb6c188aebf8d9894f6216aa6dce853463c4196f`.
- Postdeploy active/new/running/waiting executions: `0`.

Unchanged components:
- WF03 active/current version remains `165590b5-43f7-4e1d-b756-966fd1152292`.
- media-worker image remains `sha256:fe5b0dc2da7fa8e1771ec032b9be77d31757b8e3b3af5909a6f4fcb3fe7a0aec`.
- WF05/PostgreSQL/media-worker were not redeployed.

Next exact step: submit exactly one NEW normal `How the Panama Canal locks work / ru / 15` job through WF01, follow WF01→WF05 autonomously, preserve exact failure evidence if it fails, or verify exact MP4 path/SHA256/ffprobe and deliver it for HUMAN review if it renders. Failed job `b978e057-ab76-413d-8839-bcec6512fbe1` remains immutable.
