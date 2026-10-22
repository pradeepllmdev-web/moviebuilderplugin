# Quality checklist: every complaint from a viewing, and the check that now guards it

A complaint is only fixed when something in the build would catch it next time. Each row names the guard (a text that must appear in the code: `tests/test_quality_checklist.py` fails if a guard is removed). "Manual" rows are what the review pack (`review_pack.py`) puts in front of a human.

| Complaint from a viewing | Guard |
|---|---|
| Characters walk through walls, objects, each other | `AUDIT collision` |
| Characters turn all at once, or turn their whole body to talk | `AUDIT turn` |
| Lip movement not in sync with the voice | `AUDIT lip sync` |
| Speakers and listeners not looking at each other | `AUDIT eye line` |
| Feet slide on the ground when walking | `AUDIT foot slip` |
| Hands do not reach the prop they hold or take | `AUDIT reach` |
| Faces cut off, empty frames, back-of-head shots | `AUDIT framing` |
| Something stands between the lens and everyone | `AUDIT occluded` |
| Camera inside a tree, rock or house | `_out_of_solids` |
| Arms held out in a T, bodies sunk in the ground, bodies overlapping, people frozen | `AUDIT pose: arms held out in a T` |
| People standing frozen like figures in a game | `stands almost motionless` |
| Characters walk around with no purpose | `walks for` |
| Story unclear: props set up and never used, props vanish between scenes | `is set up but never used` |
| A prop disappears between scenes | `does not carry it on` |
| The same line twice, or a late first line | `the first line comes at` |
| The film just stops (no closing beat) | `closing beat` |
| Scenes drag: long stretches with no speech and no story event | `no speech and no story event` |
| Silent or broken voice files, half-written build files | `def usable` |
| People run when they should walk | `a run is a jog` |
| Hands in tight fists | `relaxed hands` |
| Voices unclear, dialogue flat, story hard to follow with the sound off | Manual: read the lines and shots in `review_pack.html` |
| Acting looks unnatural, hands and posture look stiff | Manual: look at the stills in `review_pack.html`; for motion, watch the draft |
| Animals and T-rex animate poorly | Manual (limited: the models ship only five or six actions) |
