#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# Simple script to get information from an lv2 bundle

import os, lilv

# Get info from an lv2 bundle
# @a bundle is a string, consisting of a directory in the filesystem (absolute pathname).
def get_info_from_lv2_bundle(bundle):
    # lilv wants the last character as the separator
    if not bundle.endswith(os.sep):
        bundle += os.sep

    # Create our own unique lilv world
    # We'll load a single bundle and get all plugins from it
    world = lilv.World()

    # this is needed when loading specific bundles instead of load_all
    # (these functions are not exposed via World yet)
    lilv.lilv_world_load_specifications(world.me)
    lilv.lilv_world_load_plugin_classes(world.me)

    # convert bundle string into a lilv node
    bundlenode = lilv.lilv_new_file_uri(world.me, None, bundle)

    # load the bundle
    world.load_bundle(bundlenode)

    # free bundlenode, no longer needed
    lilv.lilv_node_free(bundlenode)

    # get all plugins in the bundle
    plugins = world.get_all_plugins()

    # make sure the bundle includes 1 and only 1 plugin (the pedalboard)
    if plugins.size() != 1:
        raise Exception('get_info_from_lv2_bundle(%s) - bundle has 0 or > 1 plugin'.format(bundle))

    # no indexing in python-lilv yet, just get the first item
    plugin = None
    for p in plugins:
        plugin = p
        break

    if plugin is None:
        raise Exception('get_info_from_lv2_bundle(%s) - failed to get plugin, you are using an old lilv!'.format(bundle))

    # handy class to get lilv nodes from. copied from lv2.py in mod-ui
    class NS(object):
        def __init__(self, base):
            self.base = base
            self._cache = {}

        def __getattr__(self, attr):
            if attr not in self._cache:
                self._cache[attr] = lilv.Node(world.new_uri(self.base+attr))
            return self._cache[attr]

    # define the needed stuff
    NS_lv2core       = NS('http://lv2plug.in/ns/lv2core#')
    NS_lv2core_proto = NS_lv2core.prototype

    NS_modgui       = NS('http://portalmod.com/ns/modgui#')
    NS_modgui_thumb = NS_modgui.thumbnail

    NS_ingen           = NS('http://drobilla.net/ns/ingen#')
    NS_ingen_block     = NS_ingen.block
    NS_ingen_prototype = NS_ingen.prototype

    # check if the plugin has modgui:thumnail, if not it's probably not a real pedalboard
    thumbnail_check = plugin.get_value(NS_modgui_thumb).get_first()

    if thumbnail_check.me is None:
        raise Exception('get_info_from_lv2_bundle(%s) - plugin has no modgui:thumbnail'.format(bundle))

    # let's get all the info now
    ingenplugins = []

    info = {
        'name':      plugin.get_name().as_string(),
        #'author':    plugin.get_author_name().as_string() or '', # Might be empty
        #'uri':       plugin.get_uri().as_string(),
        'thumbnail': os.path.basename(thumbnail_check.as_string()),
        'plugins':   [] # we save this info later
    }

    blocks = plugin.get_value(NS_ingen_block)

    it = blocks.begin()
    while not blocks.is_end(it):
        block = blocks.get(it)
        it    = blocks.next(it)

        if block.me is None:
            continue

        protouri1 = lilv.lilv_world_get(world.me, block.me, NS_lv2core_proto.me, None)
        protouri2 = lilv.lilv_world_get(world.me, block.me, NS_ingen_prototype.me, None)

        if protouri1 is not None:
            ingenplugins.append(lilv.lilv_node_as_uri(protouri1))
        elif protouri2 is not None:
            ingenplugins.append(lilv.lilv_node_as_uri(protouri2))

    info['plugins'] = ingenplugins

    return info

# Test via command line
if __name__ == '__main__':
    import sys

    if len(sys.argv) == 1:
        print("usage %s /path/to/bundle" % sys.argv[0])
        sys.exit(0)

    print(get_info_from_lv2_bundle(sys.argv[1]))
