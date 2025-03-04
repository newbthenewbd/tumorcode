#!/usr/bin/env python2
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

#from plottools import Vec3
from vec import Vec3

import os
import mkstemp
import krebsutils
import povray as pv
import numpy as np
import math
import myutils

import matplotlib
'''
due to no graphics on the clusters, we have to use a differetn renderer
http://matplotlib.org/faq/usage_faq.html
'''
import identifycluster
if (identifycluster.getname()=='snowden' or identifycluster.getname()=='durga'):
  matplotlib.use('agg')
import matplotlib.pyplot
import mpl_utils

##############################################################################

def CallPovrayAndOptionallyMakeMPLPlot(epv, imagefn, cm, label, options):
    if options.overlay:
      RenderImageWithOverlay(epv, imagefn, cm, label, options)      
    else:
      epv.render(imagefn)

class Colormap(object):
  def __init__(self, name, limits, colors):
    self.value_bounds = limits
    self.colors       = colors
    self.name         = name

def matplotlibColormapToPovray(name, cm):
  import matplotlib.cm
  N = 256
  lims = cm.get_clim()
  colors = cm.to_rgba(np.linspace(lims[0],lims[1],N))
  colors = colors[:,:3] # skip alpha channel
  colors = np.power(colors, 2.4)
  return Colormap(name, lims, colors)

defaultCrossSectionColor = (0.9, 0.9, 0.9)
#defaultCrossSectionColor = (0., 0., 0.)

##############################################################################
class Transform(object):
  """
    Stores a uniform affine mapping.
    Transform is applied to the position X as (X - center) * w.
  """
  def __init__(self, center, w):
    self.center, self.w = np.asarray(center, dtype=float), w


def transform_scalar(trafo, s):
  return trafo.w * s

def transform_position(trafo, p):
  return (p - trafo.center) * trafo.w

def transform_ld(trafo, ld):
  ld = ld.Copy()
  ld.SetOriginPosition(ld.worldBox.reshape(3,2)[:,0] - trafo.center)
  ld.Rescale(trafo.w)
  return ld

def calc_centering_normalization_trafo(bbox_xxyyzz):
    '''
      We want to scale the dimensions of the sim data to the [-1/2,1/2] range.
      Mostly because so that we know where to place lights and camera.
    '''
    wb = np.asarray(bbox_xxyyzz)
    wb = bbox_xxyyzz
    wb = wb.reshape((3,2))
    sz = wb[:,1]-wb[:,0]
    center = 0.5*(wb[:,1]+wb[:,0])
    #center[2] = wb[2][0] # don't want that. want it centered in z, too
    #center = np.asarray((0.,0.,0.)) # WTF??? why????
    w = 1./max(*sz)
    return Transform(center, w)
##############################################################################

def ComputeCameraDistanceFactor(cam_fov, (W,H), wbbox):
    ''' how much distance to keep from an object to get it on screen completely.
        wbbox is only need for the size ratio along x and y axes.
        Camera is supposed to look along the z direction.'''
    cam_distance_factor = 1.02/math.tan(cam_fov*0.5*math.pi/180.)*0.5
    (object_w, object_h) = (wbbox[1]-wbbox[0], wbbox[3]-wbbox[2])
    ratio = float(W)/H
    object_ratio = object_w/object_h
    if (object_ratio < ratio):
      # The width of the screen (i.e. the displayed area in the z=0 plane
      # is adjusted to go from x = [-0.5, 0.5]. The object, i.e. vessel network, etc.
      # is also scaled into this range. However its y size may be taller than
      # the screen is high. Therefore we need a correction and go farther away
      # so that the entire y-range of the object is covered on screen.
      cam_distance_factor *= ratio
    return cam_distance_factor


