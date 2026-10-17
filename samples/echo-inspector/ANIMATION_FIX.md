# Echo Inspector animation correction

Initial failure: the new anthropomorphic character copies had no supported facial naming profile, so only a small incidental expression curve varied. The cinematic planner also assigned listen for the entire shot, producing a rigid pose. Imported bone-track/curve counts alone did not certify visible animation.

Reusable fixes:
- blendplugin-next/scene_pipeline/facerig.py: custom uppercase JawOpen/JawClose profiles, audio-driven jaw, inverse cat closure, existing blink and expression aliases.
- realistic_rig.py: optional per-character motion_defaults overrides.
- catalog.json: DemoLeo/DemoAmber use Idle_3 for listening, Talking for speech.
- 3dobjectnew/server/studio_plans.py: cinematic segments now alternate talking/listening from each dialogue line, rather than staying in listen throughout.
- export_performance.py + performance_motion_checks.py: reject custom-rig dialogue export when jaw samples are effectively static.

Tests: jaw-open and inverse jaw-close cases; speaker/partner timeline switching; static-dialogue rejection, moving dialogue acceptance and silent actor acceptance. Six focused checks pass.

The movie was rebuilt and reassembled through Movie Builder as render26 of movie36. Full decoding/audio/duration checks passed. Published /demos/EchoInspector/the-echo-inspector-v2.mp4 to avoid cached older video.

Actual Unreal Sequencer playback was verified separately over192frames per shot. Jaw and blink values change; first-shot hands travel17.6cm/22.0cm. Morph-target metadata flags are enabled. Summary files live-motion-check*.json contain only compact ranges, not geometry. Earlier screenshots were not sufficient proof; the corrected check samples evaluated playback.

Existing imported character materials were restored on only this movie's copies and lighting was softened. Automatic material transfer and more natural acting remain areas for refinement. No claim of film-quality acting.


## v3: rapid shaking correction

Default motion choices are no longer treated as explicit timed combat clips. Normal loop/transition handling is preserved; the two demo characters use75% conversation playback speed. Adjacent same-state dialogue segments merge instead of restarting the listening clip unnecessarily.

Opt-in calm_conversation.py samples evaluated upper-body poses, applies quaternion smoothing, reduces gesture amplitude and limits local angular steps. Lower-body NLA/contact animation remains intact. Custom jaw amplitude uses an asymmetric attack/release filter and a bounded per-frame change. These calming settings are enabled only for DemoLeo/DemoAmber, not all characters.

Source measurements: first-shot peak arm frame changes6.22→2.42degrees; head peaks3.86→1.88 and3.71→1.25degrees. Across both shots jaw peak changes0.48–0.53→0.144 per frame. Seven focused checks pass. Final16-second v3 fully decoded with audio, stored as MovieRender27 in movie36. Published a new video URL and updated site label to avoid cached v2.

This reduces abruptness; natural acting quality still needs visual judgement and refinement. No claim that numerical smoothness alone guarantees realistic performance.
