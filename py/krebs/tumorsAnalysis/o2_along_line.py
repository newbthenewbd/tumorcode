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
  
import os, sys
from os.path import join, basename, dirname, splitext
sys.path.append(os.path.join(os.path.dirname(os.path.realpath(__file__)),'../..'))

import krebsutils
#import extractVtkFields
#import pprint
import numpy as np
import h5py
#import identifycluster
import myutils
import multiprocessing
import scoop
import matplotlib
#matplotlib.use('agg')
from matplotlib.backends.backend_pdf import PdfPages
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D

eps_tube = 10


''' ARTERY
initial seed at: 240,400,-310
vessels at state 520
              *
              *
              * 74
              *
              *
             299
           *    *
edge:492  *      * edge: 1215
         *        *
        *          *
        340        1357  
vessels at state 538
              *
              *
              * 3508
              *
              *
             299
           *    *
edge:1216  *      * edge: 493
         *        *
        *          *
        340        1357  
'''
artery_p1 = np.asarray([216,459,-324])
artery_p2 = np.asarray([223,383,-370])
artery_p1 = np.asarray([195,356.5,-424.5])
artery_p2 = np.asarray([195,506.6,-318.4])
''' orthogonal'''
artery_p3 =np.asarray([286,394,-315])
artery_p4 =np.asarray([291,341,-241])

''' VEIN
initial seed at: 360,180,-310
vessels at state 605
             364
           *    *
edge:553  *      * edge: 552
         *        *
        *          *
        3026      22  
'''

vein_parallel_p1 = np.asarray([350,150,-370])
vein_parallel_p2 = np.asarray([344,191,-262])
vein_parallel_p1 = np.asarray([349,157,-350])
vein_parallel_p2 = np.asarray([344,185,-281])

vein_ortho_p1 = np.asarray([350,248,-327])
vein_ortho_p2 = np.asarray([327,78,-283])

metadata_dict = dict()
metadata_dict['norm'] = 'maximum norm'
metadata_dict['eps_tube'] = eps_tube
metadata_dict['number_of_sampling_points'] = 30
'''
      this creates sample points along the line
      from starting_pos to end_pos
      returns the sampling points and their distance along the line
  '''
def get_sample_points_along_line(pos_a, pos_b, number_of_samples=2):
  metadata_dict['starting_pos'] = pos_a
  metadata_dict['end_pos'] = pos_b
  positions=[]
  factors = []
  distances = []
#  print(pos_a)
#  print(pos_b)
#  print(pos_b-pos_a)
#  print(number_of_samples)
  for i in range(number_of_samples):
#    print(i)
    factor= i/(float(number_of_samples)-1)
#    print("factor: %f" %factor)
    factors.append(factor)
    new_sample_pos = pos_a+ factor*(pos_b-pos_a)
    positions.append(new_sample_pos);
    distances.append(np.linalg.norm(np.asarray(new_sample_pos)- pos_a))
#  print(positions)
  return (np.asarray(positions), np.asarray(distances))
'''
  checks which indices are within eps_tube around the line
  
  returns the indeces an their distances
'''
def is_index_good(sample_pos):
  array_of_cell_centers=scoop.shared.getConst('cell_center_pos_')
  box_length_of_max_norm=scoop.shared.getConst('box_length_of_max_norm')
  list_of_good_indeces=[]
  #print(array_of_cell_centers.shape)
  ''' euclidean norm'''
#  for (i,aPos) in enumerate(array_of_cell_centers[:,0:3]):
#    #print('aPos')
#    #print(aPos)
#    distance_from_sample_pos_to_a_cell_center_pos_i = np.linalg.norm(np.asarray(aPos) -sample_pos, axis=0)
#    if(distance_from_sample_pos_to_a_cell_center_pos_i<eps_tube):
#      list_of_good_indeces.append(i)
#  return list_of_good_indeces
  ''' max norm'''
  for (i,aPos) in enumerate(array_of_cell_centers[:,0:3]):
    #print('aPos')
    #print(aPos)
    #distance_from_sample_pos_to_a_cell_center_pos_i = np.linalg.norm(np.asarray(aPos) -sample_pos, axis=0)
    distance_from_sample_pos_to_a_cell_center_pos_i = np.linalg.norm(np.asarray(aPos) -sample_pos, np.inf, axis=0)
    if(distance_from_sample_pos_to_a_cell_center_pos_i<eps_tube):
      list_of_good_indeces.append(i)
  return list_of_good_indeces
      