##############################################################################
class VolumeData(object):
  '''
    Stores some information about a volume data set, which is here just a grid of float
    values and a bounding box. We also have a filename where it was written to
    in some povray format, and also a function name alias under which it is known
    to povray.
  '''
  def __init__(self, epv, data, worldbox):
    print 'VolumeData w. worldbox', worldbox
    self.data = np.asarray(data)  # in case we get a h5 dataset we want to con
    self.worldbox = worldbox
    self.spacing = (worldbox[0,1]-worldbox[0,0])/data.shape[0]
    self.max_grad_ = None
    self.value_bounds_ = None
    self.filename = None
    self.name = None

  @property
  def max_grad(self):
    if self.max_grad_ is not None: return self.max_grad_
    import krebsutils
    dmin, dmax = self.value_bounds
    grad = krebsutils.field_gradient(self.data, spacing = 1.)
    g = np.sqrt(np.sum(tuple(g*g for g in grad), axis=0))
    g = g.max() / (dmax-dmin + 1.e-24) # divide by data range because data range is mapped to 0, 1
    g *= 1./self.spacing
    self.max_grad_ = g
    return g

  @property
  def value_bounds(self):
    if self.value_bounds_ is not None: return self.value_bounds_
    a, b = self.data.min(), self.data.max()
#    diff = b-a
#    eps = 1.0e-6
#    a -= eps*diff
#    b += eps*diff
    self.value_bounds_ = (a,b)
    return self.value_bounds_



class EasyPovRayRender(object):
  '''
    Simplifying wrapper around the povray module.
    Keeps track of scene description files and deletes them on exit.
    Has some functions to set light, camera, and various entities to vis. data.
  '''

  def makeTmpFile(self, text=True, suffix='.pov'):
    args = dict(suffix=suffix,prefix='mwpov_main',text=text)
    if self.tempfiledir:
      args['dir'] = self.tempfiledir
    args['keep'] = self.params.keep_files
    tf = mkstemp.File(**args)
    self.tempfiles.append(tf)
    return tf

  def __enter__(self):
    return self

  def __exit__(self, type, value, traceback):
    self.clear()


  def __init__(self, params):
    self.params = params
    if 'temp_file_dir' in params:
      self.tempfiledir = params.temp_file_dir
    else:
      self.tempfiledir = None
    self.tempfiles = []
    tf = self.makeTmpFile()
    self.f = open(tf.filename, 'w')
    self.pvfile = pv.File(self.f)
    #self.pvfile.write('#include "rad_def.inc"')
    self.pvfile.write('#version 3.6;')
    pv.Item("global_settings",
            assumed_gamma = params.assumed_gamma,
            ambient_light = params.ambient_color,
            #radiosity = '{Rad_Settings(Radiosity_OutdoorHQ, 1, 1)}'
            ).write(self.pvfile)
    #self.pvfile.write("""sky_sphere { pigment {color rgb <1,1,1> } }""")


  def render(self, imgfn):
    # write
    #tf = mkstemp.File(suffix='.pov',prefix='mwpov_main',dir='.',text=True)
    #self.write(tf.filename)
    scenefilename = self.f.name
    self.f.close()
    # call povray
    povray = 'povray %s'
    if 'aa' in self.params:
      aa = self.params.aa
      aa = '+A +R%i' % aa  
    else:
      aa = ''
    if self.params.out_alpha:
      alpha = "+UA"
    else:
      alpha = ""
    num_threads = self.params.num_threads
    num_threads = ("+WT%i" % num_threads) if num_threads>1 else ""
    res = self.params.res
    res = '+W%i +H%i' % res
    imgfn = imgfn.replace('=',r'-') # povray does not like = in filenames
    cmd = povray % ('%s +FN8 %s %s -D %s +O"%s" "%s"' % (res,alpha,num_threads,aa,imgfn, scenefilename))
    print cmd
    os.system(cmd)
    self.clear()
    return imgfn


  def clear(self):
    for tf in self.tempfiles:
      tf.remove()
    self.tempfiles = []


  def setCamera(self, pos, lookat, fov, projection='perspective', **kwargs):
    W, H = self.params.res
    ratio = float(W)/H
    a = dict(
        angle = fov,
        location = Vec3(pos),
        look_at = Vec3(lookat),
        up = "<0,1,0>",
        right = "<-%f,0,0>" % ratio
    )
    up_vec = kwargs.pop("up", None)
    if up_vec:
      a['sky'] = up_vec
    pv.Camera(
      projection,
      **a
    ).write(self.pvfile)

  def addLight(self, pos, color, **kwargs):
    ls_args = (pos, ['color', Vec3(color)])
    area = kwargs.pop('area', None)
    if area:
      e1, e2, s1, s2 = area
      ls_args = ls_args + (['area_light', e1, e2, s1, s2],)
      ls_args = ls_args + (['adaptive', 1],)
      jitter = kwargs.pop('jitter', None)
      if jitter:
        ls_args = ls_args + ('jitter',)
    pv.LightSource(*ls_args).write(self.pvfile)

  def setBackground(self, color):
    pv.Background(color=Vec3(color)).write(self.pvfile)

  def addPlane(self, pos, normal, color):
    pv.Plane(
        Vec3(normal), Vec3(normal).dot(Vec3(pos)),
        pv.Pigment(
            color=Vec3(color)
        )
    ).write(self.pvfile)

