# Open saved environments and native scenes in Unreal

Environment Studio adds buttons to saved environment cards, comparison previews and native delivery-scene video. A shared observer binds buttons to saved build reports/level labels. Composite movie cards and asset inventory previews are excluded: composites do not have an equivalent native scene.

POST /api/open-unreal accepts only a level recorded by studio metadata or the fixed scene ID delivery. Arbitrary commands, unknown asset paths and arbitrary sequences are not accepted. Open jobs share the same editor lock as builds and return confirmed success/error through job status.

open_saved_unreal.py checks the verification project and both dirty map and dirty content packages BEFORE loading anything. It never saves/discards changes automatically. The native scene loads its saved map and opens its recorded LevelSequence; it does not autoplay.

Main 3dobjectnew adds /api/environment-production/open and environment buttons in generated/saved results. Its API forwards to the same guarded local operation. Main frontend production build passed.

Four safety tests passed: dirty map refuses load; dirty content refuses load; clean environment loads; clean scene loads map then sequence. Local live request was refused because Unreal had unsaved changes; no map was switched. Real successful load remains to be retried after the user saves/discards changes in the editor. Browser clickthrough was not performed.
