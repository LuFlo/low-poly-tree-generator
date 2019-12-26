import bpy, bmesh
from bpy_extras import object_utils

import math
import random

from mathutils import Euler
from mathutils import Quaternion
from mathutils import Vector
from math import radians
from random import randrange
from random import gauss

next_z = 1.0
branch_sigma = 1.4
scale_signma = 0.3
min_branch_length_factor = 0.2
initial_branch_length = 2.0

# Angle params
max_angle = 35.0
start_angle = 7.0
angle_k = 0.3

# Branch propability data
max_branch_propability = 0.9
start_branch_propability = 0.2
branch_prop_k = 0.8


def generate_tree(context, stem_mat=None, leaf_mat_prefix=None,
                  initial_radius=1.0, radius_factor=0.8, depth=10,
                  leaf_size=0.5, leaf_size_deviation=20.0):
    random.seed(context.scene.lptg_seed, version=2)
    if not context.mode == "OBJECT":
        bpy.ops.object.mode_set(mode="OBJECT")
    mesh = bpy.data.meshes.new("Stem")
    mesh.vertices.add(1)
    stem_obj = object_utils.object_data_add(context, mesh, operator=None)
    bpy.ops.object.mode_set(mode="EDIT")
    bpy.ops.mesh.select_all(action='DESELECT')
    bpy.ops.object.mode_set(mode="OBJECT")
    bpy.ops.object.mode_set(mode="EDIT")

    bm = bmesh.from_edit_mesh(stem_obj.data)
    bm.verts.ensure_lookup_table()
    root_vert = bm.verts[0]

    vertex_radius_map = (root_vert, initial_radius)
    second_radius = initial_radius * radius_factor
    outer_verts, vr_maps = extrude(bm, root_vert, [vertex_radius_map],
                                   second_radius,
                                   context=context,
                                   radius_factor=radius_factor,
                                   depth=depth)
    bm.verts.ensure_lookup_table()

    # Saving vert coordinates
    outer_coordinates = [Vector(v.co) for v in outer_verts]
    index_coordinates_map = [(v.index, Vector(v.co)) for v in outer_verts]
    # Applying radii
    index_radius_maps = [(v.index, r) for v, r in vr_maps]

    bmesh.update_edit_mesh(stem_obj.data)
    bpy.ops.object.mode_set(mode="OBJECT")

    bpy.context.view_layer.objects.active = stem_obj

    bpy.ops.object.modifier_add(type='SKIN')
    for i, r in index_radius_maps:
        stem_obj.data.skin_vertices[0].data[i].radius = (r, r)

    # add_leaves2(index_coordinates_map, stem_obj.matrix_world, leaf_mat, stem_obj)
    # Adding leaves
    # bm.verts.index_update()
    random.choices(bpy.data.materials)
    leaf_mats = [mat for mat in bpy.data.materials if mat.name.startswith(leaf_mat_prefix)]
    leaves = add_leaves(outer_coordinates, stem_obj.matrix_world,
                        leaf_mats=leaf_mats, leaf_size=leaf_size,
                        leaf_size_deviation=leaf_size_deviation,
                        leaf_geometry=context.scene.lptg_leaf_geometry)

    stem_obj.data.materials.append(stem_mat)

    scene_coll = bpy.context.scene.collection

    coll_tree = bpy.data.collections.new("Tree")
    coll_stem = bpy.data.collections.new("Stem")
    coll_leaves = bpy.data.collections.new("Leaves")
    coll_tree.children.link(coll_stem)
    coll_tree.children.link(coll_leaves)
    coll_stem.objects.link(stem_obj)
    if stem_obj in scene_coll.objects.values():
        scene_coll.objects.unlink(stem_obj)
    for leaf_obj in leaves:
        coll_leaves.objects.link(leaf_obj)
        if leaf_obj in scene_coll.objects.values():
            scene_coll.objects.unlink(leaf_obj)
    scene_coll.children.link(coll_tree)


def angle_func(steps):
    """ Return the angle based on the steps
    """
    return max_angle - (max_angle - start_angle) * (math.e ** (-steps * angle_k))


def scale_func(steps, context=None):
    nominal = context.scene.lptg_stem_section_length \
              * (context.scene.lptg_stem_length_factor ** steps)
    rand_scale = math.fabs(gauss(nominal, scale_signma * nominal))
    return max(rand_scale,
               context.scene.lptg_stem_section_length * min_branch_length_factor)


def branch_prop_func(steps):
    coeff = max_branch_propability - start_branch_propability
    prop = max_branch_propability - coeff * (math.e ** (-steps * branch_prop_k))
    rand_val = random.uniform(0.0, 1.0)
    return rand_val < prop


def rand_rot(v, mean_branch_angle):
    v_temp = Vector((v.x, v.z, v.y))
    cross1 = v.cross(v_temp)
    cross2 = v.cross(cross1)
    branch_angle = random.gauss(mean_branch_angle, branch_sigma)
    q1 = Quaternion(cross1, radians(branch_angle))
    q2 = Quaternion(q1)
    angle = random.uniform(0.0, math.pi)
    q1.rotate(Quaternion(v, angle))
    q2.rotate(Quaternion(v, angle + math.pi))

    return q1.to_euler(), q2.to_euler()


