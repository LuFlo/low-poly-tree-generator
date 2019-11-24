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
smaller = 0.75
branch_sigma = 1.4
scale_signma = 0.3
min_branch_length = 0.2
initial_branch_lengt = 2.0

# Angle params
max_angle = 35.0
start_angle = 7.0
angle_k = 0.3

# Branch propability data
max_branch_propability = 0.9
start_branch_propability = 0.2
branch_prop_k = 0.8


def generate_tree(context, stem_mat, leave_mat, initial_radius, depth):
    mesh = bpy.data.meshes.new("Stem")
    mesh.vertices.add(1)
    obj = object_utils.object_data_add(context, mesh, operator=None)
    bpy.ops.object.mode_set(mode="EDIT")
    bpy.ops.mesh.select_all(action='DESELECT')
    bpy.ops.object.mode_set(mode="OBJECT")
    bpy.ops.object.mode_set(mode="EDIT")

    bm = bmesh.from_edit_mesh(obj.data)
    bm.verts.ensure_lookup_table()
    root_vert = bm.verts[0]

    vertex_radius_map = (root_vert, initial_radius)
    second_radius = initial_radius * smaller
    outer_verts, vr_maps = extrude(bm, root_vert, [vertex_radius_map],
                                   second_radius, depth=depth)
    bm.verts.ensure_lookup_table()

    # Saving vert coordinates
    outer_coordinates = [Vector(v.co) for v in outer_verts]

    # Applying radii
    index_radius_maps = [(v.index, r) for v, r in vr_maps]

    bpy.ops.object.modifier_add(type='SKIN')

    bmesh.update_edit_mesh(obj.data)
    bpy.ops.object.mode_set(mode="OBJECT")
    for i, r in index_radius_maps:
        obj.data.skin_vertices[0].data[i].radius = (r, r)

    # Adding leaves
    add_leaves(outer_coordinates, obj.matrix_world, leave_mat)
    obj.data.materials.append(stem_mat)
    # bpy.ops.object.mode_set(mode="EDIT")


def angle_func(steps):
    """ Return the angle based on the steps
    """
    return max_angle - (max_angle - start_angle) * (math.e ** (-steps * angle_k))


def scale_func(steps):
    nominal = initial_branch_lengt * (0.9 ** steps)
    rand_scale = math.fabs(gauss(nominal, scale_signma * nominal))
    return max(rand_scale, min_branch_length)


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


def rot_and_add_vert(vert, root_vert, translated_root, euler, steps):
    # e = Euler((0.0, radians(angle_deg), 0.0), 'XYZ')
    nv = translated_root.normalized() * scale_func(steps)
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


def extrude(bm, root_vert, vertex_radius_maps, radius, depth=1, steps=0,
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
                                         translated_root, euler, steps)
    my_translated_root = other_vert.co - root_vert.co

    vr_map = (other_vert, radius)
    my_vr_maps = [*vertex_radius_maps, vr_map]
    if depth <= 1:
        return [*outer_verts, other_vert], my_vr_maps
    else:
        if branch_prop_func(steps):
            return branch_extrude(bm, other_vert, my_vr_maps, radius * smaller,
                                  depth=depth - 1, steps=steps + 1, translated_root=my_translated_root)
        else:
            eulers = rand_rot(my_translated_root, angle_func(steps) / 2.0)
            e = random.choice(eulers)
            return extrude(bm, other_vert, my_vr_maps, radius * smaller, euler=e,
                           depth=depth - 1, steps=steps + 1, translated_root=my_translated_root)
        # return extrude(bm, other_vert, my_vr_maps, radius*smaller,
        #        depth=depth-1, translated_root=my_translated_root)


def add_leaves(outer_coordinates, matrix, leave_mat):
    for v in outer_coordinates:
        my_co = matrix @ v
        bpy.ops.mesh.primitive_ico_sphere_add(
            radius=1, enter_editmode=False,
            location=my_co
        )
        bpy.ops.transform.resize(
            value=(0.5, 0.5, 0.5))
        obj = bpy.context.active_object
        if leave_mat:
            obj.data.materials.append(leave_mat)
        e, _ = rand_rot(Vector((0.0, 0.0, 1.0)), random.uniform(0, 45))
        obj.rotation_euler = e
