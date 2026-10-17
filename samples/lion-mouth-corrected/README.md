# Correct mouth position below the original muzzle

The previous repair inherited an incorrect mouth height near the nose. A front-camera ray calibration places the visible lip line at rig-local Z 1.244 m, below the original nose region around 1.316 m. The corrected copy splits the mouth at this actual lip line, keeps nose/upper-muzzle jaw weights zero and disables the legacy nose-level speech shapes.

Original facial shape data is interpolated internally through the new seam, and its weights are explicitly reset to zero before the correct controls are applied. New round/wide/close/press/smile controls are localized to the lower mouth. Teeth, tongue, gums and oral lining are repositioned accordingly.

`neutral.png` and `speech.png` show the location correction. The interior still needs fitting/cleanup before a new movie preview is warranted; there is visible original skin inside the opening. An open-mouth reference of the same lion will help guide that work. This folder is a correction checkpoint, not a finished facial asset.

`check_nose.py` checks the source nose/upper-muzzle deformation when the new jaw and all new mouth shapes are opened. Geometry is processed inside Blender; only count/error diagnostics are emitted. `nose-regression.json` stores that result.

The earlier incorrect video and original source remain preserved. Build with `samples/lion-conversation/build.py -- --repair --output samples/lion-mouth-corrected` under Blender with automatic script execution disabled.
