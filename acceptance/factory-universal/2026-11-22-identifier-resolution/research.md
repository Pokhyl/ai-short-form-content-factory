# Identifier source checks

The Studio report for `n8n автоматизация для фирм` (Ukrainian, 45 s) was recorded as `7e938043-c207-498e-8f2f-74ece66cdcd1` with the old generic clarification message.

Checks ran in the factory runtime with isolated SQLite and a fresh cache. `checks.py` and `alignment_checks.py` passed. The current source resolver used live Wikipedia responses for these briefs.

| Brief | Output language | Research result |
| --- | --- | --- |
| n8n автоматизация для фирм | Ukrainian | Found English article `N8n`. The worker reports the unavailable Ukrainian source and does not start synthesis. |
| 7-Zip для архівів | Ukrainian | Matched native article `7-Zip`. |
| MP3 kompresja dźwięku | Polish | Matched native article `MP3`. |
| B2B sales | English | Resolved the exact identifier redirect to `Business-to-business`. |

These checks cover source discovery and worker diagnostics. Fixtures exercise the requirement that a planned script include the requested focus. They generated no MP4s.

## Production verification

The updated worker (`55238bd`) processed one new submission from the public form for the original brief. Studio linked the English article and reported the lack of a usable Ukrainian article. The original job was preserved. The job list initially omitted the reason field from its summary. Release `105f007` passes it through, and the browser verified the source-specific card and link.

A separate public-form job for `photo synthesis` (English, 15 s) reached ready with the selected Google voice, six distinct images, 450 frames, exact duration, successful complete decode and a matching SHA-256. Chromium played the new 1080×1920 MP4 after deployment. The attached midpoint frames show complete captions. The two shots for the final sentence show algae without explaining the specific photosynthetic mechanism, a limitation of the selected narration and visual context. Listening approval is pending.
