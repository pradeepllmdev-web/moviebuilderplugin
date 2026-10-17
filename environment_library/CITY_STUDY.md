# Skyscraper city study

`build_skyscraper_city_unreal.py` runs inside the separate verification editor and saves a new uniquely named level. It creates 25 buildings over a five-by-five block layout, including a fictional 600 metre landmark. Other buildings range from roughly 80 to 260 metres. Each block has a podium and pavement; towers have roof caps/equipment, while the landmark uses four setbacks and a spire. Road markings, crossings and streetlight geometry provide pedestrian scale.

The façade is an opaque metallic material with a world-position window-grid shader. It is not transparent glass or furnished interiors. This is a procedural massing/scale study, not a finished realistic city. Missing production elements include varied architecture, detailed façades and ground-floor entrances, traffic, crowds, background districts and richer road surfaces.

Run `capture_house.py --set city` against local bridge 8520 to capture skyline and street views after a successful build. `demos/latest-city.json` records the active study and cameras; its directory contains build-result.json and two inspected screenshots. Captures are served by the demo site and city_showcase.js displays them on refresh. No paid assets or new downloads were needed.

Verified level save, two visual inspections, 25-building metadata with tallest height 600 metres, Python/JavaScript syntax checks, and gallery/static HTTP access. Browser clickthrough and character/navigation tests have not been performed. An initial material API error was corrected using set_editor_property; the completed level was built after that correction.
