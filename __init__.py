bl_info = {
    "name": "Low Poly Tree Generator",
    "author": "Lukas Florea",
    "version": (0, 1, 0),
    "blender": (2, 80, 0),
    "location": "View3D > Properties > Low Poly Tree",
    "description": "Generates a low poly tree with leaves",
    "warning": "",
    "wiki_url": "https://github.com/LuFlo/low-poly-tree-generator/wiki",
    "tracker_url": "https://github.com/LuFlo/low-poly-tree-generator/issues/new",
    "category": "Add Mesh"
}

import bpy
from bpy.props import (
    IntProperty,
    FloatProperty,
    FloatVectorProperty,
    StringProperty,
    EnumProperty,
    BoolProperty,
    PointerProperty,
)
from bpy.types import PropertyGroup, Panel
from . import util


class PerformGeneration(bpy.types.Operator):
    """Tooltip"""
    bl_idname = "object.generate_tree"
    bl_label = "Generate Tree"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'

    @classmethod
    def poll(cls, context):
        return True

    def execute(self, context):
        scene = context.scene
        try:
            util.generate_tree(context,
                               scene.lptg_stem_material,
                               scene.lptg_leave_material,
                               scene.lptg_init_radius,
                               scene.lptg_branch_depth)
        except ValueError as e:
            self.report({'ERROR'}, str(e))
        return {'FINISHED'}


class VIEW3D_PT_low_poly_tree(Panel):

    bl_category = "Low Poly Tree"
    bl_idname = "VIEW3D_PT_low_poly_tree"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_label = "Low Poly Tree"

    max_leave_count: IntProperty(name="Maximum Leave Count",
                                 default=20, min=1, max=50)

    @classmethod
    def poll(cls, context):
        return True

    def draw(self, context):
        layout = self.layout
        layout.row().prop(context.scene, "lptg_branch_depth")

        layout.row().prop(context.scene, "lptg_init_radius")

        row = layout.row()
        row.column().label(text="Stem material")
        row.column().prop(context.scene, "lptg_stem_material")

        row = layout.row()
        row.column().label(text="Leave material")
        row.column().prop(context.scene, "lptg_leave_material")

        row = layout.row()
        row.operator("object.generate_tree")


def register():
    bpy.utils.register_class(VIEW3D_PT_low_poly_tree)
    bpy.utils.register_class(PerformGeneration)

    bpy.types.Scene.lptg_branch_depth = IntProperty(
        name="Branch depth",
        default=10, min=1, max=20)
    bpy.types.Scene.lptg_stem_material = PointerProperty(
        type=bpy.types.Material,
        name="", description="Stem Material")
    bpy.types.Scene.lptg_leave_material = PointerProperty(
        type=bpy.types.Material,
        name="", description="Leave Material")
    bpy.types.Scene.lptg_init_radius = FloatProperty(
        default=1.0, min=0.0, max=10.0,
        name="Root radius",
        description="Stem radius at the root of the tree")


def unregister():
    bpy.utils.unregister_class(VIEW3D_PT_low_poly_tree)
    bpy.utils.unregister_class(PerformGeneration)
