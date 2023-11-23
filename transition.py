import bpy
from bpy.props import *
from .common import *
from .transition_common import *
from .node_connections import *
from .node_arrangements import *
from .subtree import *
from .input_outputs import *

def update_transition_ramp_intensity_value(self, context):
    yp = self.id_data.yp
    if yp.halt_update: return
    match = re.match(r'yp\.layers\[(\d+)\]\.channels\[(\d+)\]', self.path_from_id())
    layer = yp.layers[int(match.group(1))]
    tree = get_tree(layer)

    set_ramp_intensity_value(tree, layer, self)

def update_transition_bump_chain(self, context):
    T = time.time()

    yp = self.id_data.yp
    if yp.halt_update: return
    m = re.match(r'yp\.layers\[(\d+)\]\.channels\[(\d+)\]', self.path_from_id())
    layer = yp.layers[int(m.group(1))]
    tree = get_tree(layer)
    root_ch = yp.channels[int(m.group(2))]
    ch = self

    #if ch.enable_transition_bump and ch.enable:

    #check_mask_mix_nodes(layer, tree)
    #check_mask_source_tree(layer) #, ch)

    # Trigger normal channel update
    #ch.normal_map_type = ch.normal_map_type
    check_channel_normal_map_nodes(tree, layer, root_ch, ch)

    rearrange_layer_nodes(layer)
    reconnect_layer_nodes(layer) #, mod_reconnect=True)

    print('INFO: Transition bump chain is updated at {:0.2f}'.format((time.time() - T) * 1000), 'ms!')

def update_transition_bump_curved_offset(self, context):

    yp = self.id_data.yp
    if yp.halt_update: return
    m = re.match(r'yp\.layers\[(\d+)\]\.channels\[(\d+)\]', self.path_from_id())
    layer = yp.layers[int(m.group(1))]
    tree = get_tree(layer)
    ch = self

    #tb_bump = tree.nodes.get(ch.tb_bump)
    #if tb_bump:
    #    tb_bump.inputs['Offset'].default_value = ch.transition_bump_curved_offset

def update_transition_ao_intensity(self, context):
    set_transition_ao_intensity(self)

def update_transition_ao_edge(self, context):

    yp = self.id_data.yp
    if yp.halt_update: return
    match = re.match(r'yp\.layers\[(\d+)\]\.channels\[(\d+)\]', self.path_from_id())
    layer = yp.layers[int(match.group(1))]
    ch = self
    tree = get_tree(layer)

    bump_ch = get_transition_bump_channel(layer)

    tao = tree.nodes.get(ch.tao)
    if tao and bump_ch:
        tao.inputs['Power'].default_value = ch.transition_ao_power

def update_transition_ao_color(self, context):

    yp = self.id_data.yp
    if yp.halt_update: return
    match = re.match(r'yp\.layers\[(\d+)\]\.channels\[(\d+)\]', self.path_from_id())
    layer = yp.layers[int(match.group(1))]
    ch = self
    tree = get_tree(layer)

    tao = tree.nodes.get(ch.tao)
    if tao:
        col = (ch.transition_ao_color.r, ch.transition_ao_color.g, ch.transition_ao_color.b, 1.0)
        tao.inputs['AO Color'].default_value = col

def update_transition_ao_exclude_inside(self, context):

    yp = self.id_data.yp
    if yp.halt_update: return
    match = re.match(r'yp\.layers\[(\d+)\]\.channels\[(\d+)\]', self.path_from_id())
    layer = yp.layers[int(match.group(1))]
    ch = self
    tree = get_tree(layer)

    tao = tree.nodes.get(ch.tao)
    if tao:
        tao.inputs['Exclude Inside'].default_value = 1.0 - ch.transition_ao_inside_intensity

