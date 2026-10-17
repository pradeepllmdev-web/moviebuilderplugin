"""Verified character profiles: references and control metadata only."""
from pathlib import Path
H=Path(__file__).resolve().parent
PROFILES={
 'rowan':dict(name='Rowan',source='samples/mpfb-character/rowan.blend',catalog=None,material=None,height_cm=180,eye_height_cm=168,facial_profile='arkit',blink=True),
 # Box hold measured on the rig (bone heads, rest pose): shoulders 112cm at x+-24, arm reach ~48cm,
 # belly front 39cm (z85) / 42.5cm (z95), chin/mane underside ~107cm. The box clears belly and chin,
 # side grips stay within ~90% of arm reach, and the stand top sits below the held box.
 'lion':dict(name='Leo',source='samples/lion-grip-ik/scene.blend',catalog='DemoLeo',material='/Game/PhysicsLab/package_20261015_101957/lion/lion.lion',height_cm=185,
  # The final idle variant hunches; posture caps keep it upright and the box top stays under the chin.
  box=dict(size_cm=[36,26,24],hold_forward_cm=59,hold_height_cm=85,lift_cm=6,grip_out_cm=3,grip_back_cm=12,grip_up_cm=8,stand_top_cm=[30,22],
   posture_pitch_limits_deg={'Spine1':4,'Spine2':4,'Neck':2,'Head':15},
   body_cm=dict(back=20,front_low=32,half_width=22,low_height=72),penetration_limit_cm=2.5),
  # Existing eyelid (separate Lid/Crease meshes) and gaze shape keys; opt-in per shot with eye_life.
  # Lid L/R normals point inward when closed, so Unreal's one-sided lid material would cull the blink; flipped on the job copy.
  # Lid morphs reach Unreal intact since the exporter leads with a rest-pose frame (export_performance rest_frame).
  eyes=dict(blink=['BlinkL','BlinkR'],gaze=dict(left='GazeLeft',right='GazeRight',down='GazeDown'),gaze_amount=.35,flip_normals=['Lid L','Lid R'])),
 'cat':dict(name='Amber',source='samples/echo-inspector/DemoAmber.blend',catalog='DemoAmber',material='/Game/PhysicsLab/package_20261015_101957/cat/cat.cat',height_cm=150),
}
def profile(key):
 if key not in PROFILES:raise ValueError('Choose an installed character profile: '+', '.join(PROFILES))
 return PROFILES[key]
