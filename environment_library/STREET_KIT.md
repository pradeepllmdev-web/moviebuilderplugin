# Reusable street kit

`road_assembly.py` compiles straight, corner, T and cross tiles into boxes and compatible road connectors. Each tile is 1000 cm square: two 350 cm lanes plus 150 cm pavement on either side. Road surface is Z=0; pavement top is Z=15. Paint has no collision; pavement and road boxes use BlockAll.

Recipes use integer tile cells and quarter-turn yaw. Duplicate placements, duplicate IDs and adjoining road ports meeting a closed pavement edge are rejected. Compiled output records matched links and open ports. This validates the tile network, not vehicle navigation or arbitrary geometry overlaps. Disconnected islands are allowed and exposed through unmatched ports.

Demo: `build_streets_unreal.py` creates a new unique map and materials, then saves recipe, assembly and build report. Nine tiles create a cross with eight matched connections and four open boundaries. `capture_streets.py` captures overview and pedestrian-height views. Refresh the Environment Studio to view them.

Validation: four unit checks passed for network links, rotation, duplicates and closed-edge mismatch; Python compilation and browser module syntax passed; native Unreal saved-map report and overview screenshot inspected. Browser clickthrough not performed.

Limitations: flat terrain, square corners, no curb ramps, stop lines, drainage, traffic logic, navigation, road slope handling or surface weathering. Current visuals are blockout quality. Existing maps are preserved. Main image-analysis workflow still handles natural outdoors; it does not yet infer and assemble these streets from images.

Next: unify architecture, street and scanned-asset references in one registry; assemble dressed neighbourhood recipes; add placement clearances and pedestrian/vehicle routes before traffic simulation.
