"""Authors the three 15-minute test stories (scenes/story_<name>.txt): scene types in dramatic order plus hand-written dialogue scenes; each paragraph is checked to select its intended scene type."""
import set_pieces,story_plan,story_writer as sw
def D(setting,*lines):return setting+'\n'+'\n'.join('%s (%s): "%s"'%l for l in lines)
STORIES={
'egg_run':('The Last Egg: Leo and Pip carry a stolen dinosaur egg home across the old world',
 ['council',D('Around the campfire Leo and Pip plan the long road to the valley of the sun.',('Pip','concern','If the egg gets cold before we reach the valley it will never hatch.'),('Leo','serious','Then we do not rest until it is warm.'),('Pip','warm','You carry the egg and I will watch the road.')),
  'workshop','rapids','jungle','ruins',D('Around the campfire Pip warms the egg while Leo sharpens the quest map.',('Pip','sad','I heard the egg thieves behind us on the river road.'),('Leo','angry','Then they will meet me at the bridge.'),('Pip','concern','Be careful, Leo. They are many.')),
  'swamp','last_egg','horse_herd','rider','avalanche','cliff_rescue',D('Around the campfire the travellers rest after the mountain and the egg begins to glow.',('Leo','joy','Look, the egg is glowing. It knows we are close!'),('Pip','joy','Then we must reach the valley before sunrise.'),('Leo','warm','We will, my friend.')),
  'flood','bridge','storm_ship','ice','flight','sky','colossus','arena_duel',D('Around the campfire at dawn Leo and Pip watch the egg crack open.',('Pip','joy','It is hatching, Leo. It is really hatching!'),('Leo','warm','Welcome to the world, little one.'),('Pip','warm','You brought it home.'))]),
'clockwork':('The Clockwork Heist: Leo and Mara steal the star crown from the clockwork tower',
 ['market',D('At night in the busy market Leo and Mara plan the heist of the star crown.',('Mara','serious','The crown sits in the clockwork tower behind three locked gates.'),('Leo','warm','Then we open them one by one.'),('Mara','concern','The guards change at midnight. We have one chance.')),
  'workshop','heist','great_escape','rider',D('Around the campfire Mara counts the clockwork keys while Leo watches the road.',('Mara','serious','Two keys are copied and one is missing.'),('Leo','concern','The missing key is in the tower itself.'),('Mara','joy','Then we steal it from under their noses!')),
  'siege','observatory','forge','ruins','bridge',D('At the old council table Leo and Mara study the plans of the tower again.',('Leo','serious','The back stair is our way in and out.'),('Mara','angry','And the Rival will be waiting at the top.'),('Leo','warm','Then we will give him a surprise.')),
  'jungle','reef','swamp','avalanche','cliff_rescue','rapids','sky','flight','duel',D('Around the campfire after the heist Leo and Mara look at the crown in the firelight.',('Mara','joy','We did it. We really did it!'),('Leo','warm','Together we always do.'),('Mara','sad','Now we have to give it back to the valley.'))]),
'storm_crossing':('Storm Crossing: Leo and Tarn bring the village boat through the great storm',
 ['storm_ship',D('Around the campfire in the harbour Leo and Tarn read the storm map.',('Tarn','concern','The storm is coming from the north and the boat is not ready.'),('Leo','serious','Then we make it ready tonight.'),('Tarn','warm','You steer and I will mend the sail.')),
  'workshop','reef','rapids','flood',D('Around the campfire the travellers shelter from the rain after the flood.',('Tarn','sad','The river took the old bridge and half the village road.'),('Leo','serious','Then we build a new one together.'),('Tarn','warm','The village is lucky to have you.')),
  'cliff_rescue','avalanche','ice','forge','swamp',D('At the old council table Leo and Tarn plan the last crossing of the storm.',('Leo','serious','The great wave comes at midnight.'),('Tarn','concern','Then the boat must be at the bridge before it.'),('Leo','angry','It will be.')),
  'jungle','ruins','bridge','market','heist','horse_herd','sky','colossus','last_egg',D('Around the campfire at dawn the village gathers and the storm finally breaks.',('Tarn','joy','We made it, Leo. The whole village is safe!'),('Leo','joy','Because we crossed it together.'),('Tarn','warm','Now we can rest at last.'))]),
}
def build():
 out={}
 for name,(title,items) in STORIES.items():
  paras=[];total=0;bad=[]
  for it in items:
   if it in sw.SENT:p=sw.SENT[it];want=it
   else:p=it;want='talk'
   m=set_pieces.match(p)
   if not m or m[0]!=want:bad.append((want,m[:2]))
   total+=story_plan.DEFAULT_SECONDS.get(want,40);paras.append(p)
  open('scenes/story_%s.txt'%name,'w',encoding='utf-8').write('\n\n'.join(paras)+'\n');out[name]=(len(paras),round(total/60.,1),bad)
 return out
if __name__=='__main__':
 for k,v in build().items():print(k,v)
