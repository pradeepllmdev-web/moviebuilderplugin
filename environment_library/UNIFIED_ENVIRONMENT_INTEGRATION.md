# Unified environment integration (first version)

Main entry: http://127.0.0.1:5173/ → Environments → Create environment / Existing environments.

Integrated into 3dobjectnew:
- server/environment_production_api.py: plan/build/job/media/saved API facade; completed/ready job receipts persisted under server/environment_production.
- server/main.py: router registration.
- client/src/components/EnvironmentProduction.tsx: text + optional image, plan review, unsupported requests, build progress, preview, existing builds.
- client/src/App.tsx: Environments tab, preserving existing tabs.

Current engine service remains Environment Studio on 8521 with Unreal bridge 8520. The main app calls it server-to-server; the browser uses only the main backend endpoints. This is an incremental integration, not a migration of all implementation files into 3dobjectnew. Main frontend/backend run on 5173/8000. No credentials copied to the frontend.

Single plan contract: mood, buildings, roads, assets, optional mountains, reference_analysis, contract_version. Image analysis runs locally and its compact observations feed the same configured AI planner as text. Explicit text guides the requested result. Reference images are appearance guidance, not exact reconstruction. Exact catalogue asset ID selection is preserved.

Mountains now use the existing Unreal procedural alpine_range generator. Height/extent/distance/side are validated. Defaults: 500 m requested maximum height, 1.8 km footprint, 1.4 km centre distance, north (+Y). Backdrop skirt must remain at least 150 m outside origin. Native build report returns generator result. Preview camera changes to show the backdrop. Shape/materials remain procedural study quality.

The foreground is still a flat stage. Hills/valley sculpting, rivers in the combined builder, interiors, arbitrary architecture, semantic door-to-road routes, complete vegetation spacing, image-faithful reconstruction and quality grading remain unfinished. Older image-only nature builders still exist and were preserved. Do not call this universal environment generation.

Safety: new combined builds reject dirty Unreal map packages before opening a blank map. Failed test map from the cached-module error was saved to a unique IncompletePromptTest map; no user map was discarded. Updated planner module is reloaded within Unreal for repeated builds.

Verification:
- Main frontend npm run build passed (existing bundle-size advisory remains).
- Eleven planner checks pass, including mountain ranges/footprint separation.
- Main API real AI plan → native Unreal build → saved map/preview succeeded: PromptSet_93659096671b. Mountain visible in inspected screenshot.
- Combined image+text planning through main API succeeded using the existing Walkthrough reference. Image observations persisted in plan. First attempt rejected overlap; explicit clear placement succeeded.
- Browser clickthrough not performed. Main page/media endpoint HTTP checks performed.

Example: A small village with two houses beside a straight road, spruce trees and a mountain behind, at golden hour. For complex layouts the planner can still fail validation; those failures should be corrected rather than silently replaced with sample layouts.