def show_transition(self, context, ttype):
    if not hasattr(context, 'parent'): 
        self.report({'ERROR'}, "Context is incorrect!")
        return {'CANCELLED'}

    yp = context.parent.id_data.yp
    match = re.match(r'yp\.layers\[(\d+)\]\.channels\[(\d+)\]', context.parent.path_from_id())
    if not match: 
        self.report({'ERROR'}, "Context is incorrect!")
        return {'CANCELLED'}
    layer = yp.layers[int(match.group(1))]
    root_ch = yp.channels[int(match.group(2))]
    ch = context.parent

    bump_ch = get_transition_bump_channel(layer)

    if ttype == 'BUMP':

        if root_ch.type != 'NORMAL': 
            self.report({'ERROR'}, "Transition bump only works on Normal channel!")
            return {'CANCELLED'}

        if bump_ch and ch != bump_ch:
            self.report({'ERROR'}, "Transition bump already enabled on other channel!")
            return {'CANCELLED'}

        ch.show_transition_bump = True

        if ch.enable_transition_bump:
            self.report({'INFO'}, "Transition bump is already set!")
            return {'FINISHED'}

        ch.enable_transition_bump = True

        # Hide other channels transition bump
        for c in layer.channels:
            if c != ch:
                c.show_transition_bump = False

    elif ttype == 'RAMP':

        if root_ch.type == 'NORMAL': 
            self.report({'ERROR'}, "Transition ramp only works on color or value channel!")
            return {'CANCELLED'}

        ch.show_transition_ramp = True

        if ch.enable_transition_ramp:
            self.report({'INFO'}, "Transition ramp is already set!")
            return {'FINISHED'}

        ch.enable_transition_ramp = True

    elif ttype == 'AO':

        if root_ch.type == 'NORMAL': 
            self.report({'ERROR'}, "Transition AO only works on color or value channel!")
            return {'CANCELLED'}

        if not bump_ch:
            self.report({'ERROR'}, "Transition AO only works if there's transition bump enabled on other channel!")
            return {'CANCELLED'}

        ch.show_transition_ao = True

        if ch.enable_transition_ao:
            self.report({'INFO'}, "Transition AO is already set!")
            return {'FINISHED'}

        ch.enable_transition_ao = True

    # Expand channel content
    if hasattr(context, 'channel_ui'):
        context.channel_ui.expand_content = True

    return {'FINISHED'}

class YShowTransitionBump(bpy.types.Operator):
    """Use transition bump (This will affect other channels)"""
    bl_idname = "node.y_show_transition_bump"
    bl_label = "Show Transition Bump"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        return True

    def execute(self, context):
        return show_transition(self, context, ttype = 'BUMP')

class YShowTransitionRamp(bpy.types.Operator):
    """Use transition ramp (Works best if there's transition bump enabled on other channel)"""
    bl_idname = "node.y_show_transition_ramp"
    bl_label = "Show Transition Ramp"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        return True

    def execute(self, context):
        return show_transition(self, context, ttype = 'RAMP')

class YShowTransitionAO(bpy.types.Operator):
    """Use transition AO (Only works if there's transition bump enabled on other channel)"""
    bl_idname = "node.y_show_transition_ao"
    bl_label = "Show Transition AO"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        return True

    def execute(self, context):
        return show_transition(self, context, ttype = 'AO')

class YHideTransitionEffect(bpy.types.Operator):
    """Remove transition Effect"""
    bl_idname = "node.y_hide_transition_effect"
    bl_label = "Hide Transition Effect"
    bl_options = {'REGISTER', 'UNDO'}

    type : EnumProperty(
            name = 'Type',
            items = (
                ('BUMP', 'Bump', ''),
                ('RAMP', 'Ramp', ''),
                ('AO', 'AO', ''),
                ),
            default = 'BUMP')

    @classmethod
    def poll(cls, context):
        return True

    def execute(self, context):

        if not hasattr(context, 'parent'): 
            self.report({'ERROR'}, "Context is incorrect!")
            return {'CANCELLED'}

        yp = context.parent.id_data.yp
        match = re.match(r'yp\.layers\[(\d+)\]\.channels\[(\d+)\]', context.parent.path_from_id())
        if not match: 
            self.report({'ERROR'}, "Context is incorrect!")
            return {'CANCELLED'}
        layer = yp.layers[int(match.group(1))]
        root_ch = yp.channels[int(match.group(2))]
        ch = context.parent

        if self.type == 'BUMP' and root_ch.type != 'NORMAL':
            self.report({'ERROR'}, "Context is incorrect!")
            return {'CANCELLED'}

        if self.type != 'BUMP' and root_ch.type == 'NORMAL':
            self.report({'ERROR'}, "Context is incorrect!")
            return {'CANCELLED'}

        if self.type == 'BUMP':
            ch.enable_transition_bump = False
            ch.show_transition_bump = False
        elif self.type == 'RAMP':
            ch.enable_transition_ramp = False
            ch.show_transition_ramp = False
        else:
            ch.enable_transition_ao = False
            ch.show_transition_ao = False

        return {'FINISHED'}

