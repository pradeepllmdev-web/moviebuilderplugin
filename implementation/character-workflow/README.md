# Generate Character + Demo

Implemented in 3dobjectnew, as an opt-in workflow. Buttons appear in the 3D Character tab (image upload), series cast cards and character image record details.

API: POST /api/character-workflows with reference_file_id, name and optional text; GET collection or job ID; POST /{id}/resume; GET /{id}/files/{artifact}. Completed stages and Meshy task IDs persist to server/character_workflows/<id>. Server interruptions are detected. Resume reuses saved Meshy tasks; uncertain paid submissions require reconciliation and are never blindly retried. A single-worker queue serializes GPU-intensive jobs. Original images/models are retained.

Pipeline: dependency preflight -> Meshy image model/body rig -> vision landmarks -> facial morphs, fitted lids and separate oral anatomy -> existing recorded/procedural animation library -> structural validation -> standing/walking/running/circular speaking videos. Uses Windows SAPI voice for demos, avoiding further voice API costs. Each video is fully decoded after encoding.

Supported starting scope: full-body humanoid bipeds, PNG/JPEG references. Single skinned mesh facial adapter; other topology can stop with Needs attention. Quadrupeds are not supported. Images are not regenerated or stripped of clothing.

All successful results remain Needs review. Structural checks do not certify eyelid coverage, lip closure, likeness, oral intersections, foot contacts or turns. Generic demos do not inherit the bespoke lion's exact contact calibration; inspect them before movie use. No auto-approval, universal image-to-rig guarantee or Unreal verification is claimed.

Validation: frontend production build passes; six workflow tests cover persistence/interruption, resume, failure reporting, landmark bounds and artifact containment. Blender demo renderer renders a two-frame fixture. Facial adapter fits 18 oral parts and 16 controls to an existing lion fixture. No fresh paid model was generated during implementation. First new-image end-to-end run is pending user input.

Runtime services started: site 5173, API 8000, media service 8100. Ollama reports qwen3-vl:8b available. ComfyUI is offline but not used for this workflow because the supplied image goes directly to Meshy.

First new-image test completed: Amber Cat, job 8fe21e60764a4190ae23f4f2df71fd65, stored reference file 5007. All seven stages finished and four MP4 demos decoded successfully. Result remains Needs review. Meshy used one model generation and one body rig. The run exposed two general fixes: transient Windows replace locks now retry, and demo body actions are filtered to compatible OBJECT slots (avoiding Face/KEY actions). Resume reused the original paid Meshy task. Seven workflow regression tests now pass. Rendered samples show blinks and gait, but rough generated fur and mouth fitting still require visual refinement. No production approval is implied.

Amber facial quality correction: full-body landmarks and aggressive oral replacement distorted the muzzle. New defaults use a local face-crop second pass, preserve the original mouth anatomy, quarter-strength neutral closure and damped speech shapes. Experimental replacement fitter remains separate. The eyelid primitive winding was reversed for +Z-facing characters relative to its supplied normals; the workflow now corrects it and narrows the lash band. A separate close-up refinement preserves all original assets. Baked jagged fur and incomplete lip closure remain quality limitations; no new Meshy calls were made.
