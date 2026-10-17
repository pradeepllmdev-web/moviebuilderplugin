# Rowan prompt character

Latest repaired walking audition: `d451bd370a6b464f918527127601d52f`. The prompt builder now preserves MPFB macro shape values when resetting facial expression channels. Clearing those values had distorted the neutral body relative to eyes/hair/teeth. The repaired Unreal viewport shows the hair and face aligned again. Mesh joining also uses a temporary vertex identity attribute rather than assuming object append order; `tests/blender_shape_join_check.py` validates reordered transformed meshes. Earlier demos are retained and should be treated as pre-repair experiments.

The scene planner and character selector accept `rowan`, using the existing clothed MPFB human. The builder adds native ARKit blink and restrained eye-direction tracks, keeps speech jaw animation, cleans MPFB export helpers on a copy, and converts the eye texture alpha to a masked Unreal material. Existing lion/cat blink behavior remains disabled.

Saved demonstrations:
- `947ffda69c3f4f55b1f14924167eba3b`: Rowan and Leo - Morning Greeting, six seconds, partner head attention and listener beats.
- `cee923aad52047d198eaa6fd43580b5e`: Rowan - Walk and Talk, six seconds, full-body camera followed by a talking beat.

Refresh the studio website and open Existing scenes. Both levels and sequences were saved and the production worker confirmed completion. The final automated viewport capture timed out, so continuous playback of these new scenes still needs visual review. The earlier isolated Rowan audition demonstrated eyelid closure and visible irises in Unreal.

Eye gaze currently uses bounded procedural directions, not position-based pupil tracking. Walking has conservative route/ground checks, not physical contact simulation. Speech remains amplitude-driven jaw motion; a complete phoneme facial performance is further work. No paid service is called.
