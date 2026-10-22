# Prompt-driven pipeline: where every observation lives

Long-term flow: **3dobjectnew** writes the story, character sheets, scenes and shots; **Blender** (this repo) builds character animation and the low-poly world; **Unreal** builds the final movie. The observations from watching films are kept as DATA here, and every stage of that flow gets them as prompt text plus an automatic check.

```
3dobjectnew: story  -> character sheets -> scenes -> shots           (prompts built from production_rules.json: stages story, characters, scenes, shots)
      | story package (JSON)
      v
film_from_story.generate()      model writes the film as JSON in three stages (outline, one call per scene, whole film)
      |                         every answer is compiled by the planner and linted; errors go back to the model as text (repair round)
      v
films/generated/<id>.json  ->  perf_movie.py  ->  review_pack.py  ->  (person reviews the page)  ->  unreal_export.py  ->  Unreal
                                  audits (T-pose, collisions, reach ...)       QUALITY_CHECKLIST.md          production rules U01, U02
```

## The pieces
| piece | file | what it is |
|---|---|---|
| Rules | `production_rules.json` | 29 rules from the viewings: id, stages that receive it, must/should, the exact prompt wording, the check that guards it |
| Prompts | `production_rules.py` | `prompt_for(stage)` = the rules for that stage; for `film_spec` also the engine's real capabilities (read from the code, so a prompt never promises something the engine cannot do) and the film JSON format |
| Lint | `film_lint.py` | `lint(film)` runs the planner and every audit and story check without Blender: `errors` (cannot build) and `notes` (weaker), each mapped to the rule it breaks |
| Writer | `film_from_story.py` | `generate(story)`: outline, then each scene is compiled and, if it has an error or breaks a MUST pacing rule (walks, dead time, no goal), sent back to the model with the exact error |
| Format | a film is a plain dict | `.json` films load exactly like `.py` films (`perf_movie.load_film`), so anything that can write JSON can write a film |

## What 3dobjectnew sends and gets
* Send: a story package: `{"title", "logline", "characters": [...], "scenes": [...]}` or plain story text. Character sheets map onto cast records (`id, name, species, height, width, depth, posture, outfit, colors, description`; use species `person` for people). Scene shots are guidance for the model, not a fixed camera: the camera director chooses shots from the story beats and the storyboard.
* Get: the film JSON, the lint report (`errors`, `notes`, `rules`), and after a build `review_pack.html`, `storyboard.md`, `review.md` and `report.json` (every audit line). Hand these to the person who approves the film.
* Prompt text for the story, character, scene and shot prompts of 3dobjectnew: `production_rules.prompt_for('story' | 'characters' | 'scenes' | 'shots')`; for a model that writes the film itself, `prompt_for('film_spec')`.

## How a new observation becomes part of the process (every time)
1. Add a rule to `production_rules.json` (which stages see it, must or should, the wording, the guard).
2. Add the guard: an audit line, a story-check note or a test, whose text appears in the code. If no check can catch it yet, write `manual` and add the row to `QUALITY_CHECKLIST.md` "Manual".
3. `tests/test_production_rules.py` fails if a rule's guard text is not in the code, so a rule can never silently lose its check.
4. Prompts, the lint and the repair loop pick the rule up with no other change.

## First real test (a 5 second scene, written by Claude acting as the model)
Brief: "Ann returns the book Ben dropped, in 5 seconds". Draft 1 passed the old lint but ran 14 s and had Ann run for no reason, so two checks were added (rule S09 `target_seconds`, rule T04 now enforced). Draft 2 was 10 s; the engine then refused a character doing two things at once ("ann has two beats at the same time"); the accepted answer is one line, then a give with Ben's joy sign, 0.74 m apart: 7.2 s planned, 7.3 s built, 0 audit lines. Findings: a 5 second scene is one action and one line (the give alone is 1.9 s and every scene ends with a 2.6 s tail); and Blender-only audits (arm reach) cannot be seen by the plan-only lint, so a real loop needs a second stage that builds the scene and reads the audit lines (a reach error of 0.24 m was fixed by moving Ben 4 cm). Files: `films/generated/book_return.json`, `scenes/movie_book/`.

## Honest limits
* `film_from_story.generate` is tested with a fake model that makes a mistake and must repair it; it has not been run against a real model yet. Set `LLM_PROVIDER` (`anthropic` with `ANTHROPIC_API_KEY`, or the existing `scene_ai`) and run `python film_from_story.py story.txt`; answers are cached in `analysis_cache/`.
* The lint catches what can be measured. Dialogue quality, acting and story taste stay manual: the review pack puts them in front of a person.
* The Unreal side is unchanged: it receives only scenes with zero audit lines (rule U01).
