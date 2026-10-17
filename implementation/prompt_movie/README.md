# Main application integration

The new 3dobjectnew Movie Studio tab calls its own backend /api/movie-studio endpoints. That backend proxies the local production service on8521. Character/export adapters reuse blendplugin-next and Unreal bridge8520. Start the existing 3dobjectnew backend and frontend normally, plus environment_library/studio_server.py and the bridge in the existing Unreal editor. Do not launch a second editor for this project.

install_main_app.py was applied with backups of App.tsx and main.py. It adds MovieStudio.tsx/movie_studio_api.py and repairs a misplaced EnvironmentProduction interpolation in the preexisting main navigation. Other screens and routes are retained. The staged files in this directory are the installed sources for the new component/proxy. Original versions of modified files are in the timestamped backup directory and are not committed.

Jobs are stored in moviebuilderplugin/environment_library/scene_jobs and movie_jobs. A successful movie is not yet a row in the legacy 3dobjectnew movie tables; it appears in the new Movie Studio saved gallery. Media are served through the main backend so the user can watch there. Use explicit scene IDs to reopen recorded Unreal levels; the proxy never accepts executable Python.

See environment_library/SCENE_PROMPTS.md for current supported actions and limitations.
