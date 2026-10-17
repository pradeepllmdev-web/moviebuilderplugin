from pathlib import Path
import shutil,datetime
ROOT=Path(__file__).resolve().parents[2];APP=ROOT.parent/'3dobjectnew';stage=ROOT/'implementation/prompt_movie';backup=stage/('backup-'+datetime.datetime.now().strftime('%Y%m%d_%H%M%S'));backup.mkdir()
targets=[(stage/'movie_studio_api.py',APP/'server/movie_studio_api.py'),(stage/'MovieStudio.tsx',APP/'client/src/components/MovieStudio.tsx')]
for src,dst in targets:
 if dst.exists():shutil.copy2(dst,backup/dst.name)
 shutil.copy2(src,dst)
p=APP/'server/main.py';s=p.read_text(encoding='utf-8');shutil.copy2(p,backup/'main.py')
if 'import movie_studio_api' not in s:s=s.replace('app.include_router(environment_production_api.router)','app.include_router(environment_production_api.router)\nimport movie_studio_api\napp.include_router(movie_studio_api.router)')
p.write_text(s,encoding='utf-8')
p=APP/'client/src/App.tsx';s=p.read_text(encoding='utf-8');shutil.copy2(p,backup/'App.tsx')
if "import MovieStudio from" not in s:s="import MovieStudio from './components/MovieStudio'\n"+s
s=s.replace("type TopTab = 'environments'", "type TopTab = 'studio' | 'environments'")
s=s.replace("${topTab === 'environments' && <EnvironmentProduction />}\n        {topTab === 'scenes' ?", "${topTab === 'scenes' ?")
if '>Movie Studio</button>' not in s:s=s.replace('<div className="main-stack">','<div className="main-stack">\n        {topTab === \'studio\' && <MovieStudio />}\n        {topTab === \'environments\' && <EnvironmentProduction />}');s=s.replace('<button className={`tab-btn ${topTab === \'environments\' ?','<button className={`tab-btn ${topTab === \'studio\' ? \'active\' : \'\'}`} onClick={() => setTopTab(\'studio\')}>Movie Studio</button>\n          <button className={`tab-btn ${topTab === \'environments\' ?')
p.write_text(s,encoding='utf-8');print('Installed additive Movie Studio integration; backups:',backup)
