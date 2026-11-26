# Variable photo density

The worker prefers 6, 12, 18 or 24 unique photos at 15, 30, 45 or 60 seconds. When the available set cannot support that layout, the worker may use fewer photos while retaining at least two independently verified, distinct photos per narration beat and an average shot length of at most five seconds. The renderer enforces the exact frame count and duration.

The runtime assertions exercise a 12-to-8 shot reduction and rejection below the minimum. The FFmpeg regression renders a 15-second, 450-frame file using four generated fixture images and rejects a duplicated asset. The fixture tests the fallback independently of live provider coverage.

| Normal worker case | Result |
| --- | --- |
| «Микроскоп», Russian, 15 s. Job `14fc0e05-1115-43e8-8f77-d4ed52128bf0`. | Ready. 450 frames at 1080 × 1920, six distinct photos, two captioned beats and the selected native voice. All six midpoint images and their legible captions were inspected. The second beat shows microscopes as illustrations of a resolution concept. |
| «n8n автоматизация для фирм», Ukrainian, 45 s. Job `aaf257b6-8753-4463-9c10-ce804f2a3f07`. | Failed after the planner exhausted complete source narrations with scene-matched media. Zero native voice attempts. |

The real microscope run used the preferred six photos. Reduced photo counts were exercised by regression fixtures. The yacht-production request still lacks usable coverage in the configured source pipeline. Neither blocked topic has a verified MP4. Owner listening approval remains pending.

Studio deployed `d0ac987` after the queue was empty. The runtime, alignment and real FFmpeg checks passed. All eight application file hashes matched the server checkout, and the public health endpoint recovered after a transient 502 during restart.

After deployment, Chrome replayed completed Polish 15 s, English 30 s, Russian 45 s and Ukrainian 60 s outputs. The checks verified exact duration, 1080 × 1920 playback, the configured voices in the manifests, HTTP byte ranges and author credits. These were read-only playback checks of existing jobs.