def update_enable_transition_ao(self, context):
    T = time.time()

    yp = self.id_data.yp
    if yp.halt_update: return
    match = re.match(r'yp\.layers\[(\d+)\]\.channels\[(\d+)\]', self.path_from_id())
    layer = yp.layers[int(match.group(1))]
    ch = self

    tree = get_tree(layer)

    # Get transition bump
    bump_ch = get_transition_bump_channel(layer)

    check_transition_ao_nodes(tree, layer, ch, bump_ch)

    # Update mask multiply
    check_mask_mix_nodes(layer, tree)

    rearrange_layer_nodes(layer)
    reconnect_layer_nodes(layer)

    if ch.enable_transition_ao:
        print('INFO: Transition AO is enabled at {:0.2f}'.format((time.time() - T) * 1000), 'ms!')
    else: print('INFO: Transition AO is disabled at {:0.2f}'.format((time.time() - T) * 1000), 'ms!')

def update_enable_transition_ramp(self, context):
    T = time.time()

    yp = self.id_data.yp
    if yp.halt_update: return
    match = re.match(r'yp\.layers\[(\d+)\]\.channels\[(\d+)\]', self.path_from_id())
    layer = yp.layers[int(match.group(1))]
    root_ch = yp.channels[int(match.group(2))]
    ch = self

    tree = get_tree(layer)

    check_layer_tree_ios(layer, tree, remove_props=True)

    check_transition_ramp_nodes(tree, layer, ch)

    # Update mask multiply
    check_mask_mix_nodes(layer, tree)
    check_blend_type_nodes(root_ch, layer, ch)

    check_layer_tree_ios(layer, tree)

    rearrange_layer_nodes(layer)
    reconnect_layer_nodes(layer)

    if ch.enable_transition_ramp:
        print('INFO: Transition ramp is enabled at {:0.2f}'.format((time.time() - T) * 1000), 'ms!')
    else: print('INFO: Transition ramp is disabled at {:0.2f}'.format((time.time() - T) * 1000), 'ms!')

def update_enable_transition_bump(self, context):
    T = time.time()

    yp = self.id_data.yp
    if yp.halt_update or not self.enable: return
    match = re.match(r'yp\.layers\[(\d+)\]\.channels\[(\d+)\]', self.path_from_id())
    layer = yp.layers[int(match.group(1))]
    ch_index = int(match.group(2))
    root_ch = yp.channels[ch_index]
    ch = self
    tree = get_tree(layer)

    check_layer_tree_ios(layer, tree, remove_props=True)

    check_transition_bump_nodes(layer, tree, ch)

    check_layer_tree_ios(layer, tree)

    rearrange_layer_nodes(layer)
    reconnect_layer_nodes(layer) #, mod_reconnect=True)

    if ch.enable_transition_bump:
        print('INFO: Transition bump is enabled at {:0.2f}'.format((time.time() - T) * 1000), 'ms!')
    else: print('INFO: Transition bump is disabled at {:0.2f}'.format((time.time() - T) * 1000), 'ms!')

def register():
    bpy.utils.register_class(YShowTransitionBump)
    bpy.utils.register_class(YShowTransitionRamp)
    bpy.utils.register_class(YShowTransitionAO)
    bpy.utils.register_class(YHideTransitionEffect)

def unregister():
    bpy.utils.unregister_class(YShowTransitionBump)
    bpy.utils.unregister_class(YShowTransitionRamp)
    bpy.utils.unregister_class(YShowTransitionAO)
    bpy.utils.unregister_class(YHideTransitionEffect)
