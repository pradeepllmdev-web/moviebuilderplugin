# Performance engine: cast variety, declarative scenes, automatic camera, whole films

A second way to build films, next to the 28 bespoke set pieces: **data in, film out.** A scene is a plain dict (location, cast, props, a list of beats); a film is a cast registry plus about twenty such scenes. Nothing in a film file touches Blender.

```
films/<film>.py  (FILM = cast records + scenes written with perf_dsl)
  -> cast_registry   characters on the single lion rig: species proportions, tint, parts, accessories, posture/gait, voice
  -> perf_plan       spec -> per-frame positions, clips, speech, IK hand targets, prop tracks; numeric audits (no Blender)
  -> perf_camera     automatic coverage: establishing wide, over-the-shoulder / single / two-shot, tracking, inserts, 180 degree rule
  -> perf_locations  small low-poly location specs (13 presets, 36 object kinds, props that can be carried or pushed)
  -> perf_scene      the Blender player (one process per scene): characters, NLA clips, gaze, lip sync, IK, props, cameras, sound, audits
  -> perf_movie      builds a film scene after scene, contact sheets, master, report
```

## Run it

```
cd environment_library
python build_walk_clips.py -- scenes/ship_assets          # once: walk, strut, shuffle, bounce, sneak, stomp, brisk clips (blender -b --python build_walk_clips.py -- <ship_assets>)
python perf_movie.py films/clockwork_festival.py out/clockwork --plan-only     # seconds: compile + audit every scene, timing table
python perf_movie.py films/clockwork_festival.py out/clockwork                  # build every scene in Blender (about 7 s each), sheets, master, report.md
python perf_movie.py films/ember_road.py out/ember --scenes 3,4 --force         # rebuild some scenes
python contact_sheet.py out/ember/scene_09_storm_ruins.blend sheet.png 12 3 480 # review frames of one scene (Workbench stills, no video)
python -m unittest discover -s ../tests                                          # pure-logic tests
```
(`build_walk_clips.py` is run with Blender: `blender -b --python build_walk_clips.py -- <ship_assets_dir>`; the clips are `.blend` files and therefore not in git, `gait_report.json` is.)

## Characters (`cast_registry.py`, `cast_builder.py`)
One rig, many characters. A record: `dict(id, name, species, height, width, depth, tint, parts, accessories, posture, pace, voice_pitch, description)`. 12 species presets (lion, bear, fox, rabbit, ox, owl, wolf, mouse, heron, badger, boar, cat, elder) set proportions
(`scale` = width, depth, height relative to the 1.71 m lion, set on the unscaled root empty), tint and body parts (round/pointed/long/side/disc/tuft ears, horns, tusks, ruff, tail tuft, beak); 22 accessories (hats, crown, helmet, glasses, eye patch, flower, scarf, bow tie, cape, backpack, apron,
medals, belt, satchel, sword, staff, cane, lantern, banner) are made of primitives and parented to head, neck, spine, hip, hand and tail bones. Posture picks the gait (proud: strut, tired: shuffle, jaunty: bounce, tense: sneak, angry: stomp, hurried: brisk); `pace` scales cadence;
the voice pitch replaces the hash pitch of the synthesised voice. `Registry.save/load/merge`, `export_story_records()` (name + description + structured look, for story tools such as the sibling `3dobjectnew` repo), `from_series_character(record)` (guesses a look from the words of a series
character record: species, accessories, posture, colour, size), `distinct_report()` (twin check). Limits: faces are the lion's; variety is silhouette, colour, parts, accessories, gait and voice.

## Gaits (`gaits.py`, `build_walk_clips.py`)
The library had a run cycle and a very slow climb, so seven walking clips are generated: IK feet on stance lines that move back at exactly the gait's ground speed, hips bob and sway, pelvis against chest, arm swing, lean, baked to NLA actions. The planner derives each walk's speed from the gait table,
the character's stride (its depth scale: the walking axis is local y) and pace, and the clip's play scale from that, so the planted foot matches the ground (measured by the Blender audit: 0.0-0.3 m/s). The `run` clip has intrinsic foot slide (about 1.3 m/s whatever the speed) and is excluded from the slip audit.

