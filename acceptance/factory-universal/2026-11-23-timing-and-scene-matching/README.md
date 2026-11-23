# Narration timing and shot matching

## Paper manufacturing, English, 30 seconds

The earlier job measured three distinct complete scripts at 26.496, 30.936 and 30.408 seconds. The new job excluded all three validated cache entries before looking up images. Its first new Google Cloud recording used Algenib and lasted 28.368 seconds at native speed.

Staged job `039a1185-31f3-40d3-ba4f-ccdb04f43fe5` produced 900 frames and 12 distinct photographs. Chrome decoded and played the 1080×1920 file. All 12 shot midpoints and their captions were inspected, including both shots of paper drying. Listening approval is pending.

## Bees, Ukrainian, 60 seconds

Staged job `d878ba1a-2c75-4c83-a716-2360aecb2620` passed technical checks, and all 24 rendered shot midpoints were inspected. The output did not pass visual review. Shots 2, 6, 10, 18 and 19 depicted predators, an ant or an uncertain wasp. Shots 12–14 illustrated honey production with general anatomy photographs. The technical receipt records the render independently of this editorial failure.

The next build requires evidence for the narrated biological feature or action before accepting a candidate. This applies when a scene has a source-linked visual target as well as when it uses the primary topic. The regression suite includes the rejected file descriptions and checks that photographs of nectar feeding do not qualify as evidence of honey production.

The earlier Polish, English, Russian and Ukrainian matrix is recorded in [the four-language test results](../2026-11-23-matrix-after-reconnect/README.md).

The second Ukrainian run (`571cb830-3b98-41c0-bd10-f12a7ad8e0ae`) also rendered 1,800 frames and 24 distinct photographs, with 59.256 seconds of the selected native voice. All 24 shot midpoints were inspected. Frame review again rejected the output. A bee fly was visible in shot 19, and frames about carrion feeding and honey reserves showed generic flower photos. The follow-up regression checks cover bee flies, carrion feeding, queen-bee references, pollinator inflections and explicit honey quantities. No Ukrainian example from this series was promoted. A new, full 60-second visual acceptance with the latest rule set remains pending.

## Public Studio check

After deployment of `1b496ca`, the unauthenticated Chrome form created EN30 job `a68f3e3b-a76c-4957-9900-ae6bf5735bcf`. Studio served and played its 900-frame MP4, manifest and credits. It reused the verified native recording with zero synthesis sends. The public render selected a different set of photos from the staged render. Midpoint review rejected shots 6, 7 and 10 because they show dry scrap-paper baling during the wet-sheet pressing step. The test job carries an assistant frame review requesting changes. Runtime regression fixtures require a distinction between these two pressing operations.

Deployment `69d6213` adds the pressing-context check. The same public form created fresh job `ac0ca5fe-2cc4-4a4a-8344-66beb043f0fc` after the fix. Chrome played the verified 30-second file, and the downloaded bytes and contact-sheet hash matched the inspected reference. All 12 actual midpoints and captions were inspected, including the wet-sheet presses and the drying shots. The native audio was reused with zero new synthesis sends. The previous marked test job is preserved.

The final Bee failure on the production insect rules is `cde0867a-62fc-4374-9fdb-b6a93a665829`. It exhausted the bounded search for a valid combination of facts and photos before synthesis. The accompanying scene diagnostics and worker receipt document the failure and zero voice attempts.

## Independent Ukrainian 60-second check

The deployed image processed «Вулкан» as job `61e98237-26ed-44f8-b42b-2bb64e6a9041`. The worker reached the 900-second deadline during shot selection, before speech synthesis. The receipt records zero voice attempts. The accompanying planning trace records scenes with unavailable matching assets.
