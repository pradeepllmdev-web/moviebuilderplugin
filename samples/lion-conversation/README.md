# Earlier detailed lion: shared talking-character flow

This opt-in experiment reuses the earlier prepared `Lion_Realistic` v4 from the copied plugin's `verification/lion-detailed/authored_probe.blend`. It is an upright biped character with a Mixamo-style skeleton, not a quadruped. No new image or paid model generation was required.

The original scene is read-only. `application.json` records its SHA-256 and `verification.json` checks that it remains unchanged. Model geometry is processed only inside Blender; reports contain control names, counts, motion ranges and hashes.

## Changes

- The same `BlendshapeController` used for MPFB humans maps speech/expression commands to the existing lion jaw, rounded/wide mouth, lip closure, pressing, smile and brow shapes.
- Shared face commands now optionally include lip closure and pressing. Existing human profiles ignore those channels when no corresponding morph exists.
- The original approximate blink morphs did not hide the pupils. A calibrated Blender-only helper creates fitted lid overlays and crease strips with independent left/right closure morphs, bound to the native head. Original blink morphs are held at zero.
- The same captured body sampler and `BodyRetargeter` provide restrained talking/listening gestures. Feet/root remain stationary; native head rotation adds gentle turns and nods.
- The existing line “Tonight, I will try something stronger. A whisper.” and its local voice recording are reused.

This is an asset-specific stylized face setup, not a universal animal rigger. The lid surfaces are a practical closure approximation and need further art refinement for hero close-ups. There is no independent eyeball gaze or articulated tongue. Human facial templates are not fitted onto the lion's muzzle.

## Reproduce

```text
blender --background --disable-autoexec --python samples/lion-conversation/build.py
blender --background --disable-autoexec --python samples/lion-conversation/verify_export.py
blender --background --disable-autoexec --python samples/lion-conversation/render.py
python samples/lion-conversation/finish.py
python -m unittest discover -s tests -q
```

The local copied-plugin path, prepared lion and captured performance bank must exist. Encoder Python needs `imageio_ffmpeg`.

The builder appends only the lion rig and its mesh objects to a fresh scene. It initializes sequencer state before frame evaluation to avoid a Blender 5.2 crash associated with sequencer dependencies in the older scene.

## Outputs and verification

`lion-talking.blend` is editable. `lion-animated.glb` contains the rig and animated mouth/lids/body. `lion-talking-audition.mp4` is the eight-second voiced preview. Face/body mappings are explicit JSON files, so the shared timing/animation code can be reused without claiming that these facial deformations fit other animal meshes.

All 192 frames are checked natively and after GLB reimport: active jaw with neutral beginning/end, full eyelid-control values, hand gestures, head movement, fixed root/feet and matching facial timing. Closed-eye native and GLB renders are reviewed separately; coefficient checks alone do not establish visual closure. The source preservation hash also passes. Actual Unreal playback of this new variant is not verified.

The character remains outside the approved production catalog. Existing human samples, original lion assets and older films are preserved.
