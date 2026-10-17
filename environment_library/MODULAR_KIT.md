# Modular environment kit

First implemented category: architecture. `modular_assembly.py` defines reusable wall, doorway, window, floor, roof, corner and stair modules. Dimensions are centimetres; placement uses a 100 cm XY / 20 cm Z grid and 90 degree rotations. Wall modules are 200 cm wide and 300 cm high. Door opening is 100 × 220 cm; window sill 80 cm. Origins are at module floor height. Floor thickness extends downward.

`room_recipe(width, depth)` assembles different tile counts. `compile_recipe` emits geometry, wall end connectors and passage anchors, and rejects invalid coordinates, duplicate IDs and identical placements. Connectors are metadata for future snapping; the room generator currently places parts directly. This is not a general overlap solver or automatic navigation validator.

`build_modular_unreal.py` creates a uniquely named new level, uses existing free wood/plaster materials, enables BlockAll collision on boxes, and saves the recipe, compiled assembly and build report. The demo leaves the room roof off to expose the interior; a roof tile and stairs stand separately. Height markers represent the existing lion/cat heights, not character models. Existing levels are preserved.

Verification: `python -m unittest test_modular_assembly -v` (four checks); native Unreal build and saved-map result; `capture_modular.py` captures overview/doorway. Overview visually checked. Browser JavaScript syntax checked; browser clickthrough not performed.

Demo: refresh http://127.0.0.1:8521/ and find Modular environment kit. Gallery and dedicated section serve native editor screenshots.

Next categories: roads/pavements/junctions, then unified scanned vegetation/rock asset references, props and vehicles. Remaining architecture work: automatic connector matching, complete intersection and path checks, stairs landing compatibility, multi-room assembly, glazing/trim, dressing rules and main 3dobjectnew integration. Existing scanned assets and Kenney pack metadata remain in their current registries; they are not yet unified with this kit.
