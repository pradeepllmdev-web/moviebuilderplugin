"""Re-test every set piece later: builds each one whose assets exist, prints the AUDIT lines and what is missing.
  python verify_set_pieces.py            all pieces
  python verify_set_pieces.py storm_ship last_egg
Exit code 1 if any build fails or any audit line appears. Preview the results yourself with previs.open_viewer (no mp4)."""
import sys,time
import set_pieces
def main(names):
 bad=0
 for k in names or list(set_pieces.SET_PIECES):
  t=time.time();r=set_pieces.build(k)
  if r['missing']:print(k,'SKIPPED, missing:',*r['missing'],sep='\n  ');continue
  print(k,'OK' if r['ok'] and not r['audit'] else 'PROBLEM','%.0fs'%(time.time()-t),r['out'])
  for line in r['audit']:print('  ',line)
  if not r['ok']:print('  build failed:',r.get('log',''))
  bad+=(not r['ok'])+len(r['audit'])
 return 1 if bad else 0
if __name__=='__main__':sys.exit(main(sys.argv[1:]))
