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

"""
  This is the main script in order to generate raytraced images of vessel networks.
  It submitts stuff via qsub.
  Can be configured for tumor runs as well as single vessel network files.
  It can make videos of the former.
"""
if __name__ == '__main__':
  import os.path, sys
  sys.path.append(os.path.join(os.path.dirname(os.path.realpath(__file__)),'..'))
  
from os.path import basename, splitext, join
import sys, os
import posixpath
import h5py
import numpy
import krebsutils
from mystruct import Struct
from copy import deepcopy
import myutils
import identifycluster

from krebs import povrayRenderSettings

def clientfunc(job, cwd):
  os.chdir(cwd)
  job.render()

def estimateRuntimeAndMemory(g):
  ''' time in hours. memory in mB '''
  print(('estimate for group: %s' % g))
  if('simType' in list(g.attrs.keys())):
    if g.attrs['simType'] == 'MTS':
      print('found MTS simulation')
      N=g['vessels/po2vessels'].shape[1]
  else:
    if 'po2vessels' in g:
      N = g['po2vessels'].shape[1]
    elif 'conc' in g:
      N = len(g.parent['vessels/edges/node_a_index'])
    else:
      if 'vessels' in g: g = g['vessels']
      N = len(g['edges/node_a_index'])
  t = (N*5. / 60.)/(100000)
  #m = (1200. * N) / (300000) #this seams to be to low for tumors!
  m = (2400. * N) / (300000)
  if m < 1000:
    m=1000
  return t, m


class RenderJob(object):
  def __init__(self, filename, group_name, postfix, params):
    self.fn = filename
    self.postfix = postfix
    self.group_name = group_name
    if identifycluster.getname() == 'snowden':
      my_threads = 16
    else:
      my_threads = 4
    
#    self.params = dict(
#      res=(1400,1400),
#      aa=4,
#      colored_slice=True,
#      out_alpha=True,
#      num_threads=my_threads, 
#      temp_file_dir = '/tmp',
#      cam = 'topdown'
#    )
#    self.params.update(params)
    params.threads = my_threads
    self.params = params
    print(("self.group_name: %s" % self.group_name))
    self.runtime_and_mem = estimateRuntimeAndMemory(f[self.group_name])

  @property
  def imageFilename(self):
    return '%s-%s%s.png' % (splitext(basename(self.fn))[0], myutils.sanitize_posixpath(self.group_name).replace('/','_'), ('_'+self.postfix) if self.postfix else '')

  def render(self):
    """ run povray. This should be called on the computing node. """
    with h5py.File(self.fn,'r') as f:
      if 'po2vessels' in f[self.group_name]:
        from krebs.povrayRenderOxygenDetailed import renderScene
        renderScene(f[self.group_name],
                    self.imageFilename,
                    self.params)

      elif 'tumor' in f[self.group_name]:
        from krebs.povrayRenderTumor import render_different_data_types
        self.params.timepoint = f[self.group_name].attrs.get('time')
        ''' check if we have cell '''
        if 'cells' in f[self.group_name]:
          render_different_data_types(f[self.group_name]['vessels'],
                    f[self.group_name]['tumor'],
                    self.imageFilename,
                    self.params, cell_group = f[self.group_name]['cells'])
        else:
          print('rendering bulktissue tumor')
          render_different_data_types(f[self.group_name]['vessels'],
                    f[self.group_name]['tumor'],
                    self.imageFilename,
                    self.params)
#      else:
#        from krebs.povrayRenderVessels import renderScene
#        renderScene(f[self.group_name],
#                    self.imageFilename,
#                    **self.params)
      #renderScene(drug_grp, imagefn, parameters)
      elif 'conc' in f[self.group_name]:
        from krebs.povrayRenderIff import renderScene
        renderScene(f[self.group_name],
                    self.imageFilename,
                    self.params)
      else:
        from krebs.povrayRenderVessels import render_different_data_types
        render_different_data_types(f[self.group_name],self.params )



