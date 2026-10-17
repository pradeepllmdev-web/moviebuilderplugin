"""Two-pass facial landmarks: full-body localization followed by a face crop."""
import asyncio
from PIL import Image
import character3d_api
import face_on_glb
import local_provider

async def detect(src,work,initial=None):
    face=initial or await character3d_api.detect_face(src,work,'front',face_on_glb.facing(src))
    head=face['boxes']['head'];w=head['x1']-head['x0'];h=head['y1']-head['y0']
    bounds=[max(0,head['x0']-.25*w),max(0,head['y0']-.15*h),min(1000,head['x1']+.25*w),min(1000,head['y1']+.55*h)]
    image=Image.open(work/'front.png').convert('RGB');pixels=[round(bounds[0]/1000*image.width),round(bounds[1]/1000*image.height),round(bounds[2]/1000*image.width),round(bounds[3]/1000*image.height)]
    crop=image.crop(pixels).resize((1024,1024));path=work/'face-closeup.png';crop.save(path)
    async with local_provider._client() as client:
        image_id=await character3d_api._upload(client,path)
        job=await local_provider._run_job(client,'/v1/qa/face',{'image_id':image_id},300,'close-up facial landmarks')
    mapped={}
    for name,box in job['result'].items():
        if isinstance(box,dict) and all(k in box for k in ('x0','y0','x1','y1')):
            mapped[name]={**box,'x0':bounds[0]+box['x0']/1000*(bounds[2]-bounds[0]),'x1':bounds[0]+box['x1']/1000*(bounds[2]-bounds[0]),'y0':bounds[1]+box['y0']/1000*(bounds[3]-bounds[1]),'y1':bounds[1]+box['y1']/1000*(bounds[3]-bounds[1])}
        else:mapped[name]=box
    return {**face,'boxes':mapped,'landmark_method':'face-crop-second-pass','crop_bounds':bounds}
