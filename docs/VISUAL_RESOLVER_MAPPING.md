# Narration → entity → media

Validation: 33/33 tests pass on macOS (Node 24) and in the built Linux amd64 renderer (Node 22), with network disabled for the container suite. Docker image build passes. Read-only live UK preflight: 8/8 scenes resolve. No production deployment, TTS call, production job, or production render was performed.

## Live Ukrainian acceptance mapping

Captured 2026-09-13. Exact source revision and API responses are retained in `tests/fixtures/wikimedia-uk.json`. Montages intentionally contain all four listed members. Same-entity repetitions below occur only after no unused exact candidate is available in the verified search pool.

| # | Narration | Entity / Wikidata | Media | Evidence |
|---|---|---|---|---|
| 1 | Меркурій, Венера, Земля та Марс, звані також планетами земної групи, складаються з силікатів. | Inner planet / Q3504248 | Inner planet: File:Mercury_in_true_color.jpg + File:Venus_from_Mariner_10.jpg + File:Meteosat-12-fci-march-equinox-2025-noon.jpg + File:Mars_-_August_30_2021_-_Flickr_-_Kevin_M._Gill.png | exact_listed_members |
| 2 | Юпітер, Сатурн, Уран та Нептун, звані також газовими гігантами, масивніші, ніж планети земної групи. | Gas giant / Q121750 | Gas giant: File:Jupiter_OPAL_2024.png + File:Saturn_global_view_from_Cassini,_rings_open_Better_Colour.png + File:Uranus_Voyager2_color_calibrated.png + File:Neptune_Voyager2_color_calibrated.png | exact_listed_members |
| 3 | У Сонячній системі є дві ділянки, заповнені малими тілами. | Small Solar System body / Q193275 | File:Euler_diagram_of_solar_system_bodies.svg | exact_english_wikipedia |
| 4 | Пояс астероїдів, що розташований між Марсом і Юпітером, подібний до планет земної групи. | Asteroid belt / Q2179 | File:Asteroid_belt_positions-en.png | exact_english_wikipedia |
| 5 | Найбільшими об'єктами поясу астероїдів є Церера, Паллада та Веста. | Asteroid belt / Q2179 | File:Asteroid_belt_positions-en.png | exact_english_wikipedia / same_entity_no_alternative |
| 6 | За орбітою Нептуна розташовано транснептунові об'єкти, що містять замерзлу воду. | Trans-Neptunian object / Q6592 | File:10 Largest Trans-Neptunian objects (TNOS).png | exact_entity_commons |
| 7 | Найбільшими з них є Плутон, Седна, Гаумеа, Макемаке та Ерида. | Trans-Neptunian object / Q6592 | File:10 Largest Trans-Neptunian objects (TNOS).png | exact_entity_commons / same_entity_no_alternative |
| 8 | Сонячний вітер, потік плазми від Сонця, утворює бульбашку, яка називається геліосферою. | Solar wind / Q79833 | File:Solar_wind_flow.gif | exact_english_wikipedia |

## Deterministic multilingual contract fixtures

These 32 mappings use synthetic API responses. Their media filenames are test data, not claims that the files exist on Wikimedia. The separate live mapping above validates actual source data. Full resolver logic, language dictionaries, identity checks and media validation run in both modes.

