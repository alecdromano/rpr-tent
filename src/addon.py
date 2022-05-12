"""RPR Tent Blender Add-on / Operator interface.

Allows registering operators into Blender UI or running from the Text Editor.
"""

bl_info = {
    "name": "RPR Tent - Product Photography Pipeline",
    "author": "RPR Tent Contributors",
    "version": (0, 1, 0),
    "blender": (2, 93, 0),
    "location": "View3D > Sidebar > RPR Tent",
    "description": "Batch rendering, label mounting, and product photography toolkit for Radeon ProRender in Blender.",
    "category": "Render",
}


def register():
    try:
        import bpy
    except ImportError:
        return

    class RPR_TENT_OT_reload_textures(bpy.types.Operator):
        bl_idname = "rpr_tent.reload_textures"
        bl_label = "Reload All Textures"
        bl_description = "Reload external image textures"

        def execute(self, context):
            from src.textures import reload_images
            count = len(reload_images())
            self.report({"INFO"}, f"Reloaded {count} texture(s).")
            return {"FINISHED"}

    class RPR_TENT_OT_sort_outliner(bpy.types.Operator):
        bl_idname = "rpr_tent.sort_outliner"
        bl_label = "Sort Collections Alphabetically"
        bl_description = "Alphabetically sort collections in the outliner"

        def execute(self, context):
            from src.outliner import sort_scene_collections
            sort_scene_collections(case_sensitive=True)
            self.report({"INFO"}, "Sorted outliner collections.")
            return {"FINISHED"}

    class RPR_TENT_OT_load_labels(bpy.types.Operator):
        bl_idname = "rpr_tent.load_labels"
        bl_label = "Mount Packaging Labels"
        bl_description = "Scan label folder and create packaging label planes"

        def execute(self, context):
            from src.labels import load_labels
            count = load_labels()
            self.report({"INFO"}, f"Processed {count} label plane(s).")
            return {"FINISHED"}

    class RPR_TENT_OT_batch_render(bpy.types.Operator):
        bl_idname = "rpr_tent.batch_render"
        bl_label = "Batch Render Cameras"
        bl_description = "Render all camera views with Radeon ProRender"

        def execute(self, context):
            from src.renderer import batch_render
            from src.postprocess import clean_frame_numbers
            from src.config import TentConfig
            from pathlib import Path

            cfg = TentConfig()
            rendered = batch_render(cfg)
            paths = cfg.resolve_paths(Path(bpy.path.abspath("//")))
            clean_frame_numbers(paths["export_path"])
            self.report({"INFO"}, f"Finished rendering {len(rendered)} camera(s).")
            return {"FINISHED"}

    class RPR_TENT_PT_panel(bpy.types.Panel):
        bl_label = "RPR Tent"
        bl_idname = "RPR_TENT_PT_panel"
        bl_space_type = "VIEW_3D"
        bl_region_type = "UI"
        bl_category = "RPR Tent"

        def draw(self, context):
            layout = self.layout
            layout.operator("rpr_tent.reload_textures", icon="FILE_REFRESH")
            layout.operator("rpr_tent.sort_outliner", icon="OUTLINER")
            layout.separator()
            layout.operator("rpr_tent.load_labels", icon="TEXTURE")
            layout.separator()
            layout.operator("rpr_tent.batch_render", icon="OUTPUT")

    classes = (
        RPR_TENT_OT_reload_textures,
        RPR_TENT_OT_sort_outliner,
        RPR_TENT_OT_load_labels,
        RPR_TENT_OT_batch_render,
        RPR_TENT_PT_panel,
    )

    for cls in classes:
        bpy.utils.register_class(cls)


def unregister():
    try:
        import bpy
    except ImportError:
        return

    # In Blender unregister
    for cls in reversed(bpy.types.Panel.__subclasses__()):
        if cls.__name__.startswith("RPR_TENT"):
            bpy.utils.unregister_class(cls)

