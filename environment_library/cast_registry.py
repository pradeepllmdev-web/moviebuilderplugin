"""Character variety on the single lion rig (pure Python, no Blender): named characters with a species look, proportions, tint, accessories, posture/gait and voice, kept in a registry other tools can feed and read.

    import cast_registry as cr
    reg=cr.Registry(); reg.add(dict(id='mara',name='Mara',species='fox',accessories=['scarf','satchel'],posture='jaunty',voice_pitch=190))
    look=reg.resolve('mara')           # everything the builder needs: scale (sx,sy,sz), tint, parts, gait, pitch
    reg.save('cast.json'); cr.Registry.load('cast.json')
    cr.from_series_character({'name':'Old Bram','details':'a gruff old bear with a wizard hat and a staff','character_type':'animal'})   # a record of the sibling 3dobjectnew repo -> a registry entry
    reg.export_story_records()          # [{name, description, species, ...}] for tools that keep story data

The look of a character is a SPECIES (proportions, tint, body parts: ears, horns, ruff, tusks, tail tuft) overridden field by field by the character's own record, plus ACCESSORIES from a catalogue (hat, cape, scarf, staff, ...); the Blender side (cast_builder.py) builds
parts and accessories from primitives on the rig's head, spine, hip and hand bones. `scale` is (width, depth, height) relative to the lion (1.71 m tall): the builder sets it on the unscaled root empty, so no child of a scaled parent needs correcting.
Gait: the posture word picks the walking gait (gaits.POSTURE_GAIT) and pace multiplies its speed; voice_pitch (Hz) feeds the synthesised voice (dialogue.pitch_of is replaced per character)."""
import json,re,hashlib
LION_HEIGHT=1.71
POSTURES=('neutral','proud','tired','jaunty','tense','angry','hurried','hunched')
BODY_PARTS=('ears','horns','ruff','tusks','tuft','beak')
# species: height m, width and depth factors, tint (multiplies the lion's colour), parts, default posture, voice range
SPECIES={
 'lion':   dict(height=1.71,width=1.0, depth=1.0, tint=(1.0,1.0,1.0),parts=[],posture='proud',pitch=(95,120)),
 'bear':   dict(height=1.95,width=1.3, depth=1.2, tint=(.55,.38,.26),parts=[dict(kind='ears',shape='round',size=.9,color=(.4,.27,.18))],posture='tired',pitch=(70,95)),
 'fox':    dict(height=1.5, width=.82,depth=.9,  tint=(1.0,.5,.22),parts=[dict(kind='ears',shape='point',size=1.2,color=(.95,.45,.18)),dict(kind='tuft',size=1.,color=(.97,.95,.9))],posture='jaunty',pitch=(180,230)),
 'rabbit': dict(height=1.25,width=.75,depth=.8,  tint=(.92,.9,.85),parts=[dict(kind='ears',shape='long',size=1.3,color=(.9,.8,.78))],posture='hurried',pitch=(200,250)),
 'ox':     dict(height=2.0, width=1.35,depth=1.25,tint=(.45,.4,.36),parts=[dict(kind='horns',shape='curve',size=1.,color=(.9,.86,.75)),dict(kind='ears',shape='side',size=.8,color=(.4,.34,.3))],posture='tense',pitch=(60,85)),
 'owl':    dict(height=1.4, width=.85,depth=.85, tint=(.66,.55,.42),parts=[dict(kind='ears',shape='tuft',size=1.,color=(.5,.4,.3)),dict(kind='beak',size=1.,color=(.95,.75,.2))],posture='proud',pitch=(130,170)),
 'wolf':   dict(height=1.85,width=.95,depth=1.0, tint=(.55,.58,.64),parts=[dict(kind='ears',shape='point',size=1.0,color=(.45,.47,.52))],posture='tense',pitch=(75,100)),
 'mouse':  dict(height=1.05,width=.65,depth=.7,  tint=(.78,.72,.66),parts=[dict(kind='ears',shape='disc',size=1.5,color=(.95,.75,.75))],posture='hurried',pitch=(230,290)),
 'heron':  dict(height=2.3, width=.7, depth=.75, tint=(.7,.78,.88),parts=[dict(kind='beak',size=1.4,color=(.95,.8,.3))],posture='proud',pitch=(140,175)),
 'badger': dict(height=1.4, width=1.25,depth=1.1,tint=(.38,.38,.4),parts=[dict(kind='ears',shape='round',size=.7,color=(.3,.3,.32)),dict(kind='tuft',size=.8,color=(.95,.95,.95))],posture='angry',pitch=(85,110)),
 'boar':   dict(height=1.55,width=1.3, depth=1.2, tint=(.62,.42,.4),parts=[dict(kind='tusks',size=1.,color=(.96,.94,.86)),dict(kind='ears',shape='side',size=.9,color=(.55,.38,.36))],posture='angry',pitch=(75,100)),
 'cat':    dict(height=1.45,width=.8, depth=.85, tint=(.4,.4,.5),parts=[dict(kind='ears',shape='point',size=.9,color=(.35,.35,.42))],posture='jaunty',pitch=(160,210)),
 'elder':  dict(height=1.55,width=.9, depth=.9,  tint=(.85,.82,.78),parts=[dict(kind='ruff',size=.85,color=(.95,.95,.95))],posture='hunched',pitch=(100,130)),
}
# accessory catalogue: where it attaches (rig bone) and what it is made of (the builder owns the geometry)
ACCESSORIES={
 'hat_top':('head','top hat'),'hat_wizard':('head','pointed wizard hat'),'hat_cap':('head','soft cap with a peak'),'hat_straw':('head','wide straw hat'),'crown':('head','gold crown'),'helmet':('head','round helmet with a crest'),
 'glasses':('head','round spectacles'),'eyepatch':('head','eye patch'),'flower':('head','flower behind the ear'),
 'scarf':('neck','scarf with a hanging end'),'bowtie':('neck','bow tie'),'cape':('spine','short cape'),'backpack':('spine','pack on the back'),'apron':('spine','apron'),'medals':('spine','row of medals'),
 'belt':('hips','belt with a buckle'),'satchel':('hips','side satchel'),'sword':('hips','sword on the hip'),
 'shirt':('spine','fitted shirt cut from the body'),
 'sleeves':('limbs','long sleeves with cuffs'),'shortsleeves':('limbs','short sleeves'),'pants':('limbs','trousers with cuffs'),'shorts':('limbs','short trousers'),'boots':('limbs','boots'),'gloves':('limbs','gloves'),
 'tunic':('spine','tunic with a trim at the hem'),'dress':('hips','dress with a flared skirt'),'robe':('spine','long robe'),'vest':('spine','open vest'),'overalls':('spine','overalls with a bib'),'poncho':('spine','poncho'),'armor':('spine','breastplate with shoulder plates'),
 'tshirt':('spine','t-shirt'),'jacket':('spine','jacket with an open front'),'suit':('spine','suit: jacket, white shirt and trousers'),'plaidshirt':('spine','plaid shirt'),'stripedshirt':('spine','striped shirt'),'kilt':('hips','pleated kilt'),'tie':('neck','necktie'),
 'hat_flatcap':('head','flat cap'),'hat_cowboy':('head','wide curled hat'),'hat_sou':('head','rain hat with a long back brim'),'hat_beanie':('head','knitted beanie with a pompom'),'hat_beret':('head','beret'),'hat_chef':('head','tall chef hat'),'hat_hood':('head','cloth hood'),'hat_bonnet':('head','village bonnet'),
 'staff':('hand_r','tall staff in the right hand'),'cane':('hand_r','walking cane'),'lantern':('hand_l','lantern in the left hand'),'banner':('hand_r','small banner on a pole'),
}
# an OUTFIT is a named costume: clothing plus the pieces that go with it; rec['outfit']='knight' (and rec['colors']=[main, trim, ...]) expands to accessories, so different characters of the same species read apart at a glance
OUTFITS={'baker':['apron:1','hat_straw:0','sleeves:0','pants:2','boots:3'],'queen':['dress:0','sleeves:0','crown','cape:1','boots:2'],'king':['shirt:0','sleeves:0','pants:1','boots:2','crown','cape:1','belt'],'knight':['armor:0','sleeves:1','pants:1','boots:2','helmet','sword','cape:0'],
 'farmer':['overalls:0','sleeves:1','boots:2','hat_straw'],'wizard':['robe:0','sleeves:0','hat_wizard:0','staff','boots:1'],'merchant':['vest:0','sleeves:1','pants:2','boots:3','satchel','hat_top:0'],'peasant':['shirt:0','sleeves:1','pants:2','belt','boots:3'],
 'scout':['poncho:0','pants:1','boots:2','hat_cap:0','satchel'],'sailor':['vest:0','sleeves:1','pants:0','hat_cap:1','scarf:2','boots:3'],'scholar':['robe:0','sleeves:0','glasses','satchel','boots:1'],'guard':['shirt:0','sleeves:1','pants:1','boots:2','helmet','sword','belt'],
 'noble':['vest:0','sleeves:1','pants:2','boots:3','cape:0','bowtie'],'traveller':['poncho:0','pants:1','boots:2','backpack','scarf:0'],'mother':['dress:0','sleeves:0','apron:1','boots:2'],'child':['shirt:0','sleeves:1','shorts:2','boots:3'],
 'villager':['plaidshirt:0','vest:1','pants:2','boots:3','hat_flatcap:1'],'villageress':['dress:0','apron:1','boots:2','hat_bonnet:1'],'blacksmith':['tshirt:0','apron:1','gloves:2','pants:3','boots:2','belt'],'fisherman':['stripedshirt:0','jacket:1','pants:2','boots:1','hat_sou:1'],
 'shepherd':['tunic:0','sleeves:1','pants:2','boots:3','hat_beanie:1','staff'],'innkeeper':['shirt:0','vest:1','apron:2','pants:3','boots:3'],'miller':['tshirt:0','overalls:1','boots:2','hat_flatcap:1'],'monk':['robe:0','belt','hat_hood:0'],
 'mayor':['suit:0','tie:1','boots:2','hat_top:0','cane'],'gentleman':['suit:0','tie:1','boots:2','hat_flatcap:3'],'tourist':['tshirt:0','shorts:1','hat_cowboy:2','satchel','boots:3','glasses'],'cook':['tshirt:0','apron:1','pants:2','boots:3','hat_chef'],
 'highlander':['shirt:0','kilt:1','boots:2','hat_beret:1','sleeves:0'],'cowboy':['plaidshirt:0','vest:1','pants:2','boots:3','hat_cowboy:3','scarf:1','belt'],'artist':['tshirt:0','overalls:1','hat_beret:2','scarf:3','boots:3']}
