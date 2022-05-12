# rpr-tent

## Usage

### In Blender UI

1. Open your `.blend` file (with Radeon ProRender enabled).
2. Run or register `src/addon.py`.
3. Open the sidebar panel in **3D Viewport > Sidebar (N) > RPR Tent**:
   - **Reload All Textures**: Reloads linked image textures.
   - **Sort Collections Alphabetically**: Alphabetizes scene outliner collections.
   - **Mount Packaging Labels**: Generates packaging label planes from the labels folder.
   - **Batch Render Cameras**: Renders all cameras (skips cameras prefixed with `!`).

### CLI (Headless)

Run the automated pipeline in Blender background mode:

```bash
blender scene.blend -b -P src/pipeline.py
```

### Python API

```python
from src.pipeline import run_pipeline

run_pipeline(
    load_new_labels=False,
    sort_collections=True,
    do_render=True,
    do_clean_frames=True,
    do_convert=True,
)
```
