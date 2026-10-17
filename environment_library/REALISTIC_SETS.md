# Realistic set studies

The first study is `demos/RealisticRiver_20261015_093641`. Its build report points to the separately saved polished Unreal level. Existing levels remain preserved.

The set uses already installed scanned trees, rocks, ground surfaces, grass and ferns. A deterministic layout specifies a curved river and woodland regions. Additional ecological layers fill the far-bank woodland and four shore regions. Neutral daylight and light haze replace the first pass's heavy amber morning fog. No model geometry is printed or inspected externally.

`build_realistic_river.py` builds a new version, runs `polish_realistic_river_unreal.py`, and captures three inspection views plus a four-second editor camera study through `capture_realistic_river.py`. Requires the dedicated Unreal verification editor bridge on port 8520. Run only when no other editor build is active. Commands are not automatically retried. The capture is 48 editor snapshots at 12 playback frames per second; it is a camera/layout preview, not Movie Render Queue output or a production-quality temporal render.

Verified: saved build report, three visually inspected PNG views, no reported build warnings, complete MP4 decode, gallery API entry and HTTP access to showcase/video. Browser clickthrough was not performed. The showcase loads on refresh at port 8521.

Remaining quality issues: repeated ground detail, broad sparse bank areas, limited shoreline breakup and distant terrain, and vegetation variety. Production work should address these before promising photorealistic film quality. Interior and street realism remains a later stage; the Kenney asset layouts are stylized demonstrations only.
