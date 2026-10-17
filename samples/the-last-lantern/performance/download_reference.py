from pathlib import Path
import urllib.request,json
root=Path(__file__).parent.resolve()
files={'reference.mp4':'https://videos.pexels.com/video-files/8550366/8550366-uhd_2160_3840_30fps.mp4','face_landmarker.task':'https://storage.googleapis.com/mediapipe-models/face_landmarker/face_landmarker/float16/latest/face_landmarker.task'}
for name,url in files.items():
    target=root/name
    if not target.is_file():
        request=urllib.request.Request(url,headers={'User-Agent':'Mozilla/5.0','Referer':'https://www.pexels.com/'})
        with urllib.request.urlopen(request,timeout=90) as response,target.open('wb') as output:
            while chunk:=response.read(1024*1024):output.write(chunk)
    print('READY',name,target.stat().st_size,flush=True)
(root/'source.json').write_text(json.dumps({'source':'https://www.pexels.com/video/a-man-talking-and-doing-hand-gestures-8550366/','author':'Kindel Media','license':'Pexels License','license_url':'https://www.pexels.com/license/','use':'movement reference only; no stock audio or raw footage included in the movie','files':files},indent=2))
