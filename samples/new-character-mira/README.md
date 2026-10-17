# Mira: image to registered-body audition

New fully clothed humanoid reference generated for this test. Original characters and movies are unchanged.

1. `python -m movie_production.meshy_api --image samples/new-character-mira/reference.png --output samples/new-character-mira --env-file <existing-local-env>`
2. `blender --background --disable-autoexec --python samples/new-character-mira/audition.py`
3. Review `capabilities.json`, `body-profile.json`, and `audition-preview.png`.
4. Add `-- --render` to render the six-second body audition.

The Meshy runner records each paid task ID and refuses a blind retry after an uncertain submission. It uses the configured credential without copying it into this repository. Do not run two instances against the same output directory.

The Blender audition reads assets internally and outputs skeleton/control names, shape-key names and small diagnostics. Geometry arrays are never printed. The same `BodyRetargeter` and captured talking reference used for Snow/Jacob drive the new body, with separate existing listening motion. This is a stationary upper-body test; it does not certify walking, foot contact or finger performance.

Body auto-rigging does not establish facial readiness. Jaw, eyelids, eyes and expression controls must be audited and calibrated before lip sync is enabled. The new character remains outside the approved production catalog until visual review and facial setup are complete.

Official API specifications: https://docs.meshy.ai/en/api/image-to-3d and https://docs.meshy.ai/en/api/rigging .

## Actual result

Meshy generation and auto-rig succeeded, reporting 30 + 5 credits. The asset contains 24 body/head bones, one skinned body mesh, and no shape keys or dedicated jaw/eyelid controls. An unskinned helper object was excluded from scene framing and rendering.

The spine mapping was validated by parent hierarchy (`Spine02` → `Spine01` → `Spine`), rather than interpreting numeric labels as anatomy. Six-second motion checks passed: hand movement is present, head orientation changes by about 12 degrees, hips and feet remain stationary, and maximum hand displacement per frame is below 3 cm. This is an upper-body audition, without dialogue audio or facial lip sync.

Existing facial rigs can supply animation semantics and a reusable facial template. Arbitrary Meshy topology cannot directly inherit another character's shape keys. For reliable future human characters, fit a tested facial topology and preserve vertex ordering, its jaw/mouth/eyelid components and rig; then calibrate the shared facial profile and run a separate facial audition. Transferred weights need review around lips, eyelids and neck. A custom original-face retopology is another route when identity preservation is more important than setup speed.
