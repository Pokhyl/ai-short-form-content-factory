# V4 Cross-Topic Evidence / Representation Audit

Date: 2026-09-03

Purpose: verify that the next architecture is not shaped around one induction fixture. This audit covers three additional, materially different visual problems before new renderer logic is accepted.

## Case B — `Jak zbudowano Wieżę Eiffla` / PL

### Evidence availability

Primary factual source: official Eiffel Tower history/construction material.

Verified facts suitable for a short:

- digging began 26 January 1887;
- the tower was completed 31 March 1889;
- construction took 2 years, 2 months and 5 days;
- approximately 18,000 metallic parts were prepared;
- approximately 2.5 million rivets were used;
- prefabrication in the Levallois-Perret workshops was a central reason assembly could proceed quickly;
- historical construction imagery exists showing the actual tower during assembly.

### Representation decision

This is an `exact_media/history` case.

Correct visual language:

- exact Eiffel Tower construction photographs;
- exact present-day tower footage only when the narration refers to the finished object or transition in time;
- historical landscape images treated with portrait-safe collage/PIP/contain and camera motion;
- dates, rivet counts and construction stages as overlays on top of exact imagery;
- no generic Paris tourism footage as a factual substitute for construction evidence;
- no standalone text card replacing the tower imagery.

## Case C — `Как работает молния на одежде` / RU

### Evidence availability

Primary factual reference: YKK zipper structure/mechanism material.

Verified mechanism statement:

- zipper elements are bent/guided by the slider and interlock as the slider closes the chain.

Exact macro imagery and generic zipper close-ups can support the physical object, but generic fashion/model footage does not explain the mechanism.

### Representation decision

This is an `object + mechanism` case.

Correct visual language:

- exact macro zipper/slider footage or photos;
- close-up of teeth/elements entering the slider;
- an original motion graphic showing the slider channels bringing two element rows into engagement;
- labels/arrows as overlays over the macro or diagram;
- no fashion/lifestyle fallback merely because a zipper appears somewhere in frame;
- no copied vendor diagram required for production: vendor material is factual/reference evidence, while the project should render its own explanatory motion graphic.

## Case D — `OLED vs LCD: what actually changes` / EN

### Evidence availability

Primary factual references: Samsung Display / LG Display educational material.

Verified core distinction:

- OLED is self-emissive: individual pixels emit/control light without a backlight;
- LCD is non-emissive and requires a backlight behind the liquid-crystal/color-filter structure;
- the structural distinction makes a side-by-side explanatory graphic materially more useful than generic TV/phone stock.

### Representation decision

This is a `comparison + mechanism` case.

Correct visual language:

- original side-by-side motion graphic: LCD backlight -> liquid crystal/color layer -> viewer versus OLED self-emitting pixels -> viewer;
- exact display close-ups only when they show a visible consequence relevant to narration;
- concise `LCD` / `OLED` labels as overlays;
- no random smartphones/TVs as the main factual track;
- no full-screen text-only comparison cards replacing the visual explanation.

## Cross-topic conclusion

The audit confirms that `portrait stock + high cut frequency` cannot be the architecture.

Different topics need different truthful representation modes:

- exact/history -> exact archived media + collage/PIP/contain;
- physical mechanism -> macro exact media + original motion graphics;
- technology comparison -> original side-by-side diagram/motion graphics + exact supporting shots.

The shared renderer contract is therefore not `find a portrait clip for every beat`.

It is:

`semantic intent -> choose truthful representation -> maintain continuous meaningful visual track -> add text only as overlay/annotation -> render in vertical-safe composition`.

## General media-selection rule extracted from the audit

For factual content, a candidate is not acceptable because it is portrait, visually attractive or shares category words with the topic.

Before a full-screen photo/video shot is allowed, the storyboard must be able to state what factual subject/action it visibly represents.

If that cannot be stated truthfully, reject the candidate and change representation mode.

## Next engineering step

Implement one general timeline/storyboard contract validator and run it against all matrix fixtures before rendering:

- primary visual exists throughout normal narration;
- standalone text replacement rejected by default;
- generic fallback media rejected for factual beats;
- every visual beat names its semantic role and representation mode;
- horizontal exact evidence must declare contain/PIP/collage treatment;
- portrait full-screen media must still declare exact/justified visible subject;
- validation fixtures span all matrix classes rather than only induction.

This validator is a structural contract, not a semantic-threshold substitute. Human review remains authoritative.