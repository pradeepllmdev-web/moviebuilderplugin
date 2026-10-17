# Movie production samples and reusable character controls

This repository contains opt-in production code and isolated samples. Original Blender/Unreal repositories, downloaded character source files and existing films are preserved.

## Latest gaze test (October 16)

`environment_library/movie_jobs/1dc525ad9a1c419ea9b92188f4451075/movie.mp4` is the8-second **Look at Me - Partner Attention** test. Stationary lion/cat conversations can use `look_at: partner` in prompt plans; the adapter derives initial body facing and head offsets from their placements. The final close-up is verified in Unreal and the draft movie decoded. This is partner-facing head attention; independent pupil movement and blinking remain unfinished. See `environment_library/SCENE_PROMPTS.md`.

## Latest acting challenge

`environment_library/movie_jobs/6935db6d98c640d79b3f68d825cd7dce/movie.mp4` is the18-second **A Twig and a Brave Friend** draft. Four shots exercise a timed twig sound, smoothly held head reaction, dialogue/reassurance and walking together. `scene_attention.py` and `scene_director.py` add reusable, bounded head/sound cues to the prompt workflow. Blinking and exact eye contact remain unverified; see `environment_library/SCENE_PROMPTS.md`.

## Prompt movie workflow (October 15)

The latest workflow is available in 3dobjectnew -> Movie Studio. It plans short stories into editable Unreal shots using existing lion/cat rigs, saved environments, dialogue, cameras and conservative contact checks. Draft/final render controls assemble dialogue, an original procedural score and footsteps. The verified demonstration is `environment_library/movie_jobs/33e46a885f124dffaffb55f7040ce17c/movie.mp4` (12 seconds, three shots). Read `environment_library/SCENE_PROMPTS.md` for supported features and remaining animation/physics limitations; `implementation/prompt_movie` contains the main-app integration sources and installation backups.

## Earlier sample

The newest variation is `samples/the-last-lantern/the-last-lantern-performance.mp4`: a 19-second Blender sample with **three separately captured motion families**, not a single video driving every action. Its editable scene is `the-last-lantern-performance.blend`.

| Motion family | Reference | Applied channels |
| --- | --- | --- |
| Talking gestures | Kindel Media, Pexels 8550366 | Upper arms, forearms, wrists and restrained torso movement |
| Head attention | Gustavo Fring, Pexels 6290465 | Head turns, nods and tilt layered over conversation blocking |
| Facial expression | Tima Miroshnichenko, Pexels 4994154 | Blink/brow/smile timing and subtle gaze variation |

