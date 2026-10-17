# Prompt-driven movie production

Main application: http://127.0.0.1:5173/ -> Movie Studio.
Local standalone studio: http://127.0.0.1:8521/#scene-create/movie.

1. Choose Short movie with shots or Single scene.
2. Optionally choose an existing environment. The source level is copied, never used as the writable production level.
3. Describe the story/actions; quote short dialogue. Select Plan and review the JSON shot/action plan and unsupported requests.
4. Build editable scenes. Each shot has its own immutable performance package, level and Performance sequence. Open any shot in Unreal and play Sequencer without rendering a video.
5. In Saved scenes & movies, select Render & assemble preview. Draft is 640x360, final is 1920x1080. Final was not exercised in this implementation test. Previously rendered versions are retained by job ID on subsequent renders.

## Implemented

- 3dobjectnew main-app Movie Studio tab and additive FastAPI proxy. Existing movie/database workflows remain available; these jobs currently live in the local production service's scene_jobs/movie_jobs stores rather than being inserted into the legacy movie database.
- Lion and cat profiles. Cat uses the installed humanoid-compatible DemoAmber library and inverse JawClose mapping; lion uses the corrected working rig and JawOpen. Original character assets are not modified. Source model vertices are never returned or sent to the AI.
- One or two actors, equal-duration timelines, short generated local SAPI speech, smoothed mouth animation. Idle/talk/walk/run/circle/dance and isolated small rock-gap jump.
- Story planner creates 2-6 shots, total <=90 seconds. Each shot <=40 seconds, <=8 action segments. Wide, medium, close and reaction framing. Close-ups focus on the speaker when focus is omitted. Actor root positions carry across cuts in the same environment.
- Existing environment catalogue selector, copied levels, ground trace, slope/step checks and capsule path sweeps. These reject obstructed paths; they do not autonomously find a new navigation route.
- Corrected inherited rig constraints/tails, per-span stationary foot locking, existing locomotion ramp timing, evaluated sole grounding. Actor routes are checked for finite coordinates, matching timelines, large root jumps, stage bounds and <90cm actor separation.
- Editable Unreal sequences, verified script completion reports, dirty-editor guard, unique output directories and saved-scene reopen buttons.
- Sequential Unreal rendering and local assembly with exact dialogue placement, an original procedural score with speech ducking, procedural footsteps and a full decode check. No new asset purchases or Meshy calls.

## Boundaries

These are stylized prototypes. Forest/mountain default sets remain procedural. Blinking is disabled because an imported blink morph deformed the body in earlier tests. Finger grip, driving, climbing, complex contact interactions, realistic impacts, arbitrary new characters and image-to-model generation are not generalized here. Unsupported actions must be reported before building. Facial acting, humanlike gaze, detailed set dressing and final cinematic quality still need visual review. Contact sweeps are conservative checks, not rigid-body simulation or complete mesh collision certification.

Jump scenes allow idle/talking before/after, not other locomotion; only one actor. Gap20-60cm. Moving shots require full-body framing. Actors must remain in the cleared filming area. Dialogue longer than its assigned action duration fails with an actionable error rather than being truncated.

## Code ownership

- scene_prompt.py / character_profiles.py: data-only scene contract, bounded validation and installed asset profiles.
- movie_prompt.py: story-to-shots planning, continuity and sequential scene jobs.
- scene_prompt_worker.py: background orchestration, immutable output directories, Blender/export/import adapters, verified setup completion.
- build_prompt_scene_blender.py / merge_prompt_scene_blender.py: individual character performance and multi-character package assembly.
- scene_contacts.py / setup_prompt_scene_unreal.py: conservative path checks, ground traces, camera, materials and saving only the generated production copy.
- movie_render.py: review-first render dispatch, dialogue/music/effects mixing, versioned preview assembly and decode check.
- studio_server.py: local APIs and 8521 UI.
- implementation/prompt_movie: staged 3dobjectnew API/component and backed-up minimal installation script. Applied to server/main.py and client/src/App.tsx, with a new server/movie_studio_api.py and client/src/components/MovieStudio.tsx.

## Validation

Morning Forest Mystery: 12 seconds, 3 shots, lion and cat, dialogue, cat close-up and walking together. Generated/planned and built through the 3dobjectnew proxy, rendered 640x360, mixed, decoded and loaded in the main app video player with duration12 and no playback error. Movie ID33e46a885f124dffaffb55f7040ce17c. A separate 3-second scene successfully copied saved environment PromptSet_f9144e11985c and passed ground/contact checks.

Twenty targeted scene/route/movie validation tests pass. The 3dobjectnew TypeScript build/type-check passes. The cat stationary test's local foot drift changed from1.7cm to0cm; this does not certify every walk or visual contact.


## Reaction/attention challenge

A Twig and a Brave Friend (movie6935db6d98c640d79b3f68d825cd7dce) is an18-second, four-shot draft: walk/stop at a twig snap, cat reaction, lion reassurance, then walking together. The twig event is at2.25 seconds in shot1. Rendered preview and decode check passed. Source body/face rigs are reused; no model geometry is emitted.

Each segment now accepts look_yaw_deg (-35..35), look_pitch_deg (-8..8) and emotion (neutral/alert/curious/reassuring). scene_attention.py smoothly blends head angles over0.6 seconds; reassuring adds one restrained nod. This is head attention, not a calibrated eye-target solver or a complete emotion rig. The layer edits only baked head rotation and preserves the body/root/jaw channels. Blink remains disabled.

Scene events accept {type:twig_snap,time:seconds}, mixed once at the exact shot-local time. The general planner is checked for expressly requested head turns/snap events. If omitted, scene_director.py requests a compact bounded cue pass without changing dialogue, durations, cast or movement. Invalid or still-missing cues fail visibly; arbitrary AI code is never executed. Plans remain reviewable before building.


## Position-based partner attention (October16)

Stationary paired idle/talk segments accept look_at:"partner". scene_gaze.py uses both actor placements and approximate eye-height profiles to set an initial body heading plus a bounded head turn. Explicit actor facing_yaw_deg can override initial orientation. Walking/running with semantic partner gaze is rejected; manual glances remain supported. Partner attention starts already oriented at a cut, avoiding a repeated turn from neutral. A Blender-to-Unreal handedness correction is applied to these head offsets. Partner-focused close-ups choose the front side of the speaking character.

Look at Me - Partner Attention is an8-second, two-shot test (movie1dc525ad9a1c419ea9b92188f4451075). In the checked wide-shot frame, imported head-front control headings differ from the partner direction by about4.1deg (lion) and3.4deg (cat). Imported head tracks change70deg between the two orientation-calibration variants. These are horizontal control-direction checks, not certification of independent pupil-level eye contact. Blink morphs remain disabled. The first calibration build is preserved with a calibration title.

The local bridge URL is configurable through MOVIE_UNREAL_URL or the ignored local_settings.json; default remains8520. On October16 the existing editor was on8500, so the local override was used instead of launching another editor.

The final vertical mapping also converts partner pitch into Blender's convention, so positive target elevation looks up rather than down. Calibration movies are retained on disk and hidden from the normal saved-movie list; completed movies are ordered newest first. Explicit body headings requiring excessive head turns are rejected. Semantic partner cues do not require the AI to guess numerical angles. Exact pupil movement and blink morph repair remain separate work.
