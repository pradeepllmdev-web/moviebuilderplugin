"""Extract small face ratios from an image. No raw landmark arrays are saved."""
import argparse,hashlib,json,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT))
from movie_production.appearance import targets_from_ratios,validate_preset

def create(image,output,name):
    import cv2,mediapipe as mp,numpy as np
    from mediapipe.tasks import python
    from mediapipe.tasks.python import vision
    pixels=cv2.imread(str(image))
    if pixels is None:raise ValueError('Unreadable image')
    height,width=pixels.shape[:2]
    options=vision.FaceLandmarkerOptions(base_options=python.BaseOptions(model_asset_path=str(ROOT/'samples/the-last-lantern/performance/face_landmarker.task')),
        running_mode=vision.RunningMode.IMAGE,num_faces=2,min_face_detection_confidence=.5)
    with vision.FaceLandmarker.create_from_options(options) as detector:
        result=detector.detect(mp.Image(image_format=mp.ImageFormat.SRGB,data=cv2.cvtColor(pixels,cv2.COLOR_BGR2RGB)))
        if not result.face_landmarks:
            # Full-body references have a small face. Retry an upper-center analysis window.
            pixels=pixels[:int(height*.42),int(width*.2):int(width*.8)]
            height,width=pixels.shape[:2]
            result=detector.detect(mp.Image(image_format=mp.ImageFormat.SRGB,data=cv2.cvtColor(pixels,cv2.COLOR_BGR2RGB)))
    if len(result.face_landmarks)!=1:raise ValueError('Expected one clearly visible face')
    points=np.array([(landmark.x*width,landmark.y*height) for landmark in result.face_landmarks[0]])
    distance=lambda a,b:float(np.linalg.norm(points[a]-points[b]))
    face_width=distance(234,454)
    ratios={'eye_width':(distance(33,133)+distance(362,263))/(2*face_width),
        'nose_width':distance(98,327)/face_width,'mouth_width':distance(61,291)/face_width,
        'chin_width':distance(172,397)/face_width,'face_aspect':distance(10,152)/face_width}
    # This first experiment uses explicit, reviewed art direction for non-geometric traits.
    preset={'schema':'image-mpfb-preset/1','character_id':name,'reference_image':str(image.resolve()),
        'reference_sha256':hashlib.sha256(image.read_bytes()).hexdigest(),
        'analysis':'MediaPipe image landmarks; heuristic proportion mapping; manually selected hair/clothing palette',
        'ratios':{key:round(value,5) for key,value in ratios.items()},'targets':targets_from_ratios(ratios),
        'macro':{'gender':0.,'age':.38,'muscle':.35},'skin':'young_caucasian_female.mhmat',
        'hair':'short01.mhclo','outfit':'male_casualsuit01.mhclo','shoes':'shoes01.mhclo',
        'art_direction':{'hair':'dark brown','outfit':'teal top, tan trousers',
            'limitations':'Existing assets approximate the reference; hairstyle and jacket are not reconstructed.'}}
    validate_preset(preset);output.parent.mkdir(parents=True,exist_ok=True)
    output.write_text(json.dumps(preset,indent=2));print(json.dumps({'preset':str(output),'ratios':preset['ratios'],'target_count':len(preset['targets'])}))

if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--image',type=Path,required=True)
    parser.add_argument('--output',type=Path,required=True);parser.add_argument('--name',default='mira-template')
    args=parser.parse_args();create(args.image,args.output,args.name)