''' this is my development function
'''
#def sample_line_artery(quantity_name, group_name):
#  print('sample_line_artery called with')
#  print('quantity_name: %s \t group_name: %s' % (quantity_name, group_name))
#  print(goodArguments)
#  with h5py.File(goodArguments.vbl_simulation_file_name, 'r') as f:
#  
#    datalist = map(lambda s: s, map(str.strip, goodArguments.datalist.split(',')))
#    
#    vesselgroup = f[os.path.join(group_name, 'vessels')]
#    graph = krebsutils.read_vessels_from_hdf(vesselgroup, ['position', 'radius', 'hematocrit', 'pressure', 'flow', 'flags','shearforce'] + datalist, return_graph=True)
#    cell_center_pos = np.asarray(f[os.path.join(group_name, 'cells/cell_center_pos')])
#    cell_o2_mass = np.asarray(f[os.path.join(group_name, 'cells/o2')])
#    cell_radii = np.asarray(f[os.path.join(group_name, 'cells/cell_radii')])
#    cell_pH = np.asarray(f[os.path.join(group_name, 'cells/pH_ex')])
#    index_of_nearest_vessel = np.asarray(f[os.path.join(group_name, 'cells/index_of_nearest_vessel')])
#    index_of_nearest_vessel = index_of_nearest_vessel[:,0]  
#    distance_to_nearest_vessel = np.asarray(f[os.path.join(group_name, 'cells/distance_to_nearest_vessel')])
#    distance_to_nearest_vessel = distance_to_nearest_vessel[:,0]  
#    print('****** important points *************')
#    a=graph.edgelist[521]
#    print('a: %s pos_a: %s pos_b: %s' % (a,graph['position'][a[0]],graph['position'][a[1]]))
#    b=graph.edgelist[1244]
#    print('b: %s pos_a: %s pos_b: %s' % (b,graph['position'][b[0]],graph['position'][b[1]]))
#    
#    print('cell_o2_mass shape:')
#    cell_o2_mass=cell_o2_mass[:,0]
#    print(cell_o2_mass.shape)
#    
#    print('cell_radii_shape:')
#    cell_radii=cell_radii[:,0]
#    print(cell_radii.shape)
#    # pg/ mum^3
#    cell_o2_concentration = cell_o2_mass/ (4/float(3)* np.pi*np.power(cell_radii,3))
#    #cell_o2_concentration = cell_o2_mass
#    volume_o2_ml = cell_o2_concentration/(1.429*1e9)
#    #volume_o2_ml = cell_o2_mass/1.429
#    ''' o2 density 1.429 g/L --> 1.429*10^9 pg/ml
#        1cm^3 = 10^12 (mum^3)
#    '''
#    solubility = 3.1e-3 #ml O2/cm^3 mmHg
#    #solubility = 2.8e-3 #ml O2/cm^3 mmHg
#    #solubility = 1.1e-4 #ml O2/cm^3 mmHg
#    solubility = solubility*1e-12 #ml O2/mum^3 mmHg
#    #volume_density = 1.429e9 #pg/ml
#    #x = cell_o2_concentration/volume_density # ml / mum^3
#    
#    #cell_po2 = x/solubility
#    
#    if quantity_name=='o2':
#      quantity_to_average = volume_o2_ml/solubility
#    if quantity_name=='pH_ex':
#      quantity_to_average = cell_pH
#    #quantity_to_average = cell_o2_mass/solubility
#    #quantity_to_average = cell_po2
#    #quantity_to_average = cell_o2_concentration
#    #quantity_to_average = cell_o2_mass
#    print('cell_center_pos')
#    if scoop.IS_RUNNING:
#      if not np.asarray(scoop.shared.getConst('cell_center_pos_')).any():
#        scoop.shared.setConst(cell_center_pos_=cell_center_pos)
#    
#    
#    starting_pos=artery_p1
#    end_pos=artery_p2
#    
#    print(goodArguments.vbl_simulation_file_name)
#    print(goodArguments.grp_pattern)
#    
#    print("sample along line from:")
#    print("%s to %s" % (starting_pos, end_pos))
#    #f = h5py.File(goodArguments.vbl_simulation_file_name, 'r')
#    #vesselgroup = f[os.path.join(goodArguments.grp_pattern, 'vessels')]
#    #graph = krebsutils.read_vessels_from_hdf(vesselgroup, ['position', 'radius', 'hematocrit', 'pressure', 'flow', 'flags','shearforce'] + datalist, return_graph=True)
#    ''' these are the interesting vessels for the artery'''
#    interesting_vessels = [492, 1215]
#    edges = graph.edgelist
#    pos = graph['position']
#    for vessel in interesting_vessels:
#      print("edge: %i nodes: %s" %(vessel,edges[vessel]))
#      this_edges = edges[vessel]
#      print("node: %i, pos: %s" %(this_edges[0],pos[this_edges[0]]))
#      print("node: %i, pos: %s" %(this_edges[1],pos[this_edges[1]]))
#    print("pos 252: %s" % pos[252])
#    print("pos 293: %s" % pos[293])
#    print("pos 1259: %s" % pos[1259])
#    
#    sample_pos, distances = get_sample_points_along_line(starting_pos,end_pos,metadata_dict['number_of_sampling_points'])
#    box_length_of_max_norm = distances[1]*0.5
#    print(distances)
#    if scoop.IS_RUNNING:
#      if not scoop.shared.getConst('box_length_of_max_norm'):
#        scoop.shared.setConst(box_length_of_max_norm=box_length_of_max_norm)
#    print('box_length_of_max_norm %f' % box_length_of_max_norm )
#    #cell_center_pos = np.asarray(f[os.path.join(goodArguments.grp_pattern, 'cells/cell_center_pos')])
#    #print('cell_center_pos')
#    #scoop.shared.setConst(cell_center_pos_=cell_center_pos)
#    lists = list(scoop.futures.map(is_index_good, sample_pos))
#    for (aList, aSamplePos) in zip(lists,sample_pos):
#      print('for pos: %s found %i points in eps range' % (aSamplePos,len(aList)))
#      
#    ''' average '''
#    average_value = []
#    errors = []
#    
#    for (aList, aSamplePos) in zip(lists,sample_pos):
#      this_avg = np.average(quantity_to_average[aList])
#      average_value.append(this_avg)
#      #errors.append(np.sqrt(1/float(len(aList)))*this_avg)
#      errors.append(np.std(quantity_to_average[aList]))
#        
#    print('finished sample line artery')
#  return (np.asarray(average_value), np.asarray(errors), np.asarray(distances))

