# Rowan: free, scripted human character audition

This experiment uses MPFB 2.0.18 in an isolated Blender process. It creates a new, fully clothed adult human from a standard template, with eyes, eyebrows, eyelashes, hair, teeth and tongue. It does **not** reconstruct the earlier Mira reference image or attach a facial rig to the Meshy model.

No API credentials, subscription, paid generation or global Blender add-on installation is needed. The pinned source checkout, asset packs, cache and logs are under `.verification/mpfb`. Existing characters, plugins and movies remain unchanged.

## Reproduce

Run with a Python environment providing `imageio_ffmpeg`, and Blender 5.2:

```text
python samples/mpfb-character/download_assets.py
blender --background --disable-autoexec --python samples/mpfb-character/build.py
blender --background --disable-autoexec --python samples/mpfb-character/verify_export.py
blender --background --disable-autoexec --python samples/mpfb-character/render.py
python samples/mpfb-character/finish.py
python -m unittest discover -s tests -q
```

This sample reuses the locally available captured reference bank, listening action and dialogue fixture from `samples/the-last-lantern`, and the copied Blender plugin's `facerig` speech solver. The scripts currently reference that copied plugin's existing local path.

## Reused animation flow

- `BodyRetargeter`: the existing stationary talking/listening motion adapter, calibrated to MPFB's Mixamo skeleton.
- `speech_commands`: existing heuristic voice-driven mouth commands; not forced phoneme alignment.
- `BlendshapeController`: new reusable adapter maps semantic facial commands to named morph targets on the body and corresponding eyes/mouth/hair assets.
- Separate captured expression reference supplies brow, eyelid and gaze variation; a deliberate full blink tests eyelid closure.
- Head turns use the generated native head bone. Feet and root are held stationary.

`body-profile.json` and `face-profile.json` store explicit mappings. `capabilities.json` records counts and supported scope. `verification.json` records actual native and exported motion checks, without printing geometry arrays.

## Export findings

MPFB's mask/helper cleanup rebuilds facial shape-key data, so the export script explicitly restores the facial animation actions and slots after cleanup. Blender's scene export also defaults to splitting object animations; this experiment disables that setting to keep the body's animation and facial tracks in one playable clip. The GLB is reimported and checked across all 144 frames for mouth opening, left/right eyelid closure, brows, hand motion and head turns.

`rowan.blend` is the editable source. `rowan-animated.glb` is the portable character audition. `rowan-talking-audition.mp4` is the six-second voiced preview. Actual Unreal playback has not been verified; GLB roundtrip is not a substitute for an Unreal import/render test.

## Credits and licenses

MPFB source: MakeHuman Community, GPL-3.0; generated assets use the separately licensed graphics. The selected official system assets are CC0. Faceunits 01 are CC0, contributed by Mika Suominen. Source URLs, pinned revision and archive hashes are saved in `asset-sources.json`.

https://github.com/makehumancommunity/mpfb2/blob/v2.0.18/LICENSE.md

https://static.makehumancommunity.org/assets/assetpacks/makehuman_system_assets.html

https://static.makehumancommunity.org/assets/assetpacks/faceunits01.html

## Next boundary

The image-guided follow-up is in `samples/mpfb-mira`. `image_preset.py` extracts face ratios locally, and `build.py -- --preset <json> --output <new-directory>` applies a separate appearance preset while reusing this rig and audition. The render/export/finish scripts accept `--directory` and `--name`; their original Rowan defaults are preserved. The initial image mapping is heuristic and non-geometric choices still need explicit art direction.

Use this as a reusable **human template generator**. Character appearance can vary while the topology and facial names remain consistent. A different model family, such as a lion, needs a separate facial template and calibration. The experiment is opt-in and has not changed the production server or approved character catalog.