All are stock references under the [Pexels License](https://www.pexels.com/license/). Exact source/download URLs, authors and role selection are in `samples/the-last-lantern/performance/reference_bank.json`. Raw stock footage and its audio are not included in the movie. Reference authors are credited in the final three-second credit section.

`movie_production/capture_video.py` extracts each reference separately through MediaPipe Pose or Face Landmarker. Captures are stored as compact NPZ motion tracks, with small JSON tracking reports. `performance_tracks.py` enforces motion-type and tracking gates before selection. Facial capture never writes target jaw or lip-spread channels; the movie's generated dialogue retains its original lip sync. Snow and Jacob use different reference timing offsets rather than identical performances.

Capture tracking coverage was approximately 89.2% for the upper-body video and 100% for the two facial/head videos. The body reference has gaps of up to 0.8 seconds: those regions fade toward the existing listening clip. Blink transfer subtracts the source actor's narrow-eye baseline instead of treating every squint as a closed eyelid. Native body rotation spikes are limited to 120 degrees/second per control and quaternion signs remain continuous. This is cleaned, adapted capture, not an exact reconstruction of every original pose.

`performance-preservation.json` checks target jaw controls and planted roots/feet. `performance-continuity.json` checks every rendered-time hand sample; after cleanup its largest hand-position step was below 5 cm/frame. These are coarse safeguards, not guarantees of mesh collision-free contacts or perfect natural acting. Eighteen unit tests pass, including typed selection, failed-capture rejection and neutral-eye blink calibration. The newly captured performance has not been validated in Unreal.

`movie_production/motion_families.json` separates talking, head/face, walking, running, waving and sit/stand requirements. Only the three stationary families above are applied here. Lower-body motion and finger articulation are not inferred from these cropped/seated references. A previously labeled Talk_1 source was visually found to be stretching, and an initial facial candidate cropped the eyes; neither was used for the new facial performance. Rejected reference metadata is retained for review.

Reproduction after the attention variation:

```text
python samples/the-last-lantern/performance/download_bank.py
python movie_production/capture_video.py --bank samples/the-last-lantern/performance/reference_bank.json
blender --background --disable-autoexec --python samples/the-last-lantern/apply_performance.py
blender --background --disable-autoexec --python samples/the-last-lantern/clean_performance.py
blender --background --disable-autoexec --python samples/the-last-lantern/verify_body.py -- --performance
blender --background --disable-autoexec --python samples/the-last-lantern/verify_body_continuity.py -- --performance
blender --background --disable-autoexec --python samples/the-last-lantern/render_saved.py -- --performance
python samples/the-last-lantern/finish_movie.py --performance
```

Capture requires MediaPipe, OpenCV and SciPy in the local mocap environment, plus the official Face Landmarker model and the existing Pose Landmarker model. Dependencies and model paths are explicit in the scripts. Downloaded models and raw media are excluded from Git; no model geometry is printed or serialized into prompts.

The latest attention variation is `samples/the-last-lantern/the-last-lantern-attention.mp4`, with its editable `the-last-lantern-attention.blend`. It adds conversational head turns, held listening looks, brief path glances, eyes leading turns and discrete nods over the recorded body animation.

The previous Snow mapping addressed `Head`, whose constraints override direct rotation. The corrected face profile uses the active `FK-Head`. Jacob's yaw remains on local Y of `CTRL-HEAD`; nodding uses local Z with the calibrated opposite sign. Both profiles now allow up to 28° of yaw and 6° of nod rather than the earlier barely visible movement. The measured orientation changes in `attention-verification.json` come from evaluated deform head bones, not merely keyed input controls.

The attention variation passed sampled preservation checks in `attention-preservation.json`: jaw controls agree within floating-point precision, hand positions match the recorded-body version, and root/foot positions remain unchanged. Fourteen unit tests pass, including partner direction, held listening looks, transition easing and a single nod peak. Head calibration is engine-side control/deform metadata only; model geometry is never emitted.

`movie_production/attention.py` generates rig-independent attention commands from dialogue timing and partner side. Profiles translate them to native controls. Looks are deliberately kept as cinematic three-quarter turns so faces remain visible; this is not an exact world-space eye-target solver. The attention pass keys only gaze/head channels and keeps the existing jaw, expression and body channels. No downloaded mesh data is modified.

To rebuild this variation after the body pass:

```text
blender --background --disable-autoexec --python samples/the-last-lantern/apply_attention.py
blender --background --disable-autoexec --python samples/the-last-lantern/render_saved.py -- --attention
python samples/the-last-lantern/finish_movie.py --attention
```

`samples/the-last-lantern/the-last-lantern.mp4` is the completed 18-second sample: Snow and Jacob at a forest crossing, four dialogue shots, 16 seconds plus two seconds of credits. The editable scene is `samples/the-last-lantern/the-last-lantern.blend`. Video/audio decoding, jaw and blink animation, neutral jaw boundaries and four camera cuts passed verification. Five profile tests pass. Reports are saved beside the movie.

The sample uses Blender for rendering, locally installed Windows speech voices, the existing Blender plugin's heuristic audio/viseme analysis and an original procedural demo score. It demonstrates the reusable adapter rather than final cinematic acting, forced-aligned phonemes, independent tongue performance or photoreal environments. Jacob was separately imported and visually checked in Unreal; this two-character sample is rendered in Blender.

## Reusing the character animation

### Shared body clips — latest extension

The updated sample delivery is `samples/the-last-lantern/the-last-lantern-body.mp4`. Its scene copy is `the-last-lantern-body.blend`; the original sample remains available.

The body variation is complete: 18 seconds at 960×540 and 24 fps, including the original dialogue, score, captions and credits. It passed audio/video decoding checks. Equivalent quaternion signs are kept continuous when baking controls to avoid interpolation flips; the corrected sample's affected frames were rerendered. `body-verification.json`, `body-continuity.json` and `delivery-body-report.json` record the checks and their measured limits. The continuity check is a coarse hand-step check, not a guarantee of perfect acting or collision-free contact.

`movie_production/body.py` retargets the **existing human library's Talking and Listen recordings**, rather than generating unrelated arm waves. `motion_library.json` selects shared clips once. `catalog.json` declares each character's profiles and tested actions. `profiles/snow-body.json` and `profiles/jacob-body.json` map canonical torso/arm joints to native FK controls, rig switches and a reference bone for orientation. Recorded gesture strength is damped, transitions ease between talking and listening, root orientation is removed, and torso movement is limited to seven degrees.

The body pass leaves facial channels separate. On the reviewed nine frames, hand motion is present for both characters; root and foot positions match the original sample and jaw controls agree within floating-point precision. This checks sampled transforms, not mesh collision or every contact. Nine unit tests cover facial profiles, body profile anatomy and action capability gating.

The shared path is: **shot action → common clip → character body profile → native FK animation**, alongside **dialogue → common visemes → character face profile → native facial controls**. Bake the combined evaluated result before engine export. The two-character body update has not yet been checked in Unreal.

To add a biped, register its face/body profiles and calibrated IK/FK switches once. Declare only actions that pass a visual test. Walk/run/jump require lower-body mapping, root-motion scale, stride matching and foot/contact IK; this stationary adapter deliberately rejects them. A quadruped needs a separate anatomy-specific motion family. No single mapping makes every skeleton or anatomy compatible.

Rebuild this body variation after generating the base sample:

```text
blender --background --disable-autoexec --python samples/the-last-lantern/apply_body.py
blender --background --disable-autoexec --python samples/the-last-lantern/verify_body.py
blender --background --disable-autoexec --python samples/the-last-lantern/render_saved.py -- --body
python samples/the-last-lantern/finish_movie.py --body
```

Body controls are keyed every other frame and interpolated by Blender at the 24 fps render rate. Native body and facial evaluation, material conversion and Unreal validation remain opt-in; original plugin runners are unchanged.

`movie_production/characters.py` is the common control adapter. Profiles in `movie_production/profiles/` map semantic commands to native bones. Both supplied profiles support `jaw`, `blink`, `gaze`, `spread`, `smile`, `brow`, `head_yaw` and `head_nod`. The adapter supports native Euler/quaternion rotation, local translation and height-scaled world translation. A missing required control fails at binding, before animation is written. It does not change mesh topology or infer missing articulation.

To add another character:

1. Start with a properly rigged asset containing jaw, eyelid, eye and expression controls. Confirm its license.
2. Copy a JSON profile, replace bone names and calibrate axes/signs/ranges in a scene copy. Remove unsupported channels rather than pretending they exist.
3. Record necessary rig switches in `properties` (Snow uses FK arms). These are applied only after required controls/properties validate.
4. Bind `RigController(rig, load_profile(profile_path), actor_height_metres)` and call `controller.key(frame, semantic_commands)` for each frame. Use `speech_commands` to adapt the existing solver outputs.
5. Review neutral, jaw-open, blink-closed, smile, gaze and a short speech test. Test baked export and native engine playback before production use.

Control names and settings are configuration; speech logic is shared. Adding a new compatible rig does not require copying Snow/Jacob animation code. Raw image-generated meshes still require a facial rig, suitable mouth/eyelid topology and calibration. Native shape-key characters can continue using the existing plugin's shape-key adapter; this module is an additional bone-control route, not a replacement.

The existing plugin runners and production catalogs have not been switched to this adapter automatically. The sample imports it explicitly. This keeps legacy behavior unchanged while its integration is reviewed.

## Reproduction

Requires locally installed Blender, Python with NumPy/imageio-ffmpeg, the existing `blendplugin-next/scene_pipeline/facerig.py`, and downloaded Snow/Jacob assets in `.verification/character-evaluation`. Local paths are explicit in the sample scripts; edit them when moving machines. The generated `movie.json` stores shot text, voice choices, timing and camera selection.

Run Blender with auto-execution disabled:

```text
blender --background --disable-autoexec --python samples/the-last-lantern/build_movie.py -- --stills
blender --background --disable-autoexec --python samples/the-last-lantern/render_saved.py
python samples/the-last-lantern/finish_movie.py
python -m unittest discover -s tests -v
```

Speech WAV files are generated with installed Windows System.Speech voices, not downloaded or billed API calls. The sample builder reads the WAV recordings and uses the existing solver. Embedded downloaded asset scripts are never executed.

To regenerate dialogue on Windows, run `samples/the-last-lantern/generate_speech.ps1` before building the scene. To check saved scene animation, run `verify_animation.py` through Blender with auto-execution disabled. Downloaded assets and generated media are excluded from Git; their local files are retained for playback and editing.

## Free scripted character experiment

`samples/mpfb-character` creates Rowan with an isolated MPFB 2.0.18 checkout and CC0 graphics assets. The human template has 52 facial expression controls and uses the shared body retargeter, existing voice-driven speech commands and a new morph-target adapter in `movie_production/blendshapes.py`. The sample includes a six-second voiced audition, explicit face/body profiles and native plus GLB roundtrip verification. See `samples/mpfb-character/README.md` for reproduction and limits. This does not change the production plugins or approved catalog; Unreal playback is not yet verified.

## Asset credits

`samples/leo-anatomical` tests a new simple cartoon lion head with a hinged jaw, separate teeth/tongue/eyes, and wrapping eyelids. It preserves the earlier lion's biped body in a separate scene and includes native/GLB checks. This is a procedural facial-anatomy prototype, not an image-to-3D reconstruction or a finished hero character.

The earlier prepared upright lion is also exercised in `samples/lion-conversation`. It uses the same shared morph and body adapters as the human samples, with an explicit lion profile and fitted closure lids. Native/GLB motion and source-preservation checks are included; see that sample's README for asset-specific limitations. This new variant has not been verified in Unreal.

Snow Rig © Blender Foundation | studio.blender.org. CC BY. Source: https://studio.blender.org/characters/snow/v4/ .

Jacob by jupifox | jupifox.itch.io. CC BY 4.0. Source: https://jupifox.itch.io/jacob-game-ready-character .

Animation, poses, staging, lighting and export materials modified in scene copies. Asset credits appear in the delivery movie. Saved license evidence and source archives are under `.verification/character-evaluation`.