#def sample_line_artery_ortho(**keywords):
#  starting_pos=artery_p3
#  end_pos=artery_p4
#  
#  print(goodArguments.vbl_simulation_file_name)
#  print(goodArguments.grp_pattern)
#  
#  print("sample along line from:")
#  print("%s to %s" % (starting_pos, end_pos))
#  #f = h5py.File(goodArguments.vbl_simulation_file_name, 'r')
#  #vesselgroup = f[os.path.join(goodArguments.grp_pattern, 'vessels')]
#  #graph = krebsutils.read_vessels_from_hdf(vesselgroup, ['position', 'radius', 'hematocrit', 'pressure', 'flow', 'flags','shearforce'] + datalist, return_graph=True)
#  ''' these are the interesting vessels for the artery'''
#  interesting_vessels = [492, 1215]
#  edges = graph.edgelist
#  pos = graph['position']
#  for vessel in interesting_vessels:
#    print("edge: %i nodes: %s" %(vessel,edges[vessel]))
#    this_edges = edges[vessel]
#    print("node: %i, pos: %s" %(this_edges[0],pos[this_edges[0]]))
#    print("node: %i, pos: %s" %(this_edges[1],pos[this_edges[1]]))
#  print("pos 252: %s" % pos[252])
#  print("pos 293: %s" % pos[293])
#  print("pos 1259: %s" % pos[1259])
#  
#  sample_pos, distances = get_sample_points_along_line(starting_pos,end_pos,metadata_dict['number_of_sampling_points'])
#  box_length_of_max_norm = distances[1]*0.5
#  print(distances)
#  if scoop.IS_RUNNING:
#    scoop.shared.setConst(box_length_of_max_norm=box_length_of_max_norm)
#  print('box_length_of_max_norm %f' % box_length_of_max_norm )
#  cell_center_pos = np.asarray(f[os.path.join(goodArguments.grp_pattern, 'cells/cell_center_pos')])
#  #print('cell_center_pos')
#  scoop.shared.setConst(cell_center_pos_=cell_center_pos)
#  lists = list(scoop.futures.map(is_index_good, sample_pos))
#  for (aList, aSamplePos) in zip(lists,sample_pos):
#    print('for pos: %s found %i points in eps range' % (aSamplePos,len(aList)))
#    
#  ''' average '''
#  average_value = []
#  errors = []
#  
#  for (aList, aSamplePos) in zip(lists,sample_pos):
#    this_avg = np.average(quantity_to_average[aList])
#    average_value.append(this_avg)
#    #errors.append(np.sqrt(1/float(len(aList)))*this_avg)
#    errors.append(np.std(quantity_to_average[aList]))
#      
#  print('finished sample line artery')
#  return (np.asarray(average_value), np.asarray(errors), np.asarray(distances))


def get_cylinder_coordinate_relative_to_vessel_x(vessel_x,z_min=60, z_max=70,r_min=0.5,r_max=5,phi_min=0,phi_max=0.1):
  edges = graph.edgelist
  pos = graph['position']
  zero_center = pos[edges[vessel_x][0]]
  mid_point= zero_center+0.5*(pos[edges[vessel_x][1]]-pos[edges[vessel_x][0]])
  print('mid_point: %s ' %mid_point)
  
#  zero_center = pos[edges[vessel_x][1]]
  print('length_of vessel: %f ' % np.linalg.norm(pos[edges[vessel_x][1]]-pos[edges[vessel_x][0]])) #should be 130
  '''shift everything to that point'''
  shifted_pos = cell_center_pos-zero_center
  '''only positive z values'''
  #good_indeces_plane = np.where(np.logical_and(shifted_pos[:,2]>60.0, shifted_pos[:,2]<70.0))
  #shifted_pos = shifted_pos[good_indeces_plane]
  r=np.sqrt(shifted_pos[:,0]*shifted_pos[:,0]+shifted_pos[:,1]*shifted_pos[:,1])
  #indeces_in_cylinder = np.where(r<30.0)  
  z=shifted_pos[:,2]
  #z=z[indeces_in_cylinder]
  isInQuadrantII_or_II = shifted_pos[:,0]<0
  isInQuadrantIV = (shifted_pos[:,0]>0) & (shifted_pos[:,1]<0)
  phi= np.arctan(shifted_pos[:,1]/shifted_pos[:,0])
  #phi= shifted_pos[:,1]/shifted_pos[:,0]
  phi[isInQuadrantII_or_II] = phi[isInQuadrantII_or_II]+np.pi
  phi[isInQuadrantIV] = phi[isInQuadrantIV]+2*np.pi
  print(r.shape)
  #indeces_in_cylinder = np.where(np.logical_and(np.logical_and(shifted_pos[:,2]>65-z_extent, shifted_pos[:,2]<65+z_extent,r<r_max),r>r_min))
  indeces_in_cylinder = np.where(np.logical_and(r<r_max, r>r_min))
  return (r,z,phi, indeces_in_cylinder[0])
  
def sample_in_orthogonal_plane(index_of_vessel_to_sample, pp):
  fig1, ax1 = plt.subplots(1)
  print('shape of index_of_nearest_vessel')
  print(index_of_nearest_vessel.shape)
  cell_indeces_at_vessel = np.where(index_of_nearest_vessel == index_of_vessel_to_sample)
  print("found %i indeces" % len(cell_indeces_at_vessel[0]))
  ''' rescale '''
  distances_to_single_vessel = distance_to_nearest_vessel[cell_indeces_at_vessel]
#  for aIndex in cell_indeces_at_vessel[0]:
#    print(aIndex)
  #min_distance_to_nearest_vessel = np.min(distances_to_single_vessel)
  #max_distance_to_nearest_vessel = np.max(distances_to_single_vessel)
  min_distance_to_nearest_vessel = 2.5
  max_distance_to_nearest_vessel = 40.0
  print('min: %f, max: %f' %(min_distance_to_nearest_vessel,max_distance_to_nearest_vessel))
  
  max_endity_value_of_cells = 200
  min_endity_value_of_cells = 10
  
  quantity_to_average_for_single_vessel = quantity_to_average[cell_indeces_at_vessel]
  ''' this is not showing something -> I try it the other way round'''
  
  (r,z,phi, good_indeces_in_cylinder) = get_cylinder_coordinate_relative_to_vessel_x(index_of_vessel_to_sample,z_min=60, z_max=70,r_min=1.0,r_max=5,phi_min=0,phi_max=0.1)
  #good_in_pie = np.where(np.logical_and(np.logical_and(np.logical_and(phi>0,phi<0.1), z>50),z<80))
  ax1.hist(phi,30)
  ax1.set_title('phi')
  pp.savefig()
  ax1.clear()
  ax1.hist(r,30)
  ax1.set_title('r')
  pp.savefig()
  ax1.clear()
  ax1.hist(z,30)
  ax1.set_title('z')
  pp.savefig()
  z_min = 60
  z_max = 70
  phi_min = 0.5
  phi_max = 1
  d_phi=2*np.pi/7
  for direction in np.arange(0,2*np.pi, d_phi):
    ax1.clear()
    data_points = []
    dr = 5
    my_ranges= np.arange(0,40,dr)
    for aRange in my_ranges:
      again_good_indeces = (r>aRange)&(r<aRange+dr)&(z>z_min)&(z<z_max)&(phi>direction)&(phi<direction+d_phi)
      #data_points.append(np.average(np.logical_and(np.logical_and(np.logical_and(r>aRange,r<aRange+1), z>z_min),z<z_max)))
      data_points.append(quantity_to_average[again_good_indeces])
    ax1.boxplot(data_points)
