# Lion and cat environment story previews

Nine new short stories use the existing Leo lion and Amber cat. Original character sources, animations and Unreal levels remain preserved. No Meshy calls or paid generation are used.

| Environment | Story | Distinct action study |
| --- | --- | --- |
| Riverbank | The Floating Crown | Reach/lean and a drifting ring-shaped crown prop |
| Pine forest | The Echo Detective | Listening tilt and raised arm |
| Broadleaf woodland | The Tiny Giant | Careful lean/look down and a moving beetle prop |
| Meadow | The Backwards Race | Retargeted Mixamo running, slight root movement |
| Highland | The Brave First Step | Balance pose and controlled torso sway |
| House interior | The Secret Recipe | Stirring wrist/forearm gesture and a pot prop |
| Skyscraper city | The Cloud Inspectors | Upward head angle and raised pointing arm |
| Industrial district | The Rhythm Factory | Rhythmic upper-body dance and drum prop |
| Suburban neighborhood | The Surprise Delivery | Wave and parcel prop |

All have new offline SAPI dialogue, viseme-derived jaw/lip controls, blinks, brows, head turns, captions, and a quiet locally synthesized musical bed. The running action is retargeted from the installed motion library. Other actions are newly keyed procedural pose studies; they are not new motion-capture performances. The small props communicate the idea, but do not have a physical hand-contact solver.

These are explicitly labelled **previsualization composites**: Blender renders the animated foreground onto a still Unreal background view. They do not demonstrate characters imported into Unreal, moving-camera parallax, collisions, occlusion by environment objects, or physically matched lighting/contact shadows. Industrial/suburban plates remain stylized Kenney kit studies. Approximate graphic shadows are used. The race is an in-place motion study with small root movement, not a physically validated backwards locomotion clip.

Output: `demos/CharacterStories/<id>/movie.mp4`, `poster.png`, `performance.blend`, plan.json, render-complete.json and delivery.json. The combined reel is `demos/CharacterStories/all-stories.mp4`. Videos are 768 × 432 at 12 fps and roughly 7–9 seconds each, suitable for evaluating variety rather than final film quality. Delivery reports confirm complete FFmpeg decoding, not artistic correctness.

Rebuild dialogue: run prepare_character_stories.py using server Python. Render and encode sequentially: run run_character_stories.py. Requires installed Blender and original character/motion files. The runner creates new performances in these preview folders; it does not overwrite original films. Current story folders are fixed IDs, so rerunning intentionally replaces their preview outputs. character_stories.js presents completed deliveries and the combined reel on the local environment studio page.

`improve_story_plates.py` captures character-height alternatives for highland, city, industrial and suburban sets, using `set_story_plate_unreal.py` to open existing saved levels and set an unsaved viewport camera. The house plate temporarily hides dining furniture for a clear acting area; the saved house is unchanged. A small Blender table supports the cooking prop. After changing background plans, use `run_character_stories.py --finish-only`; after replacing one clip, use `--assemble-only` to regenerate the reel. Re-running prepare_character_stories.py resets backgrounds to the original views, so recapture/reapply plate choices afterward.

Next integration step: transfer approved skeletal performance and facial curves into Unreal/Sequencer, stage characters at real world coordinates, then render with environment occlusion and physically matched lighting. This composite workflow is not a replacement for that integration.