| Language | Narration | Entity | Fixture media |
|---|---|---|---|
| UK | Меркурій, Венера, Земля та Марс, звані також планетами земної групи, складаються з силікатів. | Terrestrial planet | Terrestrial planet: File:Mercury (planet).jpg + File:Venus.jpg + File:Earth.jpg + File:Mars.jpg |
| UK | Юпітер, Сатурн, Уран та Нептун, звані також газовими гігантами, масивніші, ніж планети земної групи. | Gas giant | Gas giant: File:Jupiter.jpg + File:Saturn.jpg + File:Uranus.jpg + File:Neptune.jpg |
| UK | У Сонячній системі є дві ділянки, заповнені малими тілами. | Small Solar System body | File:Small Solar System body.jpg |
| UK | Пояс астероїдів, що розташований між Марсом і Юпітером, подібний до планет земної групи. | Asteroid belt | File:Asteroid belt.jpg |
| UK | Найбільшими об'єктами поясу астероїдів є Церера, Паллада та Веста. | Asteroid belt | File:Asteroid belt.jpg |
| UK | За орбітою Нептуна розташовано транснептунові об'єкти, що містять замерзлу воду. | Trans-Neptunian object | File:Trans-Neptunian object.jpg |
| UK | Найбільшими з них є Плутон, Седна, Гаумеа, Макемаке та Ерида. | Trans-Neptunian object | File:Trans-Neptunian object.jpg |
| UK | Сонячний вітер, потік плазми від Сонця, утворює бульбашку, яка називається геліосферою. | Solar wind | File:Solar wind.jpg |
| RU | Меркурий, Венера, Земля и Марс, называемые также планетами земной группы, состоят из силикатов. | Terrestrial planet | Terrestrial planet: File:Mercury (planet).jpg + File:Venus.jpg + File:Earth.jpg + File:Mars.jpg |
| RU | Юпитер, Сатурн, Уран и Нептун, называемые также газовыми гигантами, массивнее, чем планеты земной группы. | Gas giant | Gas giant: File:Jupiter.jpg + File:Saturn.jpg + File:Uranus.jpg + File:Neptune.jpg |
| RU | В Солнечной системе есть две области, заполненные малыми телами. | Small Solar System body | File:Small Solar System body.jpg |
| RU | Пояс астероидов, который расположен между Марсом и Юпитером, похож на планеты земной группы. | Asteroid belt | File:Asteroid belt.jpg |
| RU | Крупнейшими объектами пояса астероидов являются Церера, Паллада и Веста. | Asteroid belt | File:Asteroid belt.jpg |
| RU | За орбитой Нептуна расположены транснептуновые объекты, которые содержат лёд. | Trans-Neptunian object | File:Trans-Neptunian object.jpg |
| RU | Крупнейшими из них являются Плутон, Седна, Хаумеа, Макемаке и Эрида. | Trans-Neptunian object | File:Trans-Neptunian object.jpg |
| RU | Солнечный ветер, поток плазмы от Солнца, образует пузырь, который называется гелиосферой. | Solar wind | File:Solar wind.jpg |
| PL | Merkury, Wenus, Ziemia i Mars, zwane także planetami skalistymi, składają się z krzemianów. | Terrestrial planet | Terrestrial planet: File:Mercury (planet).jpg + File:Venus.jpg + File:Earth.jpg + File:Mars.jpg |
| PL | Jowisz, Saturn, Uran i Neptun, zwane także gazowymi olbrzymami, są masywniejsze niż planety skaliste. | Gas giant | Gas giant: File:Jupiter.jpg + File:Saturn.jpg + File:Uranus.jpg + File:Neptune.jpg |
| PL | W Układzie Słonecznym są dwa obszary wypełnione małymi ciałami. | Small Solar System body | File:Small Solar System body.jpg |
| PL | Pas planetoid, który znajduje się między Marsem i Jowiszem, przypomina planety skaliste. | Asteroid belt | File:Asteroid belt.jpg |
| PL | Największymi obiektami pasa planetoid są Ceres, Pallas i Westa. | Asteroid belt | File:Asteroid belt.jpg |
| PL | Za orbitą Neptuna znajdują się obiekty transneptunowe, które zawierają lód. | Trans-Neptunian object | File:Trans-Neptunian object.jpg |
| PL | Największymi z nich są Pluton, Sedna, Haumea, Makemake i Eris. | Trans-Neptunian object | File:Trans-Neptunian object.jpg |
| PL | Wiatr słoneczny, strumień plazmy ze Słońca, tworzy bańkę zwaną heliosferą. | Solar wind | File:Solar wind.jpg |
| EN | Mercury, Venus, Earth and Mars, also called terrestrial planets, consist of silicates. | Terrestrial planet | Terrestrial planet: File:Mercury (planet).jpg + File:Venus.jpg + File:Earth.jpg + File:Mars.jpg |
| EN | Jupiter, Saturn, Uranus and Neptune, also known as gas giants, are more massive than terrestrial planets. | Gas giant | Gas giant: File:Jupiter.jpg + File:Saturn.jpg + File:Uranus.jpg + File:Neptune.jpg |
| EN | In the Solar System there are two regions filled with small bodies. | Small Solar System body | File:Small Solar System body.jpg |
| EN | The asteroid belt, which lies between Mars and Jupiter, resembles terrestrial planets. | Asteroid belt | File:Asteroid belt.jpg |
| EN | The largest objects of the asteroid belt are Ceres, Pallas and Vesta. | Asteroid belt | File:Asteroid belt.jpg |
| EN | Beyond the orbit of Neptune lie trans-Neptunian objects, which contain ice. | Trans-Neptunian object | File:Trans-Neptunian object.jpg |
| EN | The largest of them are Pluto, Sedna, Haumea, Makemake and Eris. | Trans-Neptunian object | File:Trans-Neptunian object.jpg |
| EN | Solar wind, a stream of plasma from the Sun, forms a bubble called the heliosphere. | Solar wind | File:Solar wind.jpg |

## Other regression coverage

The complete executable scenarios and expected failures are in `tests/safety.test.cjs`, `tests/renderer.test.cjs`, and `tests/live-replay.test.cjs`. They include non-astronomy UK/RU/PL/EN comparisons; explicit group aliases; locative/relative phrases; unresolved subjects; isolated anaphora; generic/direct-media bypass rejection; identity mismatch; co-subject Commons rejection for images and video; deduplication; preflight-before-TTS; unchanged duration tolerances; and 20-second visual-shot planning.

For a 20-second scene with verified alternate media, the shot planner produces three shots of 6.667 seconds. Without a verified alternative it records `same_entity_no_alternative`; it never fills the gap with a different topic.

## Reproduction

See `docs/VISUAL_RESOLVER_REVIEW.md` for installation, test, Docker and live preflight commands.