def expand_outfit(rec):
 """accessories of a record with its outfit expanded: each piece 'kind' or 'kind:i' takes colour i of rec['colors'] (a piece that already names a colour keeps it; no colour = the accessory palette)"""
 acc=[];cols=rec.get('colors') or []
 for k,tok in enumerate(OUTFITS.get(rec.get('outfit'),[])):
  kind,_,idx=tok.partition(':');i=int(idx) if idx else k;col=cols[i%len(cols)] if cols else None
  acc.append(dict(kind=kind,color=col) if col else kind)
 return acc+list(rec.get('accessories',[]))
GAIT_BY_POSTURE={'neutral':'walk','proud':'strut','tired':'shuffle','jaunty':'bounce','tense':'sneak','angry':'stomp','hurried':'brisk','hunched':'shuffle'}
KEYWORDS={   # description words -> species / accessories / colour / posture, used by from_series_character
 'species':{'lion':r'lion|lioness','bear':r'\bbears?\b','fox':r'\bfox|vixen','rabbit':r'rabbit|hare|bunny','ox':r'\box\b|bull|bison|buffalo|cow','owl':r'\bowl','wolf':r'wolf|wolves|hound','mouse':r'mouse|mice|rat\b|hamster','heron':r'heron|crane|stork|ostrich|giraffe','badger':r'badger|wolverine|otter','boar':r'boar|pig|hog','cat':r'\bcat\b|kitten|panther|lynx','elder':r'\belder|ancient|sage'},
 'accessories':{'hat_wizard':r'wizard|sorcer|mage','hat_top':r'top hat|gentleman|banker|magician','hat_cap':r'\bcap\b|beret|messenger|paperboy','hat_straw':r'straw hat|farmer|gardener','crown':r'crown|king|queen|princess|prince','helmet':r'helmet|knight|soldier|guard|captain','glasses':r'glasses|spectacles|scholar|professor|clerk','eyepatch':r'eye ?patch|pirate','scarf':r'scarf|scarves','bowtie':r'bow ?tie|waiter','cape':r'\bcape|cloak|hero','backpack':r'backpack|rucksack|traveller|traveler|explorer|hiker','apron':r'apron|baker|cook|smith|chef','medals':r'medal|general|admiral','belt':r'\bbelt\b|bandit','satchel':r'satchel|bag\b|courier|merchant|trader|peddler','sword':r'sword|blade|swordsman|duellist','staff':r'staff|wizard|shepherd|pilgrim','cane':r'cane|old man|old woman|gaffer|grandfather','lantern':r'lantern|lamp|watchman|lighthouse','banner':r'banner|herald|flag'},
 'posture':{'angry':r'angry|gruff|grumpy|furious|bully|short-tempered','tense':r'nervous|wary|cautious|thief|sneaky|secretive','proud':r'proud|noble|regal|vain|boastful','jaunty':r'cheerful|playful|jaunty|merry|trickster|cheeky','hurried':r'hurried|anxious|busy|restless|fussy','hunched':r'hunched|bent|frail|stooped','tired':r'tired|weary|old\b|slow|sleepy'},
 'tint':{'red':(1,.45,.35),'orange':(1,.6,.25),'golden':(1,.85,.45),'yellow':(1,.9,.4),'green':(.5,.8,.45),'blue':(.45,.6,.95),'purple':(.7,.5,.9),'pink':(1,.65,.75),'white':(.95,.95,.95),'grey':(.6,.62,.65),'gray':(.6,.62,.65),'black':(.25,.25,.28),'dark':(.4,.38,.38),'brown':(.6,.42,.3)},
}
def slug(name):return re.sub(r'[^a-z0-9]+','_',name.lower()).strip('_') or 'x'
def hash_unit(text,salt=''):
 h=int(hashlib.sha1((salt+text).encode()).hexdigest()[:8],16);return (h%10000)/10000.
