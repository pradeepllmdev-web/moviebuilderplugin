"""Validated engine-independent weather contract. Amounts are 0..1 except intensity."""
import math,re
def validate_weather(value=None):
 value={} if value is None else value
 if not isinstance(value,dict):raise ValueError('Weather must be an object')
 kind=value.get('type','none')
 if kind not in ('none','rain','snow'):raise ValueError('Weather type must be none, rain or snow')
 result={'type':kind}
 for key,default,low,high in [('intensity',.6,0,2),('wetness',.7 if kind=='rain' else 0,0,1),('snow_cover',.7 if kind=='snow' else 0,0,1)]:
  number=value.get(key,default)
  if isinstance(number,bool) or not isinstance(number,(int,float)) or not math.isfinite(number) or not low<=number<=high:raise ValueError('Invalid weather '+key)
  result[key]=number
 wind=value.get('wind_cm_s',[30,0])
 if not isinstance(wind,list) or len(wind)!=2 or any(isinstance(x,bool) or not isinstance(x,(int,float)) or not math.isfinite(x) or abs(x)>500 for x in wind):raise ValueError('Wind must be two finite cm/s values between -500 and 500')
 result['wind_cm_s']=wind
 return result

def infer_weather(prompt):
 if re.search(r'\b(no|without) (rain|snow|weather)\b',prompt,re.I):return None
 if re.search(r'\b(snow|snowing|snowy|snowfall|blizzard)\b',prompt,re.I):return validate_weather({'type':'snow'})
 if re.search(r'\b(rain|raining|rainy|rainfall|drizzle|downpour)\b',prompt,re.I):return validate_weather({'type':'rain'})
 return None
