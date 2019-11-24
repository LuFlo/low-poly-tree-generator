bl_info = {
    "name": "Low Poly Tree Generator",
    "author": "Lukas Florea",
    "version": (0, 1, 0),
    "blender": (2, 80, 0),
    "location": "View3D > Properties > Low Poly Tree",
    "description": "Generates a low poly tree with leafs",
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
    CollectionProperty,
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
                               stem_mat=scene.lptg_stem_material,
                               leaf_mat_prefix=scene.lptg_leaf_material,
                               initial_radius=scene.lptg_init_radius,
                               depth=scene.lptg_branch_depth,
                               leaf_size=scene.lptg_leaf_size,
                               leaf_size_deviation=scene.lptg_leaf_size_deviation)
        except ValueError as e:
            self.report({'ERROR'}, str(e))
        return {'FINISHED'}


class VIEW3D_PT_low_poly_tree(Panel):

    bl_category = "Low Poly Tree"
    bl_idname = "VIEW3D_PT_low_poly_tree"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_label = "Low Poly Tree"

    @classmethod
    def poll(cls, context):
        return True

    def draw(self, context):
        layout = self.layout
        layout.row().prop(context.scene, "lptg_branch_depth")
        layout.row().prop(context.scene, "lptg_init_radius")
        layout.row().prop(context.scene, "lptg_radius_factor")
        layout.row().prop(context.scene, "lptg_stem_section_length")
        layout.row().prop(context.scene, "lptg_stem_length_factor")

        row = layout.row()
        row.column().label(text="Stem material")
        row.column().prop(context.scene, "lptg_stem_material")

        row = layout.row()
        row.column().label(text="Leaf material prefix")
        row.column().prop(context.scene, "lptg_leaf_material")

        row = layout.row()
        row.column().label(text="Leaf geometry")
        row.column().prop(context.scene, "lptg_leaf_geometry")

        layout.row().prop(context.scene, "lptg_leaf_size")
        layout.row().prop(context.scene, "lptg_leaf_size_deviation")

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
    bpy.types.Scene.lptg_leaf_material = StringProperty(
        default="leaf_",
        name="", description="Every material which begins with this prefix will be "
                             "considered as leaf material. The acutal material is "
                             "chosen randomly for each leaf.")
    bpy.types.Scene.lptg_init_radius = FloatProperty(
        default=1.0, min=0.0, max=10.0,
        name="Root radius",
        description="Stem radius at the root of the tree")
    bpy.types.Scene.lptg_radius_factor = FloatProperty(
        default=0.8, min=0.05, max=1.0,
        name="Radius factor",
        description="Factor by which the stem radius gets smaller after each section")
    bpy.types.Scene.lptg_stem_section_length = FloatProperty(
        default=2.0, min=0.05, max=10.0,
        name="Initial stem size",
        description="Initial length of the first section of the stem")
    bpy.types.Scene.lptg_stem_length_factor = FloatProperty(
        default=0.9, min=0.05, max=1.0,
        name="Stem length factor",
        description="Factor by which the stem length gets smaller after each section")
    bpy.types.Scene.lptg_leaf_geometry = EnumProperty(
        items=[('mesh.primitive_cube_add', "Cube", "Cube mesh", 'CUBE', 0),
               ('mesh.primitive_ico_sphere_add', "Sphere", "Sphere mesh", 'MESH_ICOSPHERE', 1)],
        default='mesh.primitive_ico_sphere_add',
        name="",
        description="The geometry mesh from which the leaves are created",)
    bpy.types.Scene.lptg_leaf_size = FloatProperty(
        default=0.5, min=0.0, max=10.0,
        name="Leaf size",
        description="Base size for the leaves")
    bpy.types.Scene.lptg_leaf_size_deviation = FloatProperty(
        default=10.0, min=0.0, max=99.0,
        name="Max leaf size deviation",
        subtype='PERCENTAGE',
        description="Allowed percentage for the random deviation of the leaf size")


def unregister():
    bpy.utils.unregister_class(VIEW3D_PT_low_poly_tree)
    bpy.utils.unregister_class(PerformGeneration)