#  good_r5 = np.where()  
#  good_r10 = np.where(np.logical_and(np.logical_and(np.logical_and(r>7,r<9), z>z_min),z<z_max))  
#  good_r15 = np.where(np.logical_and(np.logical_and(np.logical_and(r>9,r<11), z>z_min),z<z_max))  
#  a=np.average(quantity_to_average[good_r5])
#  b=np.average(quantity_to_average[good_r10])
#  c=np.average(quantity_to_average[good_r15])
  #ax1.hist(quantity_to_average[good_in_pie])
  #r_in_cylinder = r[good_indeces]
  #z_in_cylinder = z[good_indeces]
  #phi_in_cylinder = phi[good_indeces]
  #ax1.scatter(r[good_in_pie],quantity_to_average[good_in_pie])
  #ax1.scatter(range(len(data_points)),data_points)
#  for direction in np.arange(0,3, 0.2):
#    print(direction)
#    ax1.clear()
#    again_good_indeces = (r>0)&(r<5)&(phi>direction)&(phi<direction+0.1)&(z>20)&(z<120)
#    ax1.scatter(r[again_good_indeces],quantity_to_average[again_good_indeces])
#    ax1.set_title(r'direction $\varphi = %f' % direction)
  #ax1.hist(distances_to_single_vessel)
#  if goWithDistance:
#    ax1.set_ylabel(r'pO2 / mmHg')
#    ax1.set_xlabel(r' distance to nearest vessle/ $\mu m$')
#  else:
#    ax1.set_xlabel(r'pO2 / mmHg')
#    ax2.set_ylabel(r' distance to nearest vessle/ $\mu m$')
#    plt.title('file: %s \n at %s' % (goodArguments.vbl_simulation_output_filename, goodArguments.output_grp_name))
  #pp.savefig()
  #plt.grid()
#    if interactive:
  
#    else:
    
    pp.savefig()
  
def sample_line_general(quantity_name, group_name, starting_point, end_point):
  print('sample_line_general for points:')
  print('starting point:')
  print(starting_point)
  print('end_point:')
  print(end_point)
  print('quantity_name: %s \t group_name: %s' % (quantity_name, group_name))
  print(goodArguments)
  with h5py.File(goodArguments.vbl_simulation_file_name, 'r') as f:
  
    datalist = [s for s in list(map(str.strip, goodArguments.datalist.split(',')))]
    
    vesselgroup = f[os.path.join(group_name, 'vessels')]
    graph = krebsutils.read_vessels_from_hdf(vesselgroup, ['position', 'radius', 'hematocrit', 'pressure', 'flow', 'flags','shearforce'] + datalist, return_graph=True)
    cell_center_pos = np.asarray(f[os.path.join(group_name, 'cells/cell_center_pos')])
    cell_o2_mass = np.asarray(f[os.path.join(group_name, 'cells/o2')])
    cell_radii = np.asarray(f[os.path.join(group_name, 'cells/cell_radii')])
    cell_pH = np.asarray(f[os.path.join(group_name, 'cells/pH_ex')])
    index_of_nearest_vessel = np.asarray(f[os.path.join(group_name, 'cells/index_of_nearest_vessel')])
    index_of_nearest_vessel = index_of_nearest_vessel[:,0]  
    distance_to_nearest_vessel = np.asarray(f[os.path.join(group_name, 'cells/distance_to_nearest_vessel')])
    distance_to_nearest_vessel = distance_to_nearest_vessel[:,0]  
    print('****** important points *************')
    a=graph.edgelist[521]
    print('a: %s pos_a: %s pos_b: %s' % (a,graph['position'][a[0]],graph['position'][a[1]]))
    b=graph.edgelist[1244]
    print('b: %s pos_a: %s pos_b: %s' % (b,graph['position'][b[0]],graph['position'][b[1]]))
    
    print('cell_o2_mass shape:')
    cell_o2_mass=cell_o2_mass[:,0]
    print(cell_o2_mass.shape)
    
    print('cell_radii_shape:')
    cell_radii=cell_radii[:,0]
    print(cell_radii.shape)
    # pg/ mum^3
    cell_o2_concentration = cell_o2_mass/ (4/float(3)* np.pi*np.power(cell_radii,3))
    #cell_o2_concentration = cell_o2_mass
    volume_o2_ml = cell_o2_concentration/(1.429*1e9)
    #volume_o2_ml = cell_o2_mass/1.429
    ''' o2 density 1.429 g/L --> 1.429*10^9 pg/ml
        1cm^3 = 10^12 (mum^3)
    '''
    solubility = 3.1e-3 #ml O2/cm^3 mmHg
    #solubility = 2.8e-3 #ml O2/cm^3 mmHg
    #solubility = 1.1e-4 #ml O2/cm^3 mmHg
    solubility = solubility*1e-12 #ml O2/mum^3 mmHg
    #volume_density = 1.429e9 #pg/ml
    #x = cell_o2_concentration/volume_density # ml / mum^3
    
    #cell_po2 = x/solubility
    
    if quantity_name=='o2':
      quantity_to_average = volume_o2_ml/solubility
    if quantity_name=='pH_ex':
      quantity_to_average = cell_pH
    #quantity_to_average = cell_o2_mass/solubility
    #quantity_to_average = cell_po2
    #quantity_to_average = cell_o2_concentration
    #quantity_to_average = cell_o2_mass
    print('cell_center_pos')
    if scoop.IS_RUNNING:
      if not np.asarray(scoop.shared.getConst('cell_center_pos_')).any():
        scoop.shared.setConst(cell_center_pos_=cell_center_pos)

    
    print(goodArguments.vbl_simulation_file_name)
    print(goodArguments.grp_pattern)
    
    print("sample along line from:")
    print("%s to %s" % (starting_point, end_point))
    
    
    sample_pos, distances = get_sample_points_along_line(starting_point,end_point,metadata_dict['number_of_sampling_points'])
    box_length_of_max_norm = distances[1]*0.5
    print(distances)
    if scoop.IS_RUNNING:
      if not scoop.shared.getConst('box_length_of_max_norm'):
        scoop.shared.setConst(box_length_of_max_norm=box_length_of_max_norm)
    print('box_length_of_max_norm %f' % box_length_of_max_norm )
    #cell_center_pos = np.asarray(f[os.path.join(goodArguments.grp_pattern, 'cells/cell_center_pos')])
    #print('cell_center_pos')
    #scoop.shared.setConst(cell_center_pos_=cell_center_pos)
    lists = list(scoop.futures.map(is_index_good, sample_pos))
    for (aList, aSamplePos) in zip(lists,sample_pos):
      print('for pos: %s found %i points in eps range' % (aSamplePos,len(aList)))
      
    ''' average '''
    average_value = []
    errors = []
    
    for (aList, aSamplePos) in zip(lists,sample_pos):
      this_avg = np.average(quantity_to_average[aList])
      average_value.append(this_avg)
      #errors.append(np.sqrt(1/float(len(aList)))*this_avg)
      errors.append(np.std(quantity_to_average[aList]))
        
    print('finished sample_line_general')
  return (np.asarray(average_value), np.asarray(errors), np.asarray(distances))

