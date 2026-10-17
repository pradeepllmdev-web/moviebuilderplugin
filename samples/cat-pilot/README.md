# Cat Pilot free rig evaluation

Source: https://opengameart.org/node/95204
Creator: Tomcat94. License: CC0 / public domain, as stated on the asset page. Credit retained voluntarily. Downloaded original CatPilot.blend and catPilotTex.png are unchanged in source/.

Inspected inside Blender 5.2 with automatic script execution disabled. The model has a body rig, Walk/Run/Cheer and other actions, and one Eyes shape key. It has no jaw bone, speech visemes, separate talking mouth controls, or full facial expression rig. Its smile is painted in the texture. This is a body-and-blink candidate, not a ready-made talking-cat template.

The old material slot was missing after import; the local preview copy reconnects the supplied atlas through a modern Principled material. cat-pilot-preview.mp4 demonstrates the included walk, run, cheer, and eye closure. No paid API/service was used. Geometry arrays were never emitted.

Experimental speaking copy: talking/cat-pilot-talking.blend and talking/cat-pilot-talking.mp4. Local mouth topology subdivided, lip seam split, five speech/expression keys added, ten oral parts bound to Head. Original Eyes key interpolated through topology changes. Source asset and body clips preserved. Windows SAPI supplies free speech timing. Upper-face speech displacement checked at zero. This prototype still retains the painted smile, a shared blink, and no independent brow/gaze rig. face-profile.json documents mappings; it is not production approved.