class CastError(ValueError):pass
def validate(rec):
 """list of problems with a character record (empty list = valid)"""
 out=[]
 if not rec.get('id') or not re.fullmatch(r'[a-z][a-z0-9_]{0,23}',rec['id']):out.append('id must be lowercase letters, digits, underscore')
 if not rec.get('name'):out.append('name missing')
 sp=rec.get('species','lion')
 if sp not in SPECIES:out.append('unknown species %r'%sp)
 if rec.get('outfit') and rec['outfit'] not in OUTFITS:out.append('unknown outfit %r (known: %s)'%(rec['outfit'],', '.join(sorted(OUTFITS))))
 for a in expand_outfit(rec) if rec.get('outfit') in OUTFITS else rec.get('accessories',[]):
  if (a if isinstance(a,str) else a.get('kind')) not in ACCESSORIES:out.append('unknown accessory %r'%(a,))
 if rec.get('posture','neutral') not in POSTURES:out.append('unknown posture %r'%rec.get('posture'))
 t=rec.get('tint')
 if t is not None and not (len(t)==3 and all(0<=x<=2 for x in t)):out.append('tint must be three numbers in 0..2')
 h=rec.get('height')
 if h is not None and not .5<=h<=3.2:out.append('height %.2f m outside 0.5..3.2'%h)
 p=rec.get('voice_pitch')
 if p is not None and not 50<=p<=400:out.append('voice_pitch outside 50..400 Hz')
 if not .5<=rec.get('pace',1.)<=1.5:out.append('pace outside 0.5..1.5')
 heads=[a for a in (expand_outfit(rec) if rec.get('outfit') in OUTFITS else rec.get('accessories',[])) if ACCESSORIES.get(a if isinstance(a,str) else a.get('kind'),('',))[0]=='head' and (a if isinstance(a,str) else a.get('kind')).startswith(('hat','crown','helmet'))]
 if len(heads)>1:out.append('more than one hat/crown/helmet')
 return out
