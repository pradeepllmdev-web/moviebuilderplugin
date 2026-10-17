# Free environment starter assets

Downloaded from Kenney's official website. All three included License.txt files confirm CC0 and personal/commercial use. No payment or account was needed.

| Pack | Unique models (FBX count) | Intended sets |
| --- | ---: | --- |
| Furniture Kit | 140 | Rooms, offices, furnished interiors |
| City Kit Industrial | 37 | Factories, warehouses, industrial streets |
| City Kit Suburban | 40 | Neighborhoods, houses, exterior streets |

These are stylized kits, not photorealistic assets. ZIP archives and extracted files remain local and are excluded from Git. `manifest.json` records source URLs, archive hashes, formats, and license paths. Run `../download_free_assets.py` to obtain the same versions again. No model geometry is inspected by that script.

Status: all 217 meshes imported into the separate LatestSceneVerification project under `/Game/EnvironmentAssets/Kenney`. Import settings request simple collision. `unreal-import.json` records mesh bounds and material assignment checks; collision behavior has not been play-tested.

Three sample levels and screenshots are saved under `../demos/FreeKit_*` and listed in the local studio gallery. Samples use height normalization in centimeters, room walls or outdoor ground, directional/skylight lighting, and preview cameras. These are asset demonstration sets, not completed production environments. Existing outdoor assets and levels are preserved; repeated builds save new versioned levels.

Run `import_free_assets_unreal.py` inside the verification editor to import missing meshes without overwriting existing assets. Run `verify_kit_demos.py` with the local bridge running on port 8520 to create and capture the samples. Image-driven placement for these interior/urban kits is not implemented yet; the image workflow still supports natural outdoor environments.
