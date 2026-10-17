# Reference-guided Mira template experiment

This sample tests **image measurements → MPFB appearance preset → facial/body audition** using the existing fictional Mira reference from `samples/new-character-mira/reference.png`.

MediaPipe measures five facial ratios locally. Six conservative MPFB shape adjustments are derived from them: both eye sizes, nose width, mouth width, jaw width and face height. Only ratios and a source-image hash are saved; no landmark or model geometry arrays are printed. Hair, skin, outfit and colors are explicit art direction, not automatically reconstructed.

This produces an approximate template character. It does not reproduce the source's exact identity, feature-film style, swept hairstyle, jacket details or textures. The existing hairstyle and long-sleeve shirt/trousers are substitutes. It does not reuse the unrigged Meshy face.

## Reproduce

Ensure the isolated MPFB setup from `samples/mpfb-character/download_assets.py` exists. The measurement step requires the local capture Python environment with MediaPipe/OpenCV; the encoder requires `imageio_ffmpeg`.

```text
python samples/mpfb-character/image_preset.py --image samples/new-character-mira/reference.png --output samples/mpfb-mira/appearance.json
blender --background --disable-autoexec --python samples/mpfb-character/build.py -- --preset samples/mpfb-mira/appearance.json --output samples/mpfb-mira
blender --background --disable-autoexec --python samples/mpfb-character/verify_export.py -- --directory samples/mpfb-mira --name mira-template
blender --background --disable-autoexec --python samples/mpfb-character/render.py -- --directory samples/mpfb-mira --name mira-template
python samples/mpfb-character/finish.py --directory samples/mpfb-mira --name mira-template
```

The measurement script currently contains reviewed Mira-specific choices for hair, clothes, skin and macro parameters. For another character, edit those fields in the generated preset before building. It is an initial image-guided workflow, not a universal image-to-character generator. The geometric mapping is heuristic and does not currently optimize a rendered face against the image.

## Results and limits

The character retains all 52 ARKit-style face units and the Mixamo body skeleton. The same speech solver, recorded talking/listening adapter, facial expression reference and head-turn test are reused. The six-second audition uses the existing dialogue/audio fixture for comparison, rather than a newly cast voice.

`verification.json` checks all 144 frames before/after GLB export: jaw opening, full eyelid closure, brow animation, hand gestures, stationary hips/feet and head turns. `facial_timing_max_error` compares the sampled facial coefficients, not identity similarity. Actual Unreal playback is not verified.

`likeness.json` separately compares neutral-preview and reference image ratios. In this view, nose/mouth/jaw/face proportions are relatively close, but eye width remains about 17% below the stylized reference. These are descriptive, projection-dependent measurements, not a calibrated identity score. Better likeness would require an iterative render/measure/adjust fitting step and closer hair/clothing assets.

MPFB/asset credits and licenses are documented in `samples/mpfb-character/README.md`. No paid API call or global Blender installation change is involved. Original Rowan and Meshy Mira outputs are preserved.
