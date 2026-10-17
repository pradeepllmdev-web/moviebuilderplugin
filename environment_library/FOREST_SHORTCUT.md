# Prompt-driven story audition

`test_forest_shortcut.py` sends the full story to the existing OpenAI planner through `/api/movie-plan`, validates the result, then requests `/api/movie-pipeline` with `render:false`. No character model is generated or replaced.

The site offers **Build Unreal preview first** beside the full render workflow. Open the saved movie's full master in Unreal to inspect playback. The existing render button runs the checks and creates the website draft afterwards. The same preview control is integrated into the 3dobjectnew Movie Studio component and API proxy.

Supported shared cues: wind gust, twig snap, and `branch_fall`. A falling branch is a keyed, collision-free wooden cylinder with impact audio at `time + duration`. Its landing site is ground-traced, checked for character clearance, and restricted to stationary observation shots. It is a prototype branch, not a detailed tree asset or Chaos physics simulation. Each cue belongs to its shot; prop state does not persist automatically into subsequent shots.

Example cue:

```json
{"type":"branch_fall","time":1,"duration":1,"position_cm":[0,200],"length_cm":90}
```

Use separate full-camera shots for walking/running and close/reaction shots for dialogue. Stationary partner gaze supports actual eye-contact direction; moving characters use bounded manual glances. Full-body turn-in-place, physical dodges, contact reactions and Rowan's walking remain separate animation work. This story keeps Rowan stationary and uses Leo's tested locomotion.

`forest-shortcut-plan.json`, `forest-shortcut-job.json`, and `forest-shortcut-result.json` record the local audition. Generated movie folders contain their plan, contact/animation reports, editable master metadata and, once rendered, the video. Visual review is still required for appeal, hands, knees, gaze and camera composition.
