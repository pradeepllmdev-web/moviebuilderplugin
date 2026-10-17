# Original-lion facial anatomy repair

This experiment preserves the earlier `Lion_Realistic` character's head silhouette, muzzle, nose, mane, body and texture assets. It does not substitute the procedural Leo head or generate another model.

The source scene is read-only. The script appends a scene copy, transfers lower-face skin influence to a new jaw hinge, fits a concave mouth lining, gums, small separate upper/lower teeth and a tongue, and adds small independent eyeballs plus spherical eyelids at the calibrated original eye locations.

## Lower-lip repair

The old mouth contains inner faces that stretch into triangular spikes under a hinged jaw. A small calibrated set of lower-lip faces is separated into a new mesh, preserving its original vertex positions, UV coordinates and material assignments. That patch follows the jaw uniformly instead of bridging fixed and moving parts. The original model's source file is never saved.

`neutral_surface_max_change_m` is zero for the original base vertex positions. That does not mean the complete rendered image is identical: fitted eyes/lids and mouth interiors are additions, and the original expression controls still animate the surface. Visual likeness review remains necessary.

## Outputs

- `neutral.png`, `speech.png`, `blink.png`: fit-review close-ups.
- `lion-talking.blend`: editable repaired scene.
- `lion-animated.glb`: character with native jaw, eye/tongue controls and animated facial shapes.
- `lion-talking-audition.mp4`: eight-second, 640-square voiced audition.
- `application.json`: original source hash, anatomy-fitting summary and scope.
- `verification.json`: native/GLB motion checks, facial timing and source-preservation result.

## Reproduce

```text
blender --background --disable-autoexec --python samples/lion-conversation/build.py -- --repair --output samples/lion-preserved
blender --background --disable-autoexec --python samples/lion-conversation/verify_export.py -- --directory samples/lion-preserved
blender --background --disable-autoexec --python samples/lion-conversation/render.py -- --directory samples/lion-preserved
python samples/lion-conversation/finish.py --directory samples/lion-preserved
python -m unittest discover -s tests -q
```

The same existing speech solver, captured body gestures and listening clip are reused. Tongue lift is a simple jaw-linked correction, not full phoneme-specific tongue articulation. Eye/lid fitting, lip contacts and jaw contours still require artistic review; this is an asset-specific repair prototype, not a universal animal facial rigger or a finished film character. Actual Unreal playback is not verified.

All mesh/weight/UV operations happen inside Blender. No geometry arrays are printed into the conversation. There are no paid API calls or global Blender installation changes.
