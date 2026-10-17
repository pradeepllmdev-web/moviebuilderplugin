# Lion motion diagnostic reel

Four separate spoken tests: standing, walking, running, and a circular race run. The model is a copy of the latest warm-eyelid lion. Existing files, prior videos, and downloaded source GLBs are preserved.

Voice lines use the existing OpenAI TTS integration (fable). Audio duration is measured from actual PCM bytes because the streamed WAV headers contain an unspecified length. Motion uses the existing recorded Talking, Mixamo_Walking, and Mixamo_Running actions, retargeted with the original Blender plugin's rest-space adapter. This sample does not substitute the stationary gesture adapter for gait.

Bone and skin group names are normalized on this copy. Timed speech, fitted closure lids, and a small brow/head accent are layered on the recorded full-body motion. Straight motion is calibrated from stride speed; circular travel has tangent heading and a marked track. A low-ankle contact correction reduces stance sliding and retains flight phases. Following cameras keep the character in frame.

Rebuild each section with Blender: build.py -- standing|walking|running|circle. For movement sections run plant.py once, then camera.py. Verify with verify.py; render with render.py. Python finish.py encodes individual MP4s and a labelled combined reel. All mesh data stays inside Blender; reports contain only motion diagnostics.

This is an animation diagnostic, not proof the model is perfect. Foot locking uses ankle-height heuristics, not sole/toe contact geometry. Toe rolling, turn banking, exact lap closure, material seams, mouth corners and lip accuracy need review. Eyelids are fitted overlays; there is no independent gaze or full expression rig. No Unreal verification or automatic support for arbitrary new characters is claimed.