## Scene spec and beats (`perf_plan.py`, shorthand in `perf_dsl.py`)
`go` (walk/run to a point, character, prop, marker, object or seat; routed around solids and standing characters, corners rounded, goals moved out of solids, parallel walkers spread and, if their paths collide, the later one is delayed), `turn`, `say` (timed from syllables, lip sync, eye lines, listener turns and reacts, optional gesture),
`act` (any library clip: wave, nod, shrug, laugh, push, kick, bow, startle, think, argue, fall, getup, kneel, ...), `look`, `emote`, `wait`, `take` / `put` / `give` / `push` (IK hands reach the prop, it follows the hands, hands and prop are audited), `sit` / `stand` (seat ids come from the location: `bench_a.0`, `stool_b.0`, `throne.0`),
`sfx`, `cam` hints. Steps run one after another; a list inside a step runs at the same time. Spec mistakes raise `SpecError` with the step and the reason (unknown character, two lines at once, acting while seated or on the ground, taking something out of reach or too heavy, a taken seat ...).
Plan audits: speech overlap, collisions, walking into solids, bounds, turn rates, gait speeds, seated speakers facing away, props under the floor, scene length.

## Camera (`perf_camera.py`)
Establishing wide, then per step: dialogue coverage (over-the-shoulder with lateral offset sized to the listener so the speaker shows past a bear, a three-quarter single on the listener, a two-shot every third line, soliloquy = medium on the speaker), tracking shots beside walkers (high follow for long walks), an insert in front of the prop for take/put/give/push, a medium for
big acts, a wide hold at the end. Sides and distances are scored (uninvolved characters off the line of sight, nobody inside the lens, camera not in a solid or off the map); dialogue keeps one side per pair; shots are 1.3-9 s; near-identical consecutive framings are varied; inside a room the camera is clamped inside the walls. In Blender the existing `scene_base.cameras` adds depth of field, a light sway and clears the view of solids.

## Voices (`perf_voices.py`)
Real speech from Piper neural TTS (`pip install piper-tts`, models in `voices/`, fetched by `python perf_voices.py download`, about 400 MB, git-ignored). `perf_voices.catalogue` measures the pitch of 164 candidate voices once (`voices/catalogue.json`); `assign(registry)` gives every character the free voice whose pitch is closest to its registry pitch (shift by resampling for the rest), personality sets the speaking rate and the mood the delivery.
Lines are synthesised in parallel and cached as wav (`voices/cache/`, keyed by voice, text, mood); the planner uses the recorded length, the Blender player reads the cache (Blender itself never needs Piper) and the mouth follows the energy envelope of the real audio. Without Piper the formant voices are used.

## Score (`perf_score.py`, `perf_midi.py`)
Each film has a THEME (root, mode, tempo, main motif, instrument palette, character motifs). The composer writes MIDI from the compiled plan: the same motif varied in every scene, character motifs on their first line, the lead instrument chosen by the place (accordion in markets, flute in clearings, horn in ruins, vibraphone in caves), intensity from the action (running, falls, startles, thunder), a soft pad under speech, hits on crashes and thunder, a rising run for cheers, a resolving last bar.
It is rendered by FluidSynth with the GeneralUser GS SoundFont (`python perf_midi.py download`, into `music_tools/`, git-ignored) and cached. Without them the old generative score plays.

## Story legibility
Each scene has an `intent` line (one sentence of what happens and why it matters) shown on a title card before the scene; the film has a logline card and an end card; every spoken line is a coloured subtitle ("Name: line") in the master (`perf_movie` writes plan.json, `assemble_movie.py` makes the strips). Watch it with `python perf_watch.py out/<film>` (sequencer preview, sound, subtitles).

## Life
Background characters (`extras=crowd(n, area, focus, seed)` in a scene): deterministic looks and places that avoid solids and the cast, turned to the focus, breathing out of step; the cast is routed around them. Gestures follow the words and mood (wave on greetings, argue on refusals, nod on agreement, never the same clip twice running); glances and brow flashes keep the faces alive; a grounding pass lifts the root per frame for sit/fall/getup/kneel/crawl/jump so the body rests on the floor; the camera pushes in slowly on dialogue and drifts round wides.

## Sound (`perf_audio.py`)
Voices per speaker (synthesised, pitch from the registry; real recordings via `VOICE_DIR` still override), 10 ambience beds, 8 generative score moods, footsteps from the gait cycle, 13 effects (knock, door, thud, clang, bell, gong, crash, scrape, splash, thunder, chime, clap).

## Audits printed per scene (Blender side)
Eye lines (speaker 34, addressed listener 40 degrees), lip-sync keys per syllable, planted-foot slip (limit 0.35 m/s, built gaits), hand-to-target distance (0.22 m), speaker framing in every dialogue cut (head inside the frame at the middle of the cut; insert cuts check the prop; tracking cuts the group), camera inside or behind solids, persistence (nothing hidden, ever).
