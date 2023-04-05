#!/usr/bin/env python3
# -*- coding: utf-8 -*-
'''
This file is part of tumorcode project.
(http://www.uni-saarland.de/fak7/rieger/homepage/research/tumor/tumor.html)

Copyright (C) 2016  Michael Welter and Thierry Fredrich

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program.  If not, see <http://www.gnu.org/licenses/>.
'''
if __name__ == '__main__':
  import os.path, sys
  sys.path.append(os.path.join(os.path.dirname(os.path.realpath(__file__)),'..'))
from os.path import join, basename, dirname, splitext
import time
#import plottools
import krebsutils
import h5py
import numpy as np
import matplotlib.cm
import myutils
import math
import identifycluster
import copy

import povray as pv
from krebs.povrayEasy import *

#see http://assorted-experience.blogspot.com/2007/07/custom-colormaps.html
cm_redblue = matplotlib.colors.LinearSegmentedColormap('redblue', {
    'red' : ((0,0,0), (1,1,1)),
    'green' : ((0,0,0) ,(1,0,0)),
    'blue' : ((0,1,1), (1,0,0))
  })

filter_circulated = lambda e,kw: (kw['flags']&krebsutils.CIRCULATED)

def filter_small_rad(rmin):
    return lambda e,kw: np.bitwise_and(kw['rad']>rmin,kw['flags']&krebsutils.CIRCULATED)


def filter_tumorvessels1(e,kw):
    flags = kw['flags']
    rad = kw['rad']
    return np.logical_and(
        flags&krebs.CIRCULATED,
        np.logical_or(
            flags&krebs.WITHIN_TUMOR,
            rad>=10.0
        )
    )



def make_pressure_color_arrays(vesselgraph):
    edges = vesselgraph.edgelist
    flags = vesselgraph.edges['flags']
    flags = flags[:,0]
    data = vesselgraph.nodes['pressure']
    data = data[:,0]
    data = data * 7.5 # to mmHg
    num_nodes = len(vesselgraph.nodes['position'])
    nflags = krebsutils.edge_to_node_property(num_nodes, edges, flags, 'or')

    is_set = lambda flags_,flag: np.asarray(np.bitwise_and(flags_, flag), np.bool)

    gray = np.asarray((0.1,0.1,0.1))
    lgray = np.asarray((0.5, 0.5, 0.5))

    circulated = is_set(flags,krebsutils.CIRCULATED)
    ncirculated = is_set(nflags,krebsutils.CIRCULATED)
    capillary = is_set(flags, krebsutils.CAPILLARY)
    ncapillary = is_set(nflags, krebsutils.CAPILLARY)
    if 0:#not good for tumorsimulation, circulated may not be well defined
      p0 = np.amin(data[ncirculated])
      p1 = np.amax(data[ncirculated])
    else:
      p0 = np.min(data[data>0])
      p1 = np.amax(data[data>0])
    cm = matplotlib.cm.ScalarMappable(cmap=cm_redblue)
    cm.set_clim(p0, p1)

    edgedata = np.average((data[edges[:,0]], data[edges[:,1]]), axis=0)
    edgecolors = cm.to_rgba(edgedata)[:,:3]
    edgecolors[~circulated] = gray
    #edgecolors[capillary] = lgray

    nodecolors = cm.to_rgba(data)[:,:3]
    nodecolors[~ncirculated] = gray
    #nodecolors[ncapillary] = lgray

    vesselgraph.edges['colors'] = edgecolors
    vesselgraph.nodes['colors'] = nodecolors



colors = [(0, 0.2,0,0.8), (0.45, 1,0,0), (0.6, 1, 1,0), (1., 1, 1, 1) ]
cm_hematocrit = matplotlib.colors.LinearSegmentedColormap('', {
  'red'   : [(x, r, r) for (x,r,g,b) in colors],
  'green' : [(x, g, g) for (x,r,g,b) in colors],
  'blue'  : [(x, b, b) for (x,r,g,b) in colors],
}, N = 256, gamma = 1.)


