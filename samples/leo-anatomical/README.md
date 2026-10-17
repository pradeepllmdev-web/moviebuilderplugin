# Leo: a talking-animal anatomy prototype

This is a new, simple cartoon lion head built in Blender using the earlier lion screenshot as visual reference. It is a procedural anatomy prototype, **not** a new Meshy model or faithful image reconstruction. The earlier character's biped body and animation are reused in a separate scene; its original scene remains unchanged.

## Anatomy

- Solid upper head with an actual recessed mouth opening.
- Separate jaw bone; lower jaw, gums and teeth follow its hinge.
- Separate tongue parented to the jaw. It follows the jaw but has no phoneme-specific tongue articulation yet.
- Separate upper/lower ivory teeth and colored oral lining, replacing the flat dark mouth surface.
- Separate eyeballs, irises, pupils and highlights, with independent eye bones.
- Upper/lower spherical eyelid caps wrap around the eyes and meet on full blink.
- Soft muzzle shapes provide spreading, rounding, smiling and lip closure.
- New mane and scarf cover the join to the preserved body. The old head is masked only on the scene copy.

The design is intentionally simple and stylized. It is not a finished hero asset, and the relaxed mouth retains a small opening. Materials, mane silhouette, teeth shape, lip contacts and facial posing still need art review.

## Reused animation

The same `BodyRetargeter`, captured talking reference, listening clip and `speech_commands` drive this character. A bone-driven jaw is combined with the existing `BlendshapeController` for eyelids and muzzle controls. Jaw-morph validation remains enabled by default for previous characters; a profile must explicitly opt out when a bone drives the jaw.

## Reproduce

```text
blender --background --disable-autoexec --python samples/leo-anatomical/build.py
blender --background --disable-autoexec --python samples/leo-anatomical/verify.py
blender --background --disable-autoexec --python samples/leo-anatomical/render.py
python samples/leo-anatomical/finish.py
python -m unittest discover -s tests -q
```

Source/captured-reference paths point to the existing copied Blender plugin and previous local sample assets. No paid API calls or global Blender installation changes are involved.

## Outputs

`neutral.png`, `open.png`, `blink.png`: anatomical close-up checks.

`leo-talking.blend`: editable scene with eight seconds of speech and gestures.

`leo-animated.glb`: character/animation export; old-head mask is baked before export.

`leo-talking-audition.mp4`: eight-second, 640-square voiced audition using the earlier lion's existing dialogue fixture.

`verification.json`: native/GLB jaw and blink timing, fixed foot check, tongue hierarchy, separate tooth objects and source-preservation hash. These checks do not certify artistic realism or speech intelligibility. Actual Unreal playback is not verified.

Geometry stays inside Blender. Reports contain only counts, hierarchy/animation results and hashes.