def rot_and_add_vert(vert, root_vert, translated_root, euler, steps,
                     context=None):
    # e = Euler((0.0, radians(angle_deg), 0.0), 'XYZ')
    nv = translated_root.normalized() * scale_func(steps, context=context)
    nv.rotate(euler)
    return nv + root_vert.co


def branch_extrude(*extrude_args, **extrude_kwargs):
    # e1 = Euler((0.0, radians(20), 0.0), 'XYZ')
    # e2 = Euler((0.0, radians(-20), 0.0), 'XYZ')
    e1, e2 = rand_rot(
        extrude_kwargs['translated_root'],
        angle_func(extrude_kwargs['steps'])
    )
    kwargs1 = {**extrude_kwargs, 'euler': e1}
    kwargs2 = {**extrude_kwargs, 'euler': e2}

    verts1, map1 = extrude(*extrude_args, **kwargs1)
    verts2, map2 = extrude(*extrude_args, **kwargs2)

    # Combine both maps
    res_map = [*map1, *list(set(map2) - set(map1))]

    return [*verts1, *verts2], res_map


def extrude(bm, root_vert, vertex_radius_maps, radius, context=None,
            radius_factor=0.8, depth=1, steps=0,
            translated_root=None, euler=Euler((0.0, 0.0, 0.0), 'XYZ'), outer_verts=[]):
    res_dict = bmesh.ops.extrude_vert_indiv(bm, verts=[root_vert])
    # bm.verts.ensure_lookup_table()
    other_vert = res_dict['verts'][0]
    if not translated_root:
        # Don't rotate
        other_vert.co.z = root_vert.co.z + next_z
    else:
        # e = Euler((0.0, radians(20.0), 0.0), 'XYZ')
        other_vert.co = rot_and_add_vert(other_vert, root_vert,
                                         translated_root, euler, steps, context=context)
    my_translated_root = other_vert.co - root_vert.co

    vr_map = (other_vert, radius)
    my_vr_maps = [*vertex_radius_maps, vr_map]
    if depth <= 1:
        return [*outer_verts, other_vert], my_vr_maps
    else:
        if branch_prop_func(steps):
            return branch_extrude(bm, other_vert, my_vr_maps, radius * radius_factor,
                                  context=context,
                                  depth=depth - 1,
                                  steps=steps + 1,
                                  translated_root=my_translated_root)
        else:
            eulers = rand_rot(my_translated_root, angle_func(steps) / 2.0)
            e = random.choice(eulers)
            return extrude(bm, other_vert, my_vr_maps, radius * radius_factor,
                           euler=e,
                           context=context,
                           depth=depth - 1,
                           steps=steps + 1,
                           translated_root=my_translated_root)


def add_leaves2(index_coordinates_map, matrix, leaf_mat, stem_obj):
    # bpy.ops.object.mode_set(mode="OBJECT")
    for v_index, v in index_coordinates_map:
        # bpy.ops.object.select_all(action='DESELECT')
        my_co = matrix @ v
        bpy.ops.mesh.primitive_ico_sphere_add(
            radius=1, enter_editmode=False,
            location=my_co
        )
        bpy.ops.transform.resize(
            value=(0.5, 0.5, 0.5))
        leaf_obj = bpy.context.active_object
        if leaf_mat:
            leaf_obj.data.materials.append(leaf_mat)
        e, _ = rand_rot(Vector((0.0, 0.0, 1.0)), random.uniform(0, 45))
        leaf_obj.rotation_euler = e


def add_leaves(outer_coordinates, matrix, leaf_mats=[], leaf_size=0.5,
               leaf_size_deviation=20.0,
               leaf_geometry='mesh.primitive_ico_sphere_add'):
    leaf_objects = []
    for v in outer_coordinates:
        my_co = matrix @ v
        if leaf_geometry == 'mesh.primitive_ico_sphere_add':
            bpy.ops.mesh.primitive_ico_sphere_add(
                radius=1, enter_editmode=False,
                location=my_co
            )
        elif leaf_geometry == 'mesh.primitive_cube_add':
            bpy.ops.mesh.primitive_cube_add(
                size=1, enter_editmode=False,
                location=my_co
            )
        deviation = leaf_size * (leaf_size_deviation / 100.0)
        size = random.uniform(leaf_size - deviation, leaf_size + deviation)
        bpy.ops.transform.resize(
            value=(size, size, size))
        leaf_obj = bpy.context.active_object
        if leaf_mats:
            leaf_obj.data.materials.append(random.choice(leaf_mats))
        e, _ = rand_rot(Vector((0.0, 0.0, 1.0)), random.uniform(0, 45))
        leaf_obj.rotation_euler = e
        leaf_obj.name = "Leaf"
        leaf_objects.append(leaf_obj)
    return leaf_objects