def plot_averages_at_venous_orthogonal_single_time(pp , out_grp_name):
  result_string = ''
  (avg_values, errors_avg, distances) = dataman.obtain_data('po2_at_certain_time_point_vo', out_grp_name)
  #avg_values, errors_avg, distances = sample_line_artery('o2',goodArguments.grp_pattern)
  fig1, ax1 = plt.subplots(1)
  ax1.errorbar(distances,avg_values, yerr=errors_avg, linestyle='None', marker='o', color='k')
  #if infos:
  hours = (int) (out_grp_name[3:7])
  if infos:
    ax1.set(title = '%i hours after seed' % hours )
  ax1.set_xlabel(r'distance along line/ $\mu m$')
  ax1.set_ylabel(r'$pO_2 / mmHg$', color='k')
  #ax1.grid(color='k', linestyle=':', linewidth=0.5)
  
  if addpH:
    avg_values_pH, errors_avg_pH, distances = sample_line_general('pH_ex',out_grp_name, vein_ortho_p1, vein_ortho_p2)
    ax2=ax1.twinx()
    distances=distances+2.0
    ax2.errorbar(distances,avg_values_pH, yerr=errors_avg_pH,linestyle='None',marker='x',color='b' )
    ax2.set_ylabel('pH', color='b')
    ax2.yaxis.set_major_formatter(matplotlib.ticker.FormatStrFormatter('%.2f'))
  
  for entry in metadata_dict:
    result_string+= '%s:\t%s\n' % (entry, metadata_dict[entry])
  meta_data_fig.text(0.1,0.1,result_string, transform=meta_data_fig.transFigure, size=14, ha="left")
  pp.savefig(fig1)
  if infos:
    pp.savefig(meta_data_fig)

def plot_averages_at_venous_orthogonal_for_all_times(pp ):
  result_string=''
  ''' get data from cache file '''
  dict_with_a_lot_of_data=dataman.obtain_data('po2_at_all_times_vo')
  
  max_group_id = (int)(goodArguments.grp_pattern[3:7])
  min_group_id = 350
  fig1 = plt.figure()
  ax=fig1.add_subplot(111,projection='3d')
  
  group_list = np.arange(max_group_id, min_group_id, -1)
  out_group = 'out%04i' % group_list[0]
  dist=dict_with_a_lot_of_data[out_group][2]
  avg = dict_with_a_lot_of_data[out_group][0]
  print('shape dist: ')
  print(dist.shape)
  print('shape avb:')
  print(avg.shape)
  X,Y = np.meshgrid(dist,group_list)
  #deepcopy here!!!
  Z=np.ones(X.shape)
  print('shapes')
  print(X.shape)
  print(Y.shape)
  for (i,time_point) in enumerate(group_list):
    out_group = 'out%04i' % time_point
    #xs = dict_with_a_lot_of_data[out_group][2]
    avg = dict_with_a_lot_of_data[out_group][0]
    Z[i,:] = np.asarray(avg)
  surf= ax.plot_surface(X,Y,Z)
  ax.set_zlabel(r'$pO_2 / mmHg$')
  ax.set_xlabel(r'distance along line/ $\mu m$')
  ax.set_ylabel(r'hours after seed')
  
  for entry in metadata_dict:
    result_string+= '%s:\t%s\n' % (entry, metadata_dict[entry])
  meta_data_fig.text(0.1,0.1,result_string, transform=meta_data_fig.transFigure, size=14, ha="left")
  pp.savefig(fig1)
  if infos:
    pp.savefig(meta_data_fig)


def plot_averages_at_venous_bifurcation_single_time(pp , out_grp_name):
  result_string = ''
  (avg_values, errors_avg, distances) = dataman.obtain_data('po2_at_certain_time_point_v', out_grp_name)
  #avg_values, errors_avg, distances = sample_line_artery('o2',goodArguments.grp_pattern)
  fig1, ax1 = plt.subplots(1)
  ax1.errorbar(distances,avg_values, yerr=errors_avg, linestyle='None', marker='o', color='k')
  
  hours = (int) (out_grp_name[3:7])
  if infos:
    ax1.set(title = '%i hours after seed' % hours )
  ax1.set_xlabel(r'distance along line/ $\mu m$')
  ax1.set_ylabel('$pO_2 / mmHg$', color='k')
  #ax1.grid(color='k', linestyle=':', linewidth=0.5)
  
  if addpH:
    avg_values_pH, errors_avg_pH, distances = sample_line_general('pH_ex',out_grp_name,vein_parallel_p1,vein_parallel_p2 )
    ax2=ax1.twinx()
    distances=distances+2.0
    ax2.errorbar(distances,avg_values_pH, yerr=errors_avg_pH,linestyle='None',marker='x',color='b' )
    ax2.set_ylabel('pH', color='b')
    ax2.yaxis.set_major_formatter(matplotlib.ticker.FormatStrFormatter('%.2f'))
  
  for entry in metadata_dict:
    result_string+= '%s:\t%s\n' % (entry, metadata_dict[entry])
  meta_data_fig.text(0.1,0.1,result_string, transform=meta_data_fig.transFigure, size=14, ha="left")
  pp.savefig(fig1)
  if infos:
    pp.savefig(meta_data_fig)

