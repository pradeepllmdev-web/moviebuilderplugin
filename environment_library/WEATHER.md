# Rain and snow (prototype)

Weather contract: type none/rain/snow; intensity0..2; wind_cm_s [x,y] bounded±500; wetness0..1; snow_cover0..1. Missing weather defaults to none. Text rain/snow keywords supply planner defaults; the AI still returns the full validated plan. Explicit no/without weather suppresses inference.

Existing /Game/UnrealBridge/FX/NS_Weather is reused. Particle user parameters are set and the effect is advanced for editor preview. Area100m; wind and intensity feed existing presets; sprites reduced for readability. Full movie-motion rendering not verified this turn; saved-map screenshots show effects.

Wetness: duplicate direct materials into unique per-build folders; darken base colour and reduce roughness. Original materials are preserved. Complex imported material instances are left unchanged.

Snow cover: noncolliding thin flat caps on generated ground and roof boxes. Not physically accumulated snow, no footprints and no snow on foliage/imported rooftops. Mountain surfaces use the existing mountain generator. Weather does not yet collide with roofs or shelter characters indoors. No puddles/splashes.

Presets available in Asset Library → Generators & presets. Demo previews in Existing environments → Prompt examples. Main 3dobjectnew planner/build API carries the same weather contract.

Tests: five weather validation checks and eleven planner checks passed. Rain native build c2ec4adaca4b has98 changed direct-material slots; snow f9144e11985c has three simple caps and an active snowfall effect. Both inspected visually. Earlier snow shader attempt was replaced with predictable caps; failed maps preserved.
