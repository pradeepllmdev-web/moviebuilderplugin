# New Meshy lion: talking preview

The supplied Nano Banana image generated a new Meshy model and body rig (35 credits total). Original downloaded model and rig are preserved. No additional Meshy tasks were used for this preview.

`talking/lion-talking-audition.mp4` is an eight-second prototype using the existing whisper dialogue, audio-driven jaw opening, a complementary lip-seal shape, captured upper-body gestures, and a small head turn. Blender meshes are processed internally; no geometry arrays are emitted.

`prepare_talking.py` builds a separate mouth copy from `face-fit.blend`: splits the lip line, removes obstructing interior faces, fits recessed teeth/tongue/lining, and adds LipSeal from the unmixed basis. `build_talking.py` uses the shared speech/body modules. Anatomy is bound to the Head bone.

`talking/verification.json` checks source preservation, jaw activity and rest, upper-face shape protection, head turn, and hand motion. `talking/delivery.json` records complete MP4 decoding.

This is a prototype, not an approved facial asset. Mouth corners and lip transitions still need topology work. Eyes have no blink/gaze rig. Speech uses an audio-driven jaw approximation, not complete phoneme-specific lips or tongue. No Unreal verification has been performed. Previous prototypes are retained.

Updated preview: talking-blink/lion-talking-audition.mp4 adds calibrated closure lids with warm tan material (linear RGB .52,.35,.20), head binding, crease, and blinks at frames 28/79/145. Ten pupil/eye coverage rays pass. Closed/open stills visually reviewed. Only affected blink intervals rerendered, with other frames copied from the prior version. Independent gaze remains unavailable; eyelid overlays remain a prototype fit.
