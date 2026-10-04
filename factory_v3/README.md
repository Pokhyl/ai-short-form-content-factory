# Factory v3 — availability first

This is the replacement branch authorized on 2026-10-04. It is not a finished factory.

The previous architecture froze narration and synthesized audio before proving that every shot had a distinct valid image. Actual execution12126 could cover only7/9 shots. Replacement order:

1. Research facts and discover real media within recorded provider budgets.
2. Review pixels and license/provenance; create an inventory of facts the media can actually show.
3. Compose a storyboard and narration from that inventory and cited facts. Do not silently drop requested factual scope: return an explicit coverage failure if material cannot support it.
4. Prove global unique assignment before voice. Freeze script, asset bytes, review contracts and attribution. Revalidate reviews whenever a contract or asset changes.
5. Synthesize once, align exact audio, reuse working FFmpeg renderer and perform actual media QA.
6. Use existing public service as an intake/review facade; move product decisions into ordinary versioned code instead of many embedded workflow scripts. Protect unrelated n8n automation.

Implemented: deterministic maximum matching, exact deficit witnesses and receipt revalidation before downstream work. CLI can replay the actual failed graph without external calls:

```sh
python3 factory_v3/visual_plan.py acceptance/release-coverage/12126-assignment-deficits.json --output acceptance/factory-v3/failed-12126-preflight.json
# Expected exit2: blocked,7/9. No TTS is invoked.
python3 -m unittest discover -s tests/factory_v3 -v
```

Not implemented yet: availability-led provider/review inventory, grounded composer, provenance freeze with actual asset hashes, durable runtime integration, intake/review wiring and release acceptance. Imported legacy approvals are only graph evidence, never acceptance of new contracts. Current production remains unchanged. Free-only policy, supported languages/durations, exact audio reuse and strict real-media checks remain requirements.
