"""Capture a typed reference bank; keep landmarks internal and emit small QA reports."""
import argparse,json,sys
from pathlib import Path
import cv2,mediapipe as mp,numpy as np
from scipy.spatial.transform import Rotation
from scipy.signal import savgol_filter

BODY_NAMES=['Hips','Spine','Spine1','Spine2','Neck','Head','LeftShoulder','LeftArm','LeftForeArm','LeftHand','RightShoulder','RightArm','RightForeArm','RightHand']

def bone_frame(aim,forward):
    y=aim/(np.linalg.norm(aim)+1e-9);z=forward-y*np.dot(y,forward)
    if np.linalg.norm(z)<.001:z=np.cross(y,[1,0,0])
    z/=np.linalg.norm(z)+1e-9;x=np.cross(y,z)
    return Rotation.from_matrix(np.stack([x,y,z],axis=1)).as_quat()[[3,0,1,2]]

def upper_body(points):
    p=points;up=(p[11]+p[12]-p[23]-p[24])/2
    forward=np.cross(p[11]-p[12],up);forward/=np.linalg.norm(forward)+1e-9
    out={name:bone_frame(up,forward) for name in BODY_NAMES}
    for side,sh,el,wr,ix,pi in [('Left',11,13,15,19,17),('Right',12,14,16,20,18)]:
        out[side+'Arm']=bone_frame(p[el]-p[sh],forward)
        out[side+'ForeArm']=bone_frame(p[wr]-p[el],forward)
        out[side+'Hand']=bone_frame((p[ix]+p[pi])/2-p[wr],forward)
    return np.array([out[name] for name in BODY_NAMES])

def rest_body():
    up=np.array([0.,0.,1.]);forward=np.array([0.,-1.,0.])
    result=[]
    for name in BODY_NAMES:
        aim=np.array([1.,0.,0.]) if name.startswith('Left') and name not in ('LeftShoulder',) else np.array([-1.,0.,0.]) if name.startswith('Right') and name not in ('RightShoulder',) else up
        result.append(bone_frame(aim,forward))
    return np.array(result)

def fill_gaps(values,valid):
    values=np.asarray(values,float);index=np.arange(len(values));good=index[np.asarray(valid,bool)]
    if len(good)<10:raise ValueError('Not enough tracked frames')
    flat=values.reshape(len(values),-1)
    for col in range(flat.shape[1]):flat[:,col]=np.interp(index,good,flat[good,col])
    return flat.reshape(values.shape)

def capture(name,item,root,pose_model,face_model):
    video=cv2.VideoCapture(str(root/item['file']));source_fps=video.get(cv2.CAP_PROP_FPS) or 30
    base=mp.tasks.BaseOptions;vision=mp.tasks.vision
    if item['capture']=='body':
        detector=vision.PoseLandmarker.create_from_options(vision.PoseLandmarkerOptions(base_options=base(model_asset_path=str(pose_model)),running_mode=vision.RunningMode.VIDEO,num_poses=1))
    else:
        detector=vision.FaceLandmarker.create_from_options(vision.FaceLandmarkerOptions(base_options=base(model_asset_path=str(face_model)),running_mode=vision.RunningMode.VIDEO,num_faces=1,output_face_blendshapes=True,output_facial_transformation_matrixes=True))
    values=[];valid=[];times=[];extra=[];index=0
    with detector:
        while index/source_fps<18:
            ok,frame=video.read()
            if not ok:break
            t=index/source_fps;index+=1
            if item['capture']=='body' and len(times) and t-times[-1]<1/24-.002:continue
            size=min(1,960/max(frame.shape[:2]));frame=cv2.resize(frame,None,fx=size,fy=size)
            image=mp.Image(image_format=mp.ImageFormat.SRGB,data=cv2.cvtColor(frame,cv2.COLOR_BGR2RGB))
            result=detector.detect_for_video(image,round(t*1000));times.append(t)
            if item['capture']=='body':
                found=bool(result.pose_world_landmarks)
                if found:
                    pts=result.pose_world_landmarks[0];confidence=min(pts[j].visibility for j in (11,12,13,14,15,16));found=confidence>.45
                    p=np.array([[point.x,point.z,-point.y] for point in pts]);values.append(p)
                else:values.append(np.zeros((33,3)))
                valid.append(found)
            else:
                found=bool(result.facial_transformation_matrixes)
                if found:
                    matrix=np.array(result.facial_transformation_matrixes[0])[:3,:3]
                    values.append(Rotation.from_matrix(matrix).as_euler('xyz'))
                    blend={b.category_name:float(b.score) for b in result.face_blendshapes[0]}
                else:values.append(np.zeros(3));blend={}
                extra.append([max(blend.get('eyeBlinkLeft',0),blend.get('eyeBlinkRight',0)),max(blend.get('browInnerUp',0),blend.get('browOuterUpLeft',0),blend.get('browOuterUpRight',0)),(blend.get('mouthSmileLeft',0)+blend.get('mouthSmileRight',0))/2,(blend.get('eyeLookOutLeft',0)-blend.get('eyeLookInLeft',0)+blend.get('eyeLookInRight',0)-blend.get('eyeLookOutRight',0))/2])
                valid.append(found)
    video.release();coverage=sum(valid)/max(1,len(valid))
    if coverage<.80:raise ValueError(f'{name}: tracking coverage only {coverage:.1%}')
    values=fill_gaps(values,valid);times=np.array(times)
    data={'time':times,'valid':np.array(valid),'types':np.array(item['types'])}
    if item['capture']=='body':
        values=savgol_filter(values,7,2,axis=0)
        quats=np.array([upper_body(p) for p in values])
        for i in range(1,len(quats)):
            mask=(quats[i]*quats[i-1]).sum(axis=1)<0;quats[i,mask]*=-1
        data.update(names=np.array(BODY_NAMES),quaternions=quats,rest=rest_body())
    else:
        values=np.unwrap(values,axis=0);values=savgol_filter(values,7,2,axis=0)
        values-=np.median(values,axis=0)
        data.update(head_angles=values,expression=fill_gaps(extra,valid))
    np.savez_compressed(root/(name+'.npz'),**data)
    report={'reference':name,'types':item['types'],'frames':len(times),'duration':float(times[-1]),'tracking_coverage':coverage,'source_fps':source_fps,'source':item['source'],'author':item['author'],'status':'captured; retarget/visual review still required'}
    if item['capture']=='face':report['head_angle_range_degrees']=np.degrees(np.ptp(values,axis=0)).tolist()
    (root/(name+'-capture.json')).write_text(json.dumps(report,indent=2));print('CAPTURED',json.dumps(report),flush=True)

if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--bank',required=True);parser.add_argument('--only');args=parser.parse_args();path=Path(args.bank).resolve();bank=json.loads(path.read_text())
    for name,item in bank['references'].items():
        if args.only and name!=args.only:continue
        capture(name,item,path.parent,Path('C:/Users/nagal/mocap/mediapipe/pose_landmarker_heavy.task'),path.parent/'face_landmarker.task')
