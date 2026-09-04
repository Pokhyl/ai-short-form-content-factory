# MoneyPrinterTurbo — HUMAN FAIL — 2026-09-04

MoneyPrinterTurbo is rejected as the production-core candidate for the short-form content factory.

## Exact reviewed artifacts

1. Turbocharger RU proof
   - SHA256 `1038a41c68f397d8dd80217272fef9c9cf2c52ea2bfd0a8bdc0d4ce2340ec844`
   - user rejected the artifact.

2. Volcano RU proof
   - SHA256 `158fd931cbd01d112500c0ef4c24c6ea7032799c23e59723d81babe9e7d69903`
   - final duration `19.466667 s` instead of the intended short target;
   - narration measured about `19.44 s`;
   - available capped visual material measured about `11.50 s`;
   - MoneyPrinterTurbo filled the gap by looping three clips;
   - user explicitly rejected the result as poor quality.

## General product defects proven

- the engine does not enforce the requested short duration as a product contract when prepared narration exceeds it;
- when visual material is insufficient, its normal behavior is to loop previously used clips rather than fail or acquire new relevant material;
- therefore technical completion can produce repetitive, visibly low-quality output;
- this behavior is unacceptable for the target product and must not be hidden with topic-specific patches, extra retries, or hard-coded media.

## Decision

`MoneyPrinterTurbo = HUMAN FAIL / rejected as production core.`

Do not integrate it into Studio/n8n/PostgreSQL and do not spend time patching its looping/timing behavior merely to make the current fixtures pass. Continue the engine bake-off with a different architecture/candidate.