def plot_averages_at_venous_bifurcation_for_all_times(pp ):
  result_string=''
  ''' get data from cache file '''
  dict_with_a_lot_of_data=dataman.obtain_data('po2_at_all_times_v')
  
  max_group_id = (int)(goodArguments.grp_pattern[3:7])
  min_group_id = 350
  fig1 = plt.figure()
  ax=fig1.add_subplot(111,projection='3d')
  
  group_list = np.arange(max_group_id, min_group_id, -1)
  out_group = 'out%04i' % group_list[0]
  dist=dict_with_a_lot_of_data[out_group][2]
  avg = dict_with_a_lot_of_data[out_group][0]
  print('shape dist: ')
  print(dist.shape)
  print('shape avb:')
  print(avg.shape)
  X,Y = np.meshgrid(dist,group_list)
  #deepcopy here!!!
  Z=np.ones(X.shape)
  print('shapes')
  print(X.shape)
  print(Y.shape)
  for (i,time_point) in enumerate(group_list):
    out_group = 'out%04i' % time_point
    #xs = dict_with_a_lot_of_data[out_group][2]
    avg = dict_with_a_lot_of_data[out_group][0]
    Z[i,:] = np.asarray(avg)
  surf= ax.plot_surface(X,Y,Z)
  ax.set_zlabel(r'$pO_2 / mmHg$')
  ax.set_xlabel(r'distance along line/ $\mu m$')
  ax.set_ylabel(r'hours after seed')
  
  for entry in metadata_dict:
    result_string+= '%s:\t%s\n' % (entry, metadata_dict[entry])
  meta_data_fig.text(0.1,0.1,result_string, transform=meta_data_fig.transFigure, size=14, ha="left")
  pp.savefig(fig1)
  if infos:
    pp.savefig(meta_data_fig)


def plot_averages_at_arterial_bifurcation_single_time(pp , out_grp_name):
  result_string = ''
  (avg_values, errors_avg, distances) = dataman.obtain_data('po2_at_certain_time_point_a', out_grp_name)
  #avg_values, errors_avg, distances = sample_line_artery('o2',goodArguments.grp_pattern)
  fig1, ax1 = plt.subplots(1)
  ax1.errorbar(distances,avg_values, yerr=errors_avg, linestyle='None', marker='o', color='k')
  
  hours = (int) (out_grp_name[3:7])
  if infos:
    ax1.set(title = '%i hours after seed' % hours )
  ax1.set_xlabel(r'distance along line/ $\mu m$')
  ax1.set_ylabel('pO2/mmHg', color='k')
  #ax1.grid(color='k', linestyle=':', linewidth=0.5)
  
  if addpH:
    avg_values_pH, errors_avg_pH, distances = sample_line_general('pH_ex',out_grp_name, artery_p1, artery_p2)
    ax2=ax1.twinx()
    distances=distances+2.0
    ax2.errorbar(distances,avg_values_pH, yerr=errors_avg_pH,linestyle='None',marker='x',color='b' )
    ax2.set_ylabel('pH', color='b')
    ax2.yaxis.set_major_formatter(matplotlib.ticker.FormatStrFormatter('%.2f'))
  
  for entry in metadata_dict:
    result_string+= '%s:\t%s\n' % (entry, metadata_dict[entry])
  meta_data_fig.text(0.1,0.1,result_string, transform=meta_data_fig.transFigure, size=14, ha="left")
  pp.savefig(fig1)
  if infos:
    pp.savefig(meta_data_fig)
    
    
def plot_averages_at_arterial_bifurcation_for_all_times(pp ):
  result_string=''
  ''' get data from cache file '''
  dict_with_a_lot_of_data=dataman.obtain_data('po2_at_all_times_a')
  
  max_group_id = (int)(goodArguments.grp_pattern[3:7])
  min_group_id = 350
  fig1 = plt.figure()
  ax=fig1.add_subplot(111,projection='3d')
  
  group_list = np.arange(max_group_id, min_group_id, -1)
  out_group = 'out%04i' % group_list[0]
  dist=dict_with_a_lot_of_data[out_group][2]
  avg = dict_with_a_lot_of_data[out_group][0]
  print('shape dist: ')
  print(dist.shape)
  print('shape avb:')
  print(avg.shape)
  X,Y = np.meshgrid(dist,group_list)
  #deepcopy here!!!
  Z=np.ones(X.shape)
  print('shapes')
  print(X.shape)
  print(Y.shape)
  for (i,time_point) in enumerate(group_list):
    out_group = 'out%04i' % time_point
    #xs = dict_with_a_lot_of_data[out_group][2]
    avg = dict_with_a_lot_of_data[out_group][0]
    Z[i,:] = np.asarray(avg)
  surf= ax.plot_surface(X,Y,Z)
  ax.set_zlabel(r'$pO_2 / mmHg$')
  ax.set_xlabel(r'distance along line/ $\mu m$')
  ax.set_ylabel(r'hours after seed')
  
  for entry in metadata_dict:
    result_string+= '%s:\t%s\n' % (entry, metadata_dict[entry])
  meta_data_fig.text(0.1,0.1,result_string, transform=meta_data_fig.transFigure, size=14, ha="left")
  pp.savefig(fig1)
  if infos:
    pp.savefig(meta_data_fig)
    
    