if __name__ == '__main__':
  import qsub
  import argparse
  parser = argparse.ArgumentParser(description='Povray wrapper',
                                   formatter_class=argparse.ArgumentDefaultsHelpFormatter)
  
  parser.add_argument('vesselFileNames', nargs='+', type=argparse.FileType('r'), default=sys.stdin)
  parser.add_argument('grp_pattern')
  parser.add_argument('-p', '--povParamsSet', default=None, help='use parameters found in povrayRenderSettings.py')
  parser.add_argument("-d","--data", dest="datalist", help="which data (pressure, flow, shearforce, hematocrit) as comma separated list", default=['pressure'], action="store")
  parser.add_argument("-f","--filter-uncirculated", dest="filteruncirculated", help="filter uncirculated vessels", default=False, action="store_true")
  parser.add_argument("--filterradiushighpass", help='filter vessels from tree above this value', default = -1., type=float)
  parser.add_argument("--filterradiuslowpass", help='filter vessels from tree below this value',  default = -1., type=float)     
  parser.add_argument("--noOverlay", help='decide if mpl overlay is created', default = False, action="store_true")
  #note this would be helpfull for debuging, but needs data cache
  #not yet done  
  #parser.add_argument("--only_overlay", default = False, action="store_true")  
  parser.add_argument("--dpi", help='dpi for the rendering', default=300.)
  parser.add_argument("--format", help='output format of image', default='png', action="store")
  parser.add_argument("-c","--cam", help="camera mode: topdown, pie, topdown_slice, pie_only_cells, pie_only_vessels", default='topdown_slice', action="store", type=str)
  parser.add_argument("-u","--plot_auc", help="for area under curve, we have only a single timepoint", default=False, action="store_true")
  parser.add_argument("-a","--auto_colorscale", help=" ", default=False, action="store_true")  
  parser.add_argument("--fontcolor", help='fontcolor in overlay, use mpl style colors', default='black')  
  parser.add_argument("--temp_file_dir", help='dir for temp povray scene', default=None)
  parser.add_argument("--keep_files", help='keep tmp file?', default=False, action="store_true")
  parser.add_argument("--assumed_gamma", help=" ", default=1.0)
  parser.add_argument("--background", help="backgroundcolor matplotlib style", default = 'white')
  parser.add_argument("--ambient_color", help=" ", default=(0.1, 0, 0))
  parser.add_argument("--res", help="use comma seperated list of resx,resy ", default=(2048,2048))
  parser.add_argument("--num_threads", help=" ", type=int, default=7)
  parser.add_argument("--out_alpha", help=" ", default=False, action="store_true")
  parser.add_argument("--cam_distance_multiplier", help=" ", type=float, default=1.0 )
  parser.add_argument("--colored_slice", help=" ", default=True)
  parser.add_argument("--bigColorbar", help=" ", default=False, action="store_true")
  parser.add_argument("--planeZCoord", help='in case your render a data slice, this allows you to choose the position, should vary from -0.5 to +0.5', type=float, default=0.0)
  #parser.add_argument("--projection_plot", help=" ", default=True)
  parser.add_argument("--not_render_volume", help="For combined images", default=False, action="store_true")
  parser.add_argument("--not_render_vessels", help="For combined images", default=False, action="store_true")
  parser.add_argument("--timepoint", help="timepoint for tumor overlay", default=None)
  # maybe we need that in future?
  parser.add_argument("--logcolor", help="if set, the colorscale will be logarithmic", default=False, action="store_true")
  parser.add_argument("--vessel_clip", help="arguments are height above and below type of clip uasage (no =): 'zslice' -0.1 0.1", nargs=3,metavar=('type', 'arg1', 'arg2'), type=str,default=None)
  parser.add_argument("--tumor_clip", help="origin of tumor clipping", nargs=3, metavar=('x', 'y', 'z'),type=float,default=None)
  parser.add_argument("--clip_box", help="clip a box from vessels", nargs=6, metavar=('box_center_x', 'box_center_y', 'box_center_z', 'x_extent', 'y_extent', 'z_extent'),type=float, default=None)
  parser.add_argument("--clip_ball", help="clip a ball from vessels", nargs=4, metavar=('ball_x', 'ball_y', 'ball_z', 'radius'),type=float, default=None)
  parser.add_argument("--slice_pos", help="slice position on z axis in mu m", default=None, type=int)
  parser.add_argument("--cells", help="if activated, the VBL cells will be rendered", default=False, action="store_true")
  parser.add_argument("--cellsProperty", help="property of the cells to plot", default= "o2", type=str)
  parser.add_argument("--cellsColorLimits", help = "set border of visible data usage: simply name followed by 2 number no, bracket or quotations", nargs=2, metavar=('a', 'b'),type=float, default=None)
  parser.add_argument("--vesselsColorLimits", help = "set border of visible data usage: simply name followed by 2 number no, bracket or quotations", nargs=2, metavar=('a', 'b'),type=float, default=None)
  parser.add_argument("--imageFileName", help="name of output file", default='foo', type=str)
  parser.add_argument("--noLabel", help="if activated, the labels in the overlay will not be displayed", default=False, action='store_true')
  goodArguments, otherArguments = parser.parse_known_args()
  qsub.parse_args(otherArguments)
  
  """ some corrections on command line reads"""
  if not parser.get_default('datalist') == goodArguments.datalist:
    goodArguments.datalist= goodArguments.datalist.split(',')
  if not parser.get_default('res') == goodArguments.res:
    goodArguments.res= tuple(goodArguments.res.split(','))
  if goodArguments.vessel_clip is not None:
    goodArguments.vessel_clip[1] = float(goodArguments.vessel_clip[1])
    goodArguments.vessel_clip[2] = float(goodArguments.vessel_clip[2])
  """ read parameters from file """
  #create filename due to former standards
  filenames=[]
  for fn in goodArguments.vesselFileNames:
    filenames.append(fn.name)
  goodArguments.vesselFileNames = filenames
  pattern = goodArguments.grp_pattern
  postfix = ''
  try:
    if not goodArguments.povParamsSet is None:
      if not goodArguments.povParamsSet in dir(povrayRenderSettings):
        raise AssertionError('Unknown parameter set %s!' % goodArguments.povParamsSet)
      else:
        """ apply found parameters from file
            this overwrites the command line arguments!!!!
        """
        params_from_file = getattr(povrayRenderSettings, goodArguments.povParamsSet)
        for key in list(params_from_file.keys()):
          print(('found %s with %s in file\n' %(key,params_from_file[key])))
          if not key in goodArguments:
            raise AssertionError('Unknown key %s in file\n' % key)
          else:
            setattr(goodArguments,key,params_from_file[key])
          
    for fn in filenames:
        if not os.path.isfile(fn):
            raise AssertionError('The file %s is not present!'%fn)
  except Exception as e:
    print(e.message)
    sys.exit(-1)
  
  """ create job"""
  jobs = []
  a = jobs.append
  for fn in filenames:
    with h5py.File(fn,'r') as f:
      paths = myutils.walkh5(f, pattern)
      if goodArguments.plot_auc:
        path = myutils.walkh5(f, 'out0000')
        j = RenderJob(f.filename, path[0], postfix, goodArguments)
      for path in paths:
        j = RenderJob(f.filename, path, postfix, goodArguments)
        a(j)

  for job in jobs:
    t, m = job.runtime_and_mem
    print('submit %s, %i mb, %f h' % (job.imageFilename, m, t))
    qsub.submit(
      qsub.func(clientfunc, job, os.getcwd()),
      name='job_render_'+basename(job.imageFilename),
      num_cpus=job.params.threads,
      mem=('%iMB' % m),
      days=0.001)
