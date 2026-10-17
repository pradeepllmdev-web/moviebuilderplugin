# Sitting on a bench

Lion actions `sit_down`, `sit`, `sit_talk` and `stand_up` (each transition at least 2.5 s), mixed only with idle/talk. Example: `test_sit_movie.py` (sit down, a seated line, stand up, across three shots).

| Action | Clip | Notes |
|---|---|---|
| `sit_down` | `Stand_To_Sit`, from 2 s in | skips the clip's shuffle; descent 0.5–1.5 s into the beat |
| `sit` | `Sit_Idle` | seated hips match `Stand_To_Sit` (37.6 cm) |
| `sit_talk` | `Mixamo_Sitting_Talking` | aligned to the seat by its hips |
| `stand_up` | `Sit_To_Stand_M` | rise 1.4–2.8 s into the beat |

How it fits the lion (all on the per-job copy; source models untouched):

- **Clip stitching** (`clip_stitch.py`): mocap clips are not in place, so each clip is shifted to where the previous one left off — at the feet while standing, at the hips while seated (so the body never slides along the seat). A shot that opens seated puts its hips at the lion's seated anchor (`DEFAULT_SEAT['hips_cm']`), so every shot agrees on the seat.
- **Sitting back**: on the lion's short legs the hips drop almost straight down, so the root eases 25 cm back during the descent while foot locking pins the feet (and forward again when standing up).
- **Seat from the body**: `seat.json` takes the lowest pelvis/thigh vertex under the hips over the seated frames (≈13 cm on the lion, same spot in every shot within 2 mm). `sit_props_unreal.py` puts a solid 70 × 32 cm wooden bench there.
- **Grounding** uses the feet while sitting (the tail and folded thighs go below the feet).
- **Lean cap**: forward tilt of spine/neck/head is capped during sit_down/stand_up (the lion's big head turned the clip's natural lean into a deep bow).
- **Tail** (`tail_rig.py`): the lion's tail was weighted to the leg bones, so it swung with the legs and sank 25–45 cm into the floor when seated. A `Tail` bone under the hips now carries it, lifted each frame just enough to clear the ground and the bench, with a slow sway. Also applied to lion walking/idle/talk/run/circle shots (grounded on the body without the tail).

## Fast checks

- `python -m unittest discover -s tests -p "test_*.py"` — 0.5 s, rules and geometry.
- `python quick_review.py shot all --plan test_sit_movie:PLAN --no-sheet` — every shot in parallel in Blender, ~10 s, prints seat/tail/safety/foot numbers.
- `python quick_review.py shot 1 --plan test_sit_movie:PLAN` — adds a side-view sheet with a bench proxy (~12 s).
- `python quick_review.py movie --plan test_sit_movie:PLAN` — full Unreal preview (~1 min) plus a frame sheet; editor icons are hidden automatically. Restart `studio_server.py` after code changes first.

Known gaps: seated foot drift up to ~10 cm during sit_down; seat height varies 0.5 cm between shots.