class DataArterialBifurcation(object):
  keywords = ['po2_at_all_times_a','po2_at_certain_time_point_a']
  
  def obtain_data(self, dataman, dataname, *args):
    max_group_id = (int)(goodArguments.grp_pattern[3:7])
    min_group_id = 350
    if dataname == 'po2_at_certain_time_point_a':
      print(args)
      this_out_grp_name =args[0]
      def read(hdf_cache_grp, data_name):
        print('data_name: %s' %data_name)
        print('hdf_cache_grp in read')
        print(list(hdf_cache_grp.keys()))
        return (np.asarray(hdf_cache_grp[data_name + '/' + 'average_po2']),np.asarray(hdf_cache_grp[data_name + '/' + 'average_po2_error']),np.asarray(hdf_cache_grp[data_name + '/' + 'distances']))
      def write(hdf_cache_grp, data_name):
        (average_value, errors, distances) = sample_line_general('o2', this_out_grp_name, artery_p1, artery_p2)
        group_of_single_timepoint = hdf_cache_grp.create_group(this_out_grp_name)
        print('hdf_cache_grp')
        print(hdf_cache_grp)
        print(data_name)
        print('before create')
        group_of_single_timepoint.create_dataset('average_po2', data=average_value)
        group_of_single_timepoint.create_dataset('average_po2_error', data=errors)
        group_of_single_timepoint.create_dataset('distances', data=distances)
        
      return myutils.hdf_data_caching(read, write, f_cache['/po2_at_all_times_a/'], this_out_grp_name)
    if dataname == 'po2_at_all_times_a':
      def read(hdf_cache_grp_name, data_name):
        return_dict=dict()
        hdf_data_grp=hdf_cache_grp_name[data_name]
        for out_group_id in np.arange(min_group_id,max_group_id+1):
          out_group = 'out%04i' % out_group_id
          print('reading group: %s' %out_group)
          (average_value, errors, distances) = dataman.obtain_data('po2_at_certain_time_point_a', out_group)
          return_dict[out_group] = (average_value, errors, distances)
        return return_dict
      def write(hdf_cache_grp_name, data_name):
        hdf_data_grp = hdf_cache_grp_name.create_group(data_name)
        ''' here comes the calculation '''
        for out_group_id in np.arange(min_group_id,max_group_id+1):
          out_group_name = 'out%04i' % out_group_id
          print('calculating group: %s' %out_group_name)
          dataman.obtain_data('po2_at_certain_time_point_a', out_group_name)
          
      return myutils.hdf_data_caching(read, write, f_cache, 'po2_at_all_times_a')

class DataVenousBifurcation(object):
  keywords = ['po2_at_all_times_v','po2_at_certain_time_point_v','po2_at_all_times_vo','po2_at_certain_time_point_vo']
  
  def obtain_data(self, dataman, dataname, *args):
    max_group_id = (int)(goodArguments.grp_pattern[3:7])
    min_group_id = 350
    if dataname == 'po2_at_certain_time_point_v':
      print(args)
      this_out_grp_name =args[0]
      def read(hdf_cache_grp, data_name):
        print('data_name: %s' %data_name)
        print('hdf_cache_grp in read')
        print(list(hdf_cache_grp.keys()))
        return (np.asarray(hdf_cache_grp[data_name + '/' + 'average_po2']),np.asarray(hdf_cache_grp[data_name + '/' + 'average_po2_error']),np.asarray(hdf_cache_grp[data_name + '/' + 'distances']))
      def write(hdf_cache_grp, data_name):
        (average_value, errors, distances) = sample_line_general('o2', this_out_grp_name, vein_parallel_p1, vein_parallel_p2)
        group_of_single_timepoint = hdf_cache_grp.create_group(this_out_grp_name)
        print('hdf_cache_grp')
        print(hdf_cache_grp)
        print(data_name)
        print('before create')
        group_of_single_timepoint.create_dataset('average_po2', data=average_value)
        group_of_single_timepoint.create_dataset('average_po2_error', data=errors)
        group_of_single_timepoint.create_dataset('distances', data=distances)
        
      return myutils.hdf_data_caching(read, write, f_cache['/po2_at_all_times_v/'], this_out_grp_name)
    if dataname == 'po2_at_all_times_v':
      def read(hdf_cache_grp_name, data_name):
        return_dict=dict()
        hdf_data_grp=hdf_cache_grp_name[data_name]
        for out_group_id in np.arange(min_group_id,max_group_id+1):
          out_group = 'out%04i' % out_group_id
          print('reading group: %s' %out_group)
          (average_value, errors, distances) = dataman.obtain_data('po2_at_certain_time_point_v', out_group)
          return_dict[out_group] = (average_value, errors, distances)
        return return_dict
      def write(hdf_cache_grp_name, data_name):
        hdf_data_grp = hdf_cache_grp_name.create_group(data_name)
        ''' here comes the calculation '''
        for out_group_id in np.arange(min_group_id,max_group_id+1):
          out_group_name = 'out%04i' % out_group_id
          print('calculating group: %s' %out_group_name)
          dataman.obtain_data('po2_at_certain_time_point_v', out_group_name)
          
      return myutils.hdf_data_caching(read, write, f_cache, 'po2_at_all_times_v')
    if dataname == 'po2_at_certain_time_point_vo':
      print(args)
      this_out_grp_name =args[0]
      def read(hdf_cache_grp, data_name):
        print('data_name: %s' %data_name)
        print('hdf_cache_grp in read')
        print(list(hdf_cache_grp.keys()))
        return (np.asarray(hdf_cache_grp[data_name + '/' + 'average_po2']),np.asarray(hdf_cache_grp[data_name + '/' + 'average_po2_error']),np.asarray(hdf_cache_grp[data_name + '/' + 'distances']))
      def write(hdf_cache_grp, data_name):
        (average_value, errors, distances) = sample_line_general('o2', this_out_grp_name, vein_ortho_p1, vein_ortho_p2)
        group_of_single_timepoint = hdf_cache_grp.create_group(this_out_grp_name)
        print('hdf_cache_grp')
        print(hdf_cache_grp)
        print(data_name)
        print('before create')
        group_of_single_timepoint.create_dataset('average_po2', data=average_value)
        group_of_single_timepoint.create_dataset('average_po2_error', data=errors)
        group_of_single_timepoint.create_dataset('distances', data=distances)
        
      return myutils.hdf_data_caching(read, write, f_cache['/po2_at_all_times_vo/'], this_out_grp_name)
    if dataname == 'po2_at_all_times_vo':
      def read(hdf_cache_grp_name, data_name):
        return_dict=dict()
        hdf_data_grp=hdf_cache_grp_name[data_name]
        for out_group_id in np.arange(min_group_id,max_group_id+1):
          out_group = 'out%04i' % out_group_id
          print('reading group: %s' %out_group)
          (average_value, errors, distances) = dataman.obtain_data('po2_at_certain_time_point_vo', out_group)
          return_dict[out_group] = (average_value, errors, distances)
        return return_dict
      def write(hdf_cache_grp_name, data_name):
        hdf_data_grp = hdf_cache_grp_name.create_group(data_name)
        ''' here comes the calculation '''
        for out_group_id in np.arange(min_group_id,max_group_id+1):
          out_group_name = 'out%04i' % out_group_id
          print('calculating group: %s' %out_group_name)
          dataman.obtain_data('po2_at_certain_time_point_vo', out_group_name)
          
      return myutils.hdf_data_caching(read, write, f_cache, 'po2_at_all_times_vo')