def _acc(a):
 return dict(kind=a,color=None) if isinstance(a,str) else {**dict(color=None),**a}
def resolve(rec):
 """the full look: scale (sx,sy,sz), tint, parts (species parts overridden by kind), accessories, gait, pitch, pace"""
 bad=validate(rec)
 if bad:raise CastError('%s: %s'%(rec.get('id'),'; '.join(bad)))
 sp=SPECIES[rec.get('species','lion')];h=rec.get('height',sp['height']);sz=h/LION_HEIGHT
 w=rec.get('width',sp['width']);d=rec.get('depth',sp['depth']);tint=tuple(rec.get('tint',sp['tint']))
 parts={p['kind']:dict(p) for p in sp['parts']}
 for p in rec.get('parts',[]):parts[p['kind']]=dict(parts.get(p['kind'],{}),**p)
 for k in rec.get('no_parts',[]):parts.pop(k,None)
 posture=rec.get('posture',sp['posture']);lo,hi=sp['pitch'];pitch=rec.get('voice_pitch',lo+(hi-lo)*hash_unit(rec['id'],'pitch'))
 acc=[_acc(a) for a in expand_outfit(rec)]
 return dict(id=rec['id'],name=rec['name'],species=rec.get('species','lion'),height=h,scale=(round(w*sz,4),round(d*sz,4),round(sz,4)),tint=tint,parts=list(parts.values()),accessories=acc,posture=posture,gait=GAIT_BY_POSTURE[posture],pace=rec.get('pace',1.),pitch=pitch,voice=rec.get('voice'),
  reach=.55*sz,radius=round(max(w,d)*sz*.38,3))