def make_any_color_arrays(vesselgraph, data_name,options):
  edges = vesselgraph.edgelist
  num_nodes = len(vesselgraph.nodes['position'])
  flags = vesselgraph.edges['flags']
  #flags = flags[:,0]
  #flags = np.asarray(flags,dtype='uint32')
  nflags = krebsutils.edge_to_node_property(num_nodes, edges, flags, 'or')

  mask = myutils.bbitwise_and(flags,krebsutils.CIRCULATED)
  nmask = myutils.bbitwise_and(nflags,krebsutils.CIRCULATED)

  if data_name in vesselgraph.edges:
    edgedata = vesselgraph.edges[data_name]
    nodedata = krebsutils.edge_to_node_property(num_nodes, edges, edgedata, 'avg')
  else:
    nodedata = vesselgraph.nodes[data_name]
    edgedata = np.average((nodedata[edges[:,0]], nodedata[edges[:,1]]), axis=0)

  gray = np.asarray((0.1,0.1,0.1))
  edgecolors = np.repeat(gray.reshape(1,-1), len(edgedata), axis=0)
  nodecolors = np.repeat(gray.reshape(1,-1), len(nodedata), axis=0)
 # colors = lambda arr: cm.to_rgba(arr)[:,:3]
  colors = lambda arr: np.power(cm.to_rgba(arr)[:,:3], 2.4)

  if data_name == 'hematocrit':
    h0 = np.min(edgedata[np.nonzero(edgedata)])
    if h0<0.1:
      print(("Minimal hematocrit is: %f" % h0))
      print("using 0.1 instead")
      h0 = 0.1
    h1 = np.max(edgedata[np.nonzero(edgedata)])
    unmapped_range = (h0, h1)
    cm = matplotlib.cm.ScalarMappable(cmap = matplotlib.cm.hsv)
    if options.vesselsColorLimits is None:
      cm.set_clim(h0, h1)
    else:
      print('setting colors limits for vessels')
      print((options.vesselsColorLimits[0]))
      print((options.vesselsColorLimits[1]))
      cm.set_clim(vmin=options.vesselsColorLimits[0], vmax=options.vesselsColorLimits[1])
    
    edgecolors[mask[:,0]] = colors(edgedata[mask])
    nodecolors[nmask[:,0]] = colors(nodedata[nmask])
    #unmapped_range = (0.,1.)
    #edgecolors[mask] = colors(edgedata[mask])
    #nodecolors[nmask] = colors(nodedata[nmask])
  elif data_name == 'pressure':
    #this looks really ugly if there is a zero pressure node
    #p0 = np.amin(nodedata)
    p0 = np.min(nodedata[np.nonzero(nodedata)])
    p1 = np.amax(nodedata)
    unmapped_range = (p0, p1)
    cm = matplotlib.cm.ScalarMappable(cmap=cm_redblue)
    if options.vesselsColorLimits is None:
      cm.set_clim(p0, p1)
    else:
      print('setting colors limits for vessels')
      print((options.vesselsColorLimits[0]))
      print((options.vesselsColorLimits[1]))
      cm.set_clim(vmin=options.vesselsColorLimits[0], vmax=options.vesselsColorLimits[1])
    
    edgecolors[mask[:,0]] = colors(edgedata[mask])
    nodecolors[nmask[:,0]] = colors(nodedata[nmask])
    #edgecolors[mask] = colors(edgedata[mask])
    #nodecolors[nmask] = colors(nodedata[nmask])
  elif data_name == 'shearforce':
    mask = mask & (edgedata>0)
    nmask = nmask & (nodedata>0)
    edgedata = edgedata[mask]
    nodedata = nodedata[nmask]
    unmapped_range = edgedata.min(), edgedata.max()
    edgedata = np.log10(edgedata)
    nodedata = np.log10(nodedata)
    #p0 = -4
    #p1 = -1
    p0 = np.amin(edgedata)
    p1 = np.amax(edgedata)
    cm = matplotlib.cm.ScalarMappable(cmap=matplotlib.cm.Spectral)
    if options.vesselsColorLimits is None:
      cm.set_clim(p0, p1)
    else:
      print('setting colors limits for vessels')
      print((options.vesselsColorLimits[0]))
      print((options.vesselsColorLimits[1]))
      cm.set_clim(vmin=options.vesselsColorLimits[0], vmax=options.vesselsColorLimits[1])
    edgecolors[mask[:,0]] = colors(edgedata)
    nodecolors[nmask[:,0]] = colors(nodedata)
  elif data_name == 'radius':
    mask = mask & (edgedata>0)
    nmask = nmask & (nodedata>0)
    edgedata = edgedata[mask]
    nodedata = nodedata[nmask]
    #edgedata = np.log10(edgedata)
    #nodedata = np.log10(nodedata)
    unmapped_range = edgedata.min(), edgedata.max()
    #cm = matplotlib.cm.ScalarMappable(cmap=matplotlib.cm.copper)
    cm = matplotlib.cm.ScalarMappable(cmap=matplotlib.cm.Spectral)
    p0 = np.amin(edgedata)
    p1 = np.amax(edgedata)
    if options.vesselsColorLimits is None:
      cm.set_clim(p0, p1)
    else:
      print('setting colors limits for vessels')
      print((options.vesselsColorLimits[0]))
      print((options.vesselsColorLimits[1]))
      cm.set_clim(vmin=options.vesselsColorLimits[0], vmax=options.vesselsColorLimits[1])
    edgecolors[mask[:,0]] = colors(edgedata)
    nodecolors[nmask[:,0]] = colors(nodedata)
  elif data_name == 'S_tot':
    #mask = mask & (edgedata>0)
    #nmask = nmask & (nodedata>0)
    edgedata = edgedata[mask]
    nodedata = nodedata[nmask]
    unmapped_range = edgedata.min(), edgedata.max()
    p0 = np.amin(edgedata)
    p1 = np.amax(edgedata)
    #print("p0: %f, p1: %f" % (p0,p1))
    #unmapped_range = (p0, p1)
    cm = matplotlib.cm.ScalarMappable(cmap=matplotlib.cm.jet)
    cm.set_clim(p0, p1)
    #edgedata = np.log10(edgedata)
    #nodedata = np.log10(nodedata)
    #p0 = -4#np.amin(edgedata)
    #p1 = -1#np.amax(edgedata)
    #cm = matplotlib.cm.ScalarMappable(cmap=matplotlib.cm.spectral)
    #cm.set_clim(p0, p1)
    edgecolors[mask] = colors(edgedata)
    nodecolors[nmask] = colors(nodedata)
  elif data_name == 'flow':
    mask = mask & (edgedata>0)
    nmask = nmask & (nodedata>0)
    edgedata = edgedata[mask]
    nodedata = nodedata[nmask]
    unmapped_range = edgedata.min(), edgedata.max()
    edgedata = np.log10(edgedata)
    nodedata = np.log10(nodedata)
    p0 = np.floor(np.amin(edgedata))
    p1 = np.ceil(np.amax(edgedata))
    cm = matplotlib.cm.ScalarMappable(cmap=matplotlib.cm.jet)
    
    if options.vesselsColorLimits is None:
      cm.set_clim(p0, p1)
    else:
      print('setting colors limits for vessels')
      print((options.vesselsColorLimits[0]))
      print((options.vesselsColorLimits[1]))
      cm.set_clim(vmin=options.vesselsColorLimits[0], vmax=options.vesselsColorLimits[1])
    edgecolors[mask[:,0]] = colors(edgedata)
    nodecolors[nmask[:,0]] = colors(nodedata)
  elif data_name == 'conductivitySignal':
    edgedata = edgedata[mask]
    nodedata = nodedata[nmask]
    unmapped_range = edgedata.min(), edgedata.max()
    p0 = np.amin(edgedata)
    p1 = np.amax(edgedata)
    cm = matplotlib.cm.ScalarMappable(cmap=matplotlib.cm.jet)
    cm.set_clim(p0, p1)
    edgecolors[mask[:,0]] = colors(edgedata)
    nodecolors[nmask[:,0]] = colors(nodedata)
  elif data_name == 'metabolicSignal':
    edgedata = edgedata[mask]
    nodedata = nodedata[nmask]
    unmapped_range = edgedata.min(), edgedata.max()
    p0 = np.amin(edgedata)
    p1 = np.amax(edgedata)
    cm = matplotlib.cm.ScalarMappable(cmap=matplotlib.cm.jet)
    cm.set_clim(p0, p1)
    edgecolors[mask[:,0]] = colors(edgedata)
    nodecolors[nmask[:,0]] = colors(nodedata)
  elif data_name == 'flags':
    edgecolors[mask & (flags & krebsutils.ARTERY).astype(np.bool)] = np.asarray((1., 0., 0.))
    nodecolors[nmask & (nflags & krebsutils.ARTERY).astype(np.bool)] = np.asarray((1., 0., 0.))
    edgecolors[mask & (flags & krebsutils.VEIN).astype(np.bool)] = np.asarray((0., 0., 1.))
    nodecolors[nmask & (nflags & krebsutils.VEIN).astype(np.bool)] = np.asarray((0., 0., 1.))
    edgecolors[mask & (flags & krebsutils.CAPILLARY).astype(np.bool)] = np.asarray((0., 1., 0.))
    nodecolors[nmask & (nflags & krebsutils.CAPILLARY).astype(np.bool)] = np.asarray((0., 1., 0.))
    for idx in vesselgraph.roots:
      nodecolors[idx] = np.asarray((1., 1., 0.))
    cm, unmapped_range = None, (None, None)
  vesselgraph.edges['colors'] = edgecolors
  vesselgraph.nodes['colors'] = nodecolors
  return cm, unmapped_range



