# Website character workflow, performance v2

Installed in 3dobjectnew through install_performance.py, which backs up only the five affected files. The original Meshy generation/rigging client and its persisted task IDs are unchanged. No Meshy requests are made by verification scripts.

New jobs automatically use:

- Source mouth pose detection, with an open/closed override on the upload panel. A protected lower-jaw rotation preserves the source nose and upper face. Open mouths become a near-closed basis with a jawOpen morph reversing the closure. Closed mouths retain their basis and get a downward jaw motion.
- Original textures, existing oral geometry and skin weights. No invented replacement face or new mouth at the nose.
- Fitted skin-colored closure eyelids, corrected winding and a narrow lash edge.
- Speech-envelope gesture gating. A native idle pose is held during pauses; talking gestures blend in slowly at 18% by default. Quiet disables these gestures. Only upper-body rotations are blended for stationary tests. Head attention and facial controls remain active.
- Standing, walking, running and circular-running full-body videos, plus a procedural forest scene preview using the entered dialogue. The scene opens and ends wide and moves closer during dialogue.
- Editable demo.blend files and standalone animated performance.glb exports for the stationary/scene results. These include the actual baked calm performance; the separately downloadable character model retains its reusable animation library.

Use the site's Generate Character + Demo panel, choose a full-body biped image, enter dialogue, optionally choose the source mouth pose and gesture level, then generate. Compact character-image buttons use automatic mouth detection and subtle gestures. Refresh the page after installation. New Meshy generations still require credits.

Existing jobs and models are preserved and are not silently reprocessed or charged again. The improved paired lion/cat movie is a separate scene sample; the website creates one-character demos and a one-character forest preview rather than automatically authoring a two-character movie.

Validation: workflow regression tests, performance math tests, frontend build, installed Blender renderer, GLB structural validation, complete MP4 decode and visual checks on an existing cat fixture. These checks do not guarantee the likeness or topology of a new Meshy result. Auto landmarks can fail; missing anatomy cannot be recovered reliably from an image. Unusual rigs, separate oral meshes, lip closure, walking contacts and intersections still require visual review. Unreal export has not been validated by this update.

Files: server/character_workflow.py, server/character_workflow_face.py, server/character_workflow_performance.py, server/blender_scripts/character_workflow_demo.py, client/src/components/CharacterWorkflow.tsx.
