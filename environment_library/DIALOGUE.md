# Dialogue in the movie flow

Write a conversation in a story paragraph and it becomes a `talk` scene (any paragraph with two or more spoken lines; `set_pieces.match` and `story_plan` do this automatically):

    Around the campfire Leo and Mara plan the quest.
    Mara (serious): "The old map says the crystal sleeps under the dome."
    Leo (warm): "Then at moonrise we wake it."

Or in prose: `Mara says, "Not yet," and Leo replies, "Then we keep going."` Moods: serious, angry, warm, concern, sad, joy (guessed from the text when not given). Setting: `campfire` (default) or `hall` (the words hall/council/table/throne/chamber in the paragraph). Up to 4 speakers and 24 lines per scene.

What the scene does (`talk_scene.py`, built on `scene_base`): times each line from its syllables or from a real recording; voices it; keys the mouth (jaw, round, wide on the face, teeth, tongue and mouth interior) from the voice; keys the expression from the mood and gives the addressee a reaction;
blinks every character; plays a talk/argue/shrug/laugh clip for the speaker and a nod/think/laugh reaction for the addressee; keeps every head on a gaze target that moves to the speaker (the speaker looks at the addressee); generates the camera coverage
(wide, over-the-shoulder, reaction single, two-shot, wide close) with depth of field and a light handheld sway. The audit checks overlaps, eye lines (speaker and listeners within 32/38 degrees at mid-line), mouth shapes per syllable, voice length.

Real voices: put `line_<k>.wav` (k = 0-based line number within the scene, PCM16, any rate) in a folder and set `VOICE_DIR` to it (or use `dialogue.register_voice_provider(name, fn)` with a text-to-speech service). The recording's length becomes the line's length and its energy envelope places the syllables, so the mouth follows the real speech.
Voice tracks are written one per speaker (`audio_talk/voice_<name>.wav`), so they can be mixed or replaced separately in Unreal.

Known limits: the ring of characters is static (no walking or blocking changes), gestures come from clips (no IK, and the lion rig has no finger bones, so no finger poses), the default voice is a synthesiser (intelligible rhythm, not speech).
