# Turning, conversation and visual review

The reusable `turn` action is a walking arc, not a planted-foot pivot or motion-captured turn. It currently supports the calibrated lion, 30–120 degrees either direction, radius 60–100cm, duration 2–6 seconds and arc speed 20–120cm/s. Use a full camera and separate stationary dialogue shots for partner gaze. Subsequent movement uses the resulting heading. The movie builder carries both placement and turned heading across cuts.

```json
{"action":"turn","duration":2,"angle_deg":-90,"radius_cm":80,"dialogue":""}
```

Negative angles turn toward +X from the initial +Y heading. Turns use the walking animation on a curved root path; visual checks for skating, foot contacts and acceleration remain necessary. Keep these auditions separate from jumping, circles, dancing and hand props. Rowan remains stationary until his locomotion is calibrated.

`lookdev:"soft_portrait"` adds broad following fill lights to the generated scene and master. It does not modify source models, fur geometry, teeth or eyelid controls. Existing materials and eye conversion remain intact.

Review reports now include per-frame heading snap checks, approximate head/foot framing from scalar profile heights, root placement/heading across cuts, body and facial animation availability, missing branch actors and dialogue duration. Framing checks are warnings and do not cover occlusion or actual mesh silhouettes. Contact checks cover ground, slope, steps, routes and actor separation, not physics-driven collisions or finger gripping.

Full movement shots automatically widen from 32mm to 28mm if the approximate head/foot check flags cropping, then report whether the wider view clears it. Portrait views use a less tight 42mm lens. Final head-pose continuity is blended after attention corrections so a new gaze target does not snap the head at a cut. Review warnings explicitly retain unverified animal eyelids and overlapping speech.

Suggested prompt: “Leo takes a short walk, stops when Rowan calls, makes a 90 degree right walking turn, looks at Rowan during a stationary conversation, then makes a left walking turn and continues. Keep Rowan stationary. Use a morning forest, full movement shots, a dialogue close-up, soft_portrait lighting, and preserve heading and position between shots.”

Use **Build Unreal preview first**. Review Sequencer playback, then render the website draft. `test_turn_conversation.py` builds the independent audition without replacing earlier movies. Reports and videos are stored in its unique movie/scene job folders.