if __name__ == '__main__':
  if scoop.IS_RUNNING:
    print("scoop is running")
    
  import argparse
  parser = argparse.ArgumentParser(description='plot cell o2 along a line')  
  parser.add_argument('vbl_simulation_file_name')
  parser.add_argument('grp_pattern')
  parser.add_argument('type', help="seed of initial spheroid: v: vein or a: artery")
  parser.add_argument("-d","--data", dest="datalist", help="which data (pressure, flow, shearforce, hematocrit) as comma separated list", default='pressure', action="store")
  parser.add_argument("-f","--filter-uncirculated", dest="filteruncirculated", help="filter uncirculated vessels", default=False, action="store_true")
  parser.add_argument("--filter-radius-high-pass", dest="filterradiushighpass", type=float, default=-1.0)
  parser.add_argument("--no-overlay", dest="overlay", default = True, action="store_false")
  parser.add_argument("--dpi", dest="dpi", default=None, action="store")
  parser.add_argument("--format", dest="format", default=None, action="store")
  parser.add_argument("-n", dest="out_nl", default = False, action="store") 
  parser.add_argument("--outFilename", dest="outfn", default= None, type=str)
  '''this option come from the tumor side'''
  parser.add_argument("--writeVessels", help="when doing the tumor, export vesesls", default=True, action="store_true")  
  parser.add_argument("--writeFields", help="when doing the tumor, export Fields", default=None)  
  goodArguments, otherArguments = parser.parse_known_args()
  
  '''check input'''
  try:
    dirs = set()
    if not os.path.isfile(goodArguments.vbl_simulation_file_name):
      raise AssertionError('The file %s is not present!'%goodArguments.vbl_simulation_file_name)
    with h5py.File(goodArguments.vbl_simulation_file_name, 'r') as f:
      d = myutils.walkh5(f, goodArguments.grp_pattern)
      if not len(d)>0:
        raise AssertionError('pattern "%s" not found in "%s"!' % (goodArguments.grp_pattern, goodArguments.vbl_simulation_file_name))
      else:
        dirs = set.union(dirs,d)
  except Exception as e:
    print(e.message)
    sys.exit(-1)
    
  
  ''' begin of code '''
  '''register a clases at data manager'''
  f_cache = h5py.File('cache_'+ goodArguments.vbl_simulation_file_name, 'a')
  dataman = myutils.DataManager(20, [ DataArterialBifurcation(), DataVenousBifurcation()])
  
  ''' pdf output '''
  meta_data_fig = plt.figure(figsize=(11.69,8.27))
  meta_data_fig.clf()
  result_string = ''

  infos = False  
  addpH = True
  if goodArguments.type == 'a':
    with PdfPages('3d_arterial_%s_%s.pdf' %(goodArguments.vbl_simulation_file_name,goodArguments.grp_pattern))  as pp:
      '''creates data for all time points'''
      plot_averages_at_arterial_bifurcation_for_all_times(pp)
    with PdfPages('out0350_arterial_%s_%s.pdf' %(goodArguments.vbl_simulation_file_name,goodArguments.grp_pattern))  as pp:
      plot_averages_at_arterial_bifurcation_single_time(pp, 'out0350')
    with PdfPages('%s_arterial_%s.pdf' %(goodArguments.grp_pattern, goodArguments.vbl_simulation_file_name))  as pp:
      plot_averages_at_arterial_bifurcation_single_time(pp, goodArguments.grp_pattern)
#      plot_averages_along_outward_line(pp)
#      sample_in_orthogonal_plane(3553,pp)
    
  if goodArguments.type == 'v':
    with PdfPages('3d_venous_%s_%s.pdf' %(goodArguments.vbl_simulation_file_name,goodArguments.grp_pattern))  as pp:
      '''creates data for all time points'''
      plot_averages_at_venous_bifurcation_for_all_times(pp)
    with PdfPages('out0350_venous_%s_%s.pdf' %(goodArguments.vbl_simulation_file_name,goodArguments.grp_pattern))  as pp:
      plot_averages_at_venous_bifurcation_single_time(pp, 'out0350')
    with PdfPages('%s_venous_%s.pdf' %(goodArguments.grp_pattern, goodArguments.vbl_simulation_file_name))  as pp:
      plot_averages_at_venous_bifurcation_single_time(pp, goodArguments.grp_pattern)
      
    with PdfPages('3d_venous_o_%s_%s.pdf' %(goodArguments.vbl_simulation_file_name,goodArguments.grp_pattern))  as pp:
      '''creates data for all time points'''
      plot_averages_at_venous_orthogonal_for_all_times(pp)
    with PdfPages('out0350_venous_o_%s_%s.pdf' %(goodArguments.vbl_simulation_file_name,goodArguments.grp_pattern))  as pp:
      plot_averages_at_venous_orthogonal_single_time(pp, 'out0350')
    with PdfPages('%s_venous_o_%s.pdf' %(goodArguments.grp_pattern, goodArguments.vbl_simulation_file_name))  as pp:
      plot_averages_at_venous_orthogonal_single_time(pp, goodArguments.grp_pattern)