#def addVesselTree(epv, vesselgraph, trafo, options):
#    edges = vesselgraph.edgelist
#    pos = vesselgraph['position']
#    rad = vesselgraph.edges['radius']
#    #print 'positions = ', np.amin(pos, axis=0), np.amax(pos, axis=0)
#    pos = transform_position(trafo, pos)
#    rad = transform_scalar(trafo, rad)
#    #print 'positions after trafo = ', np.amin(pos, axis=0), np.amax(pos, axis=0)
#    
#    if 'vessel_clip' in options:
#      clip = clipFactory(options.vessel_clip)
#    else:
#      clip = clipFactory(None)
#    #clip_vessels = [clipFactory(clips) for clips in kwargs.pop('vessel_clip', None)]
#
#    edgecolors = vesselgraph.edges['colors']
#    nodecolors = vesselgraph.nodes['colors']
#
#    class Styler(object):
#      @staticmethod
#      def edge_style(i, a, b):
#        c = edgecolors[i]
#        return "MkStyle(<%0.2f,%0.2f,%0.2f>)" % tuple(c)
#      @staticmethod
#      def node_style(i):
#        c = nodecolors[i]
#        return "MkStyle(<%0.2f,%0.2f,%0.2f>)" % tuple(c)
#
#    if 'colored_slice' in options:
#      ClipStyler = Styler
#    else:
#      class ClipStyler(object):
#        styleString = "pigment { color rgb<%0.2f,%0.2f,%0.2f> }" % defaultCrossSectionColor
#        @staticmethod
#        def edge_style(i, a, b):
#          return ClipStyler.styleString
#        @staticmethod
#        def node_style(i):
#          return ClipStyler.styleString
##	  ambient 0.05 * c
#    epv.pvfile.write("""
#    #macro MkStyle(c)
#    texture {
#	pigment {
#	  color rgb c
#	}
#	finish {
#	  specular 0.1
#      ambient 1.
#	}
#    }
#    #end
#    """)
#
#    #print pos.shape, rad.shape, edges.shape, clip_vessels
##    for clip in clip_vessels:
#    epv.addVesselTree(np.asarray(edges, dtype=np.int32),
#                      np.asarray(pos, dtype=np.float32),
#                      np.asarray(rad, dtype=np.float32),
#                      Styler, clip, ClipStyler)
#    #del Styler; del ClipStyler
#    #print 'write time: ', time.time(


