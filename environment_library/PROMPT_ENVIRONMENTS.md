# Prompt-to-Unreal environments

Refresh http://127.0.0.1:8521/ and use **Build an environment from a prompt**. Generate plan, inspect notes/unsupported requests, then Build validated plan. The completed job displays a saved-map path and native Unreal preview. Existing levels are preserved.

The planner reuses `3dobjectnew/server/scene_ai.py` and its existing provider/model selection, environment loading and request logging. No credentials are copied or returned to the browser. No changes were made to the sibling repository. This form currently lives in Environment Studio, not the main 3dobjectnew frontend.

`index_prompt_assets_unreal.py` indexes installed StaticMesh and SkeletalMesh names, asset paths, bounds and bottom offsets. `assets/prompt-catalog.json` currently contains 28 scanned variants, including 12 trees. It reads metadata/bounds, not vertices or face data. Run the indexer again after installing assets.

`prompt_environment.py` selects up to 16 candidate descriptions by prompt keyword relevance. Only compact IDs/names/categories/dimensions are sent to the model. The backend retains Unreal paths. The existing shared client uses JSON mode, not strict JSON-schema Structured Outputs. Backend validation is mandatory and one AI repair is allowed. A future shared-client enhancement can add strict schema output without changing existing generation calls.

Implemented checks: supported lighting, bounded tile/building/instance counts, known asset IDs, supplied candidate IDs, grid and transform bounds, road neighbour connections, building/building and building/road overlap, vegetation bounding footprints against buildings/roads. These are conservative axis-aligned checks, not runtime navigation. Asset-to-asset spacing, disconnected road components, slopes, accessible door-to-road paths and terrain grounding beyond the flat plane are not solved yet.

Builder: `build_prompt_unreal.py` creates box-based architecture/street geometry and places real catalogue meshes at their bounds-based ground offset. It saves plan, compiled assembly and result in a unique PromptSet folder/map. Trees may cluster and building detail remains blockout quality. Rivers, terrain mountains, vehicles, interior dressing and arbitrary new assets are unsupported by this planner version; the AI is instructed to report them.

Endpoints: POST /api/prompt-plan {prompt}; GET /api/jobs/{id}; POST /api/prompt-build {plan}. Both prompt and existing image jobs share one Unreal build lock. Review/build uses the exact validated plan, not a second AI generation. Errors do not silently substitute demo layouts.

Validation: five prompt checks plus four road and four architecture checks; Python compile and JS syntax checks. Real configured-provider prompt, native Unreal saved build and screenshot inspection completed for PromptSet_3a1b7fd9a2fe. Browser clickthrough was not performed. Initial overlap and build-report failures were fixed before the successful run.

Cloud providers can consume configured API credits; local provider selection remains available through existing 3dobjectnew configuration. No assets or paid services were purchased.