#  def addFog(self, distance, color):
#    pv.Fog(
#        distance = distance,
#        color = Vec3(color)
#    ).write(self.pvfile)


  def addVesselTree(self, edges, pos, rad, style_object, clip_object, clip_style_object):
    tf = self.makeTmpFile()
    krebsutils.export_network_for_povray(
      edges, pos, rad, style_object, clip_style_object, clip_object, tf.filename)
    self.pvfile.write("#include \"%s\"" % tf.filename)


  def declareVolumeData(self, data, worldbox, ld = None):
#    if ld:
#      newdata = np.empty((data.shape[0]+1, data.shape[1], data.shape[2]), dtype = data.dtype)
#      newdata[0   ,:,:]    = data[0,:,:]
#      newdata[1:-1,:,:]   = 0.5*(data[1:,:,:]+data[:-1,:,:])
#      newdata[-1  ,:,:]   = data[-1,:,:]
#      data = newdata
#      newdata = np.empty((data.shape[0], data.shape[1]+1, data.shape[2]), dtype = data.dtype)
#      newdata[:,0   ,:]    = data[:,0,:]
#      newdata[:,1:-1,:]   = 0.5*(data[:,1:,:]+data[:,:-1,:])
#      newdata[:,-1  ,:]   = data[:,-1,:]
#      data = newdata
    if data.shape[2] == 1: # actually povary seems to be fine without this
      worldbox[-2] = -1.
      worldbox[-1] =  1.
      x, y, z = data.shape
      data = np.resize(data, (x, y, 2*z)) # replicate data into two z-layers. The two-dimensional image plane where the volume dataset is cut lies in-between.
    wb = worldbox.reshape((3,2))
    vd = VolumeData(self, data, wb)
    # writing of the volume data takes place here
    tf = self.makeTmpFile(suffix='.df3') # create and register a temporary file which holds the data
    vd.filename = tf.filename # assign the filename
    pv.writeArrayAsDensityFile(vd.filename, vd.data, vd.value_bounds)
    # declare a function which references the data
    vd.name = os.path.splitext(os.path.basename(vd.filename))[0].upper()
    pv.Declare(vd.name, pv.Function(
        pv.Pattern(
        'density_file df3 "%s"' % vd.filename,
        'interpolate 1',
        ['scale', (wb[:,1]-wb[:,0])],
        ['translate', (wb[:,0])],
      )
      )).write(self.pvfile)
    return vd


  def declareColorMap(self, cm):
    colors = cm.colors
    values = np.linspace(0., 1., colors.shape[0])
    s = '\n'.join(('[%f color <%f,%f,%f>]' % (v,r,g,b))
                for (v,(r,g,b)) in zip(values, colors))
    pv.Declare(
      cm.name,
      pv.String('color_map\n{\n%s\n}' % s)
    ).write(self.pvfile)


  def addIsosurface(self, volumedata, level, style_object, clip_object, clip_style_object):
    vb = volumedata.value_bounds
    wb = volumedata.worldbox

    o = pv.Isosurface(
      pv.Function('-%s(x,y,z)' % (volumedata.name)),
      ['max_gradient', volumedata.max_grad],
      pv.ContainedBy(
          pv.Box(
              wb[:,0], wb[:,1]
          )
      ),
      ['threshold', -(level-vb[0])/(vb[1]-vb[0])],
      ['all_intersections'],
      #['scale', (wb[:,1]-wb[:,0])],
      #['translate', (wb[:,0])],
    )
    o = pv.Object(o, style_object())
    if clip_object:
      s = krebsutils.povray_clip_object_str(clip_object, str(clip_style_object))
      if s:
        o = pv.Intersection(o, s)
    o.write(self.pvfile)


  def addVolumeDataSlice(self, volumedata, origin, normal, colormap):
    vb = volumedata.value_bounds
    cb = colormap.value_bounds
    a = (vb[0]-cb[0])/(cb[1]-cb[0])
    m = (vb[1]-vb[0])/(cb[1]-cb[0])
    style = """
      texture {
        pigment {
          function { %s + %s*%s(x,y,z) }
          color_map { %s }
        }
        finish {
          specular 0.
          ambient 1.
        }
      }""" % (a, m, volumedata.name, colormap.name)
    o = pv.Plane(pv.Vector(*normal), np.dot(origin, normal),
                 pv.ClippedBy(
                    pv.Box(
                      volumedata.worldbox[:,0], volumedata.worldbox[:,1]
                    )
                 ),
                 style)
    o.write(self.pvfile)



  def write(self, fn):
    pass
    #open(fn, 'w').write(self.f.getvalue())