def ComputeBoundingBox(vesselgroup, vesselgraph):
  if 'lattice' in vesselgroup:
    vess_ldgroup = vesselgroup['lattice']
    #wbbox = krebsutils.read_lattice_data_from_hdf(vess_ldgroup).worldBox
    fn=str(vess_ldgroup.file.filename)
    path=str(vess_ldgroup.name)
    print(("reading bounding box from file: %s at %s" %(fn,path)))
    
    Pyld = krebsutils.read_lattice_data_from_hdf_by_filename(fn, path)
    wbbox = Pyld.worldBox
    del(Pyld)
    print(wbbox)
  else:
    pos = vesselgraph['position']
    minval = np.amin(pos, axis=0)
    maxval = np.amax(pos, axis=0)
    wbbox = np.vstack((minval, maxval)).transpose().ravel()  # xmin ,xmax, ymin, ymax, zmin ,zmax ...
    print('WBBOX = ', wbbox)
  return wbbox
  
#  pos = vesselgraph['position']
#  minval = np.amin(pos, axis=0)
#  maxval = np.amax(pos, axis=0)
#  wbbox = np.vstack((minval, maxval)).transpose().ravel()  # xmin ,xmax, ymin, ymax, zmin ,zmax ...
#  print 'WBBOX = ', wbbox
#  return wbbox


