# Box delivery audition

The lion supports `box_pickup`, `box_back`, `turn` (walking arc while holding), `box_carry`, `box_hold`, `box_bump` and `box_setdown`. The box (36 × 26 × 24cm) and its hold come from the lion's `box` profile in `character_profiles.py`, measured on the rig: shoulders 112cm, arm reach ~48cm, belly front 39–42.5cm, chin/mane underside ~107cm. It is held 59cm ahead at 85cm, below the chin and clear of the belly, gripped on its side walls. Pickup and set-down stands are 70cm high. Other characters, running, arbitrary props and ground pickup need their own calibration.

The pickup stand is straight ahead, so a carry must first step back (`box_back`, 20–60cm, a reversed walk on its own strip) and make a walking turn before carrying. `box_timeline.py` owns the root path (same trapezoid speed profile as the animation clips, stopping only at standstills and reversals) and rejects any plan whose lower-body footprint crosses a stand. The movie simulates the whole box path up front, so every stand exists from the first shot.

A shared scalar trajectory drives the Blender wrist targets and an independent Unreal prop that turns with the carrier. While the hands are on the box, spine, neck and head forward tilt are capped (`posture_pitch_limits_deg`), because some idle variants hunch and nod the snout into the box. Box shots use a heading-relative side camera; `box_camera.py` picks the side where the box never covers the face (`box-camera-check.json`).

Checks per shot: `box-contact-check.json` (wrist IK error, posture caps), `box-clearance-check.json` (deepest skinned body vertex inside the box, hands/forearms excluded, limit 2.5cm, plus stand clearance and per-action posture), `motion-safety.json` (now with the frame of the largest joint step), and foot drift in `build-check.json`. Fingers are not wrapped around the box; the bump/recoil is keyed, not simulated.

Existing animal mouth-round, mouth-wide and smile controls receive restrained speech/expression keys where available. Broken/unverified animal blink morphs remain disabled. No source geometry is modified and no model buffers are printed.

Example prompt: “Leo picks up a box from a waist-high stand, steps back, turns right and carries the box slowly 120cm, pauses, gently bumps its front edge against a small stop and recoils, then sets the box down on a nearby stand. End with ‘There. Safe and sound.’ Keep the same box across shots. Use morning forest, full movement views and soft_portrait lighting.”

Use **Build Unreal preview first**, inspect the editable master, then render. `test_box_movie.py` exercises the public movie API; the studio server must be restarted after code changes because it keeps modules loaded. Unique job folders preserve existing movies.

## Fast iteration

`quick_review.py` is the edit → check → look loop. Each run prints every pass/fail number on a few lines and saves one contact sheet (`quick_review/<run>/sheet.png`):

- `python quick_review.py shot 2` (~20 s): Blender-only build of one shot, with box state, position and heading chained from earlier shots, plus a side-view sheet with a box proxy. Use this for body, hand and posture changes.
- `python quick_review.py movie` (~2 min): full Unreal preview through the studio server, plus Unreal screenshots at the start, middle and end of every shot. Use this for props, cameras and lighting.
- `python quick_review.py frames <movie_id> 60,270` (~10 s): re-capture frames of an existing movie without rebuilding.

Restart `studio_server.py` after code changes before using `movie`; `shot` always runs the current code.