##############################################################################
## We want to clip away some parts of the scene i.e. in order to produce the
## "slice" renderings or the "pie" renderings. For this, i use objects which
## store information about the clipping planes and which are considered where
## the sim data is written as povray file
##############################################################################

v3_ = lambda x: x #numpy.asarray(x, dtype=numpy.float32)

def ClipKuchen(v0, v1, o):
  return (krebsutils.ClipShape.pie, v3_(v0), v3_(v1), v3_(o))

def ClipSlice(v0, v1, o0, o1):
  return (krebsutils.ClipShape.slice, v3_(v0), v3_(v1), v3_(o0), v3_(o1))

def ClipNone():
  return (krebsutils.ClipShape.none,)

def clipFactory(args):
  if not args or not args[0]: return ClipNone()
  if 'pie' == args[0]:
    a = args[1]
    a = np.asarray([a,a,0])
    clip = ClipKuchen((1,0,0),(0,1,0),a)
  elif 'zslice' == args[0]:
    a, b = args[1:]
    a = np.asarray([0,0,a])
    b = np.asarray([0,0,b])
    clip = ClipSlice((0,0,1),(0,0,-1),b,a)
  elif 'yslice' == args[0]:
    a, b = args[1:]
    a = np.asarray([0,a,0])
    b = np.asarray([0,b,0])
    clip = ClipSlice((0,1,0),(0,-1,0),b,a)
  elif 'xslice' == args[0]:
    a, b = args[1:]
    a = np.asarray([a,0,0])
    b = np.asarray([b,0,0])
    clip = ClipSlice((1,0,0),(-1,0,0),b,a)   
  return clip


##############################################################################
## Interoperability with matplotlib ...
##############################################################################
''' if cm=None, we only plot a sizebar'''
#def OverwriteImageWithColorbar(options,image_fn, cm, label, output_filename, wbbox, fontcolor = 'black', dpi = 90.):  
def OverwriteImageWithColorbar(options,image_fn, cm, label, output_filename): 
  '''
    overlays a small colorbar and adds a label on top of the image and writes it over the original location
  '''
  rc = matplotlib.rc
  fontcolor=options.fontcolor
  dpi = options.dpi
  wbbox = options.wbbox
  rc('lines', color = fontcolor)
  rc('text', color = fontcolor)
  rc('axes', edgecolor = fontcolor, labelcolor = fontcolor)
  rc('xtick', color = fontcolor)
  rc('ytick', color = fontcolor)
  rc('axes', facecolor = 'none')
  #rc('font', size = 10.)
  rc('savefig', facecolor = 'none', edgecolor = 'none') # no background so transparency is preserved no matter what the config file settings are
  img = matplotlib.image.imread(image_fn)
  resy, resx, _ = img.shape
  mytextsize=resx/float(dpi)*4
  if not options.cam == 'pie':
    fig = matplotlib.pyplot.figure(figsize = (resx/dpi, resy/dpi*1.1), dpi=dpi)
    ax = fig.add_axes([0.0, 0.05, 1, 1.0])
  else:
    fig = matplotlib.pyplot.figure(figsize = (resx/dpi, resy/dpi*1.0), dpi=dpi)
    ax = fig.add_axes([0.0, 0.0, 1, 1.0]) #[left, bottom, width, height] 
  ax.imshow(img, interpolation = 'nearest')