#def renderScene(vesselgroup, imagefn, **kwargs):
#    vess_ldgroup = vesselgroup['lattice']
#    graph = krebsutils.read_vessels_from_hdf(vesselgroup, ['position', 'flags', 'radius', 'pressure'], return_graph=True)
#    colorfactory = kwargs.pop('colorfactory', make_pressure_color_arrays)
#    colorfactory(graph)
#
#    wbbox = ComputeBoundingBox(vesselgroup, graph)
#    trafo = calc_centering_normalization_trafo(wbbox)
#    zsize = (wbbox[5]-wbbox[4])
#
#    with EasyPovRayRender(**kwargs) as epv:
#      epv.setBackground(kwargs.pop('background',0.0))
#      cam = kwargs.pop('cam','topdown') # this stuff is copy pasted everywhere, should be refactored in a extra function
#      if cam in ('topdown', 'topdown_slice'):
#        cam_fov = 60.
#        cam_distance_factor = ComputeCameraDistanceFactor(cam_fov, kwargs['res'], wbbox)
#        epv.addLight(10*Vec3(1.7,1.2,2), 1., area=(4, 4, 3, 3), jitter=True)
#        if cam == 'topdown_slice':
#          kwargs.update(vessel_clip =('zslice', -201*trafo.w, 201*trafo.w),
#                        tumor_clip =('zslice', -100*trafo.w, 100*trafo.w))
#          epv.setCamera((0,0,cam_distance_factor*0.5*(200.*trafo.w+2.)), (0,0,0), cam_fov, up = 'y')
#        else:
#          epv.setCamera((0,0,cam_distance_factor*0.5*(zsize*trafo.w+2.)), (0,0,0), cam_fov, up = 'y')
#      else:
#        basepos = np.asarray((0.6,0.7,0.7))*(1./1.4)
#        epv.setCamera(basepos, (0,0,0), 90, up = (0,0,1))
#        num_samples_large_light = 10
#        num_samples_small_light = 3
#        epv.addLight(10*Vec3(0.7,1.,0.9), 0.8, area=(1., 1., num_samples_small_light, num_samples_small_light), jitter=True)
#        epv.addLight(10*Vec3(0.5,0.5,0.5), 0.6, area=(5., 5., num_samples_large_light, num_samples_large_light), jitter=True)
#        kwargs.update(vessel_clip = ('pie', 0.),
#                      tumor_clip = ('pie', -20*trafo.w))
#
#
#      addVesselTree(epv, graph, trafo = trafo, **kwargs)
#      epv.render(imagefn)




def render_different_data_types( vesselgroup, options):
  filenamepostfix = ''
  labels = {
    'flow' : '$log_{10}$ Flow Rate',
    'shearforce': '$log_{10}$ Shear Force',
    'hematocrit' : 'Hematocrit',
    'pressure' : 'Blood Pressure $kPa$',
    'S_tot' : 'Adaption Signal',
    'conductivitySignal' : 'Conductivity Signal',
    'metabolicSignal' : 'Metabolic Signal',
    'radius': 'Vesselradius $\mu$m',
  }
  graph = krebsutils.read_vessels_from_hdf(vesselgroup, ['position', 'flags', 'radius', 'nodeflags'] + options.datalist, return_graph=True)
  #nodeflags not good for apj.h5
  #numpy int64 bug!
  #graph = krebsutils.read_vessels_from_hdf(vesselgroup, ['position', 'flags', 'radius' ] + options.datalist, return_graph=True)
  #if vesselgroup.attrs.get('CLASS') == 'GRAPH':  
  #  vessel_ld = krebsutils.read_lattice_data_from_hdf(vesselgroup['lattice'])  
  #  options.wbbox = vessel_ld.GetWorldBox()
  #if vesselgroup.attrs.get('CLASS') == 'REALWORLD':    
  #  options.wbbox = np.max(np.asarray(vesselgroup['nodes/world_pos']),0)
  options.wbbox = ComputeBoundingBox(vesselgroup, graph)
  if options.filteruncirculated:
    graph = graph.get_filtered(edge_indices = myutils.bbitwise_and(graph['flags'], krebsutils.CIRCULATED))
  if options.filterradiushighpass>0:
    graph = graph.get_filtered(edge_indices = graph['radius']> filterradiushighpass)
    filenamepostfix = '_rhp'
  if options.filterradiuslowpass>0:
    print("lowpass filter activated:")
    graph = graph.get_filtered(edge_indices = graph['radius']< filterradiuslowpass)
    filenamepostfix = '_rlp'
  for data_name in options.datalist:
    if 'colorfactory' in options:
      colors_factory = options.colorfactory
      colors_factory(graph)
    
    cm, (datamin, datamax) = make_any_color_arrays(graph, data_name, options)
    fn = vesselgroup.file.filename
    options.imageFileName = splitext(basename(fn))[0]+'_'+ myutils.sanitize_posixpath(vesselgroup.name).replace('/','-')+'_'+data_name+filenamepostfix+'.'+ options.format
    print((options.imageFileName))
    with EasyPovRayRender(options) as epv:
      CreateScene2(vesselgroup,epv, graph, options)
      if options.noOverlay:
        epv.render(imagefn)
      else:
        RenderImageWithOverlay(epv, cm, labels[data_name], options)