def from_series_character(rec):
 """a character of the sibling 3dobjectnew repo ({'name','details'|'description','character_type'}) -> a registry entry guessed from its words; nothing in that repo is touched"""
 name=rec.get('name') or 'Nameless';text=' '.join(str(rec.get(k) or '') for k in ('details','description','character_type'));low=text.lower()
 sp=next((s for s,pat in KEYWORDS['species'].items() if re.search(pat,low)),None)
 if sp is None:sp=sorted(SPECIES)[int(hash_unit(name,'species')*len(SPECIES))%len(SPECIES)]
 acc=[a for a,pat in KEYWORDS['accessories'].items() if re.search(pat,low)]
 heads=[a for a in acc if a.startswith(('hat','crown','helmet'))]
 acc=[a for a in acc if a not in heads[1:]][:3]
 post=next((p for p,pat in KEYWORDS['posture'].items() if re.search(pat,low)),None)
 out=dict(id=slug(name),name=name,species=sp,accessories=acc,description=text.strip(),source='series_character')
 if post:out['posture']=post
 for word,col in KEYWORDS['tint'].items():
  if re.search(r'\b%s\b'%word,low):out['tint']=list(col);break
 if re.search(r'\b(tall|giant|huge|towering)\b',low):out['height']=SPECIES[sp]['height']*1.15
 if re.search(r'\b(small|little|tiny|short|young|cub|kid|child)\b',low):out['height']=SPECIES[sp]['height']*.82
 if re.search(r'\b(fat|stout|round|heavy|broad)\b',low):out['width']=SPECIES[sp]['width']*1.2
 if re.search(r'\b(thin|slim|lean|slender|skinny)\b',low):out['width']=SPECIES[sp]['width']*.82
 return out
class Registry:
 def __init__(self,records=None):
  self.rec={}
  for r in records or []:self.add(r)
 def add(self,rec):
  rec=dict(rec);bad=validate(rec)
  if bad:raise CastError('%s: %s'%(rec.get('id'),'; '.join(bad)))
  self.rec[rec['id']]=rec;return rec['id']
 def get(self,id_):
  if id_ not in self.rec:raise KeyError('no character %r (known: %s)'%(id_,', '.join(sorted(self.rec))))
  return self.rec[id_]
 def resolve(self,id_):return resolve(self.get(id_))
 def ids(self):return list(self.rec)
 def merge(self,other):
  """records of another registry win; returns the ids that were replaced"""
  rep=[i for i in other.rec if i in self.rec];[self.add(r) for r in other.rec.values()];return rep
 def distinct_report(self):
  """how apart the characters look: pairs whose silhouette (scale), tint, parts and accessories are all alike (a casting audit)"""
  out=[];rs={i:self.resolve(i) for i in self.rec};ids=list(rs)
  for a in range(len(ids)):
   for b in range(a+1,len(ids)):
    A,B=rs[ids[a]],rs[ids[b]];ds=sum(abs(x-y)/max(x,y) for x,y in zip(A['scale'],B['scale']));dt=sum(abs(x-y) for x,y in zip(A['tint'],B['tint']))
    da=len({x['kind'] for x in A['accessories']}^{x['kind'] for x in B['accessories']});dp=len({p['kind']+p.get('shape','') for p in A['parts']}^{p['kind']+p.get('shape','') for p in B['parts']})
    score=ds*2+dt+.25*da+.25*dp
    if score<.6:out.append((ids[a],ids[b],round(score,2)))
  return out
 def to_json(self):return json.dumps(dict(version=1,characters=list(self.rec.values())),indent=1)
 def save(self,path):
  with open(path,'w',encoding='utf-8') as f:f.write(self.to_json())
 @classmethod
 def load(cls,path):
  with open(path,encoding='utf-8') as f:d=json.load(f)
  return cls(d['characters'])
 def export_story_records(self):
  """flat records for story/character tools (the shape the sibling repo keeps: name + a text description) with the structured look attached"""
  out=[]
  for i,r in self.rec.items():
   L=self.resolve(i);desc=r.get('description') or '%s, a %s%s'%(r['name'],L['species'],(' with '+', '.join(ACCESSORIES[a['kind']][1] for a in L['accessories'])) if L['accessories'] else '')
   out.append(dict(name=r['name'],id=i,description=desc,species=L['species'],height_m=round(L['height'],2),posture=L['posture'],accessories=[a['kind'] for a in L['accessories']],tint=list(L['tint']),voice_pitch_hz=round(L['pitch'])))
  return out