#  ax.yaxis.set_visible(False)
#  ax.xaxis.set_visible(False)
  ax.yaxis.set_visible(True)
  ax.xaxis.set_visible(True)
  ax.set_axis_off()
  #measured in fractions of figure width and height
  if not cm==None:
    ax2 = fig.add_axes([0.05, 0.05, 0.26, 0.018]) # left bottom width height
    c = np.linspace(0, 1, 256).reshape(1,-1)
    c = np.vstack((c,c))
    ax2.imshow(c, aspect='auto', cmap = cm.get_cmap(), vmin = 0, vmax = 1)
    ax2.yaxis.set_visible(False)
    xticks = np.linspace(0., 256., 5)
    #xticklabels = [ myutils.f2s(v,prec=1) for v in np.linspace(*cm.get_clim(), num = 5) ]
    ''' TODO:
        border of colorbar 
        still not resolution independent
    '''
    xticklabels = [ '%0.1f'%v for v in np.linspace(*cm.get_clim(), num = 5) ] 
    
    ax2.set(xticks = xticks)
    ax2.set(xticklabels=xticklabels)
    ax2.tick_params(labelsize=mytextsize/2, colors='black')
    #fig.text(0.2, 0.99, label, weight='bold', size='xx-small', va = 'top')
    
    ax2.text(0.5,-0.09,label,
             horizontalalignment='left',
             verticalalignment='bottom',
             transform=ax.transAxes,
             size=mytextsize*0.7,
             fontweight='bold')
  ''' length of ax is in dots
  how many dots correlates to 200mu m?
  1 pixel length im inch = 1/float(resx)/float(dpi)
  '''
  if options.cam in ('topdown', 'topdown_slice'):
    #haven't thought about adjustion the sizebar for rotated systems
    '''resx units = x_length_in_mum
    '''
    x_length_in_mum = abs(wbbox[1]-wbbox[0])
    y_length_in_mum = abs(wbbox[3]-wbbox[2])
    length_of_size_bar_in_mum = 250;
    length_in_data_space = float(resx)*length_of_size_bar_in_mum/x_length_in_mum
    length_in_data_spaceY = float(resy)*length_of_size_bar_in_mum/y_length_in_mum    
    mpl_utils.add_sizebar(ax,
                          color = 'black',
                          size=length_in_data_space,
                          text=r'$%i\mu m$'% length_of_size_bar_in_mum,
                          myfontsize=mytextsize/2,
                          size_vertical=0.05*length_in_data_space,
                          )
  if not output_filename:
    output_filename = image_fn
  ''' could be used to cut frames '''
#  from matplotlib.transforms import Bbox
#  bbox = ax.get_window_extent().transformed(fig.dpi_scale_trans.inverted())
#  width, height = bbox.width, bbox.height
#  bbox0 = Bbox.from_extents([0.1,0.1,2.9,2.9])
  fig.savefig(output_filename, dpi=dpi, bbox_inches=None ) # overwrite the original


def RenderImageWithOverlay(epv, imagefn, colormap, label, options):
  tf = mkstemp.File(suffix='.png', prefix='mwpov_', text=False, keep=True) 
  epv.render(tf.filename)
  #plotsettings = dict(myutils.iterate_items(kwargs, ['dpi','fontcolor','wbbox'], skip=True))    
  OverwriteImageWithColorbar(options,tf.filename, colormap, label, output_filename = imagefn)
