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
import math
import copy

default = dict(
  tip_radius_arterial = 2.5,
  tip_radius_capi = 2.5,
  tip_radius_vein = 3.8,
  murray_alpha_vein = 3.,
  murray_alpha_artery = 3.,
  scale = 130.,
  max_sprout_radius_artery = 8.,
  max_sprout_radius_vein = 8.,
  calcflow = dict(
    viscosityPlasma = 1.2e-6,
    rheology = 'RheologySecomb2005',
    inletHematocrit = 0.37,
    includePhaseSeparationEffect = 1,
  )
)
no_phase = copy.deepcopy(default)
no_phase['calcflow'].update(
    includePhaseSeparationEffect = 0,
    )
large_2d = dict(
  tip_radius_arterial = 2.5,
  tip_radius_capi = 2.5,
  tip_radius_vein = 3.8,
  murray_alpha_vein = 3.,
  murray_alpha_artery = 3.,
  scale = 600.,
  max_sprout_radius_artery = 8.,
  max_sprout_radius_vein = 8.,
  calcflow = dict(
    viscosityPlasma = 1.2e-6,
    rheology = 'RheologySecomb2005',
    inletHematocrit = 0.37,
    includePhaseSeparationEffect = 0,
  )
)
irino_vess = dict(
  scale = 110., #as suggested by the runs of big_calibration_vol2 on snowden
  tip_radius_arterial = 2.5,
  tip_radius_capi = 2.5,
  tip_radius_vein = 3.8,
  # estimating from relative volume of blood in veins 65%, 
  # one obtains a radius scale factor of r(vein) = 1.36 * r(arterial)
  murray_alpha_vein = 3.,
  murray_alpha_artery = 3.,
  max_sprout_radius_artery = 8.,
  max_sprout_radius_vein = 8.,
  calcflow = dict(
    viscosityPlasma = 1.2e-6,
    rheology = 'RheologySecomb2005', # WARNING: changed to new model of secomb
    inletHematocrit = 0.45,
    includePhaseSeparationEffect = 0,
  ),
)

f_ = math.sqrt(0.015/0.0139)
paramset3 = dict(
  tip_radius_arterial = 3.5*f_,
  tip_radius_capi = 3.5*f_,
  tip_radius_vein = 5.*f_,
  murray_alpha_artery = 2.8,
  murray_alpha_vein = 2.8,
  scale = 160.,
)

f_ = 3./6.
paramset4 = dict(
  tip_radius_arterial = 6.5*f_,
  tip_radius_capi = 6.*f_,
  tip_radius_vein = 12.*f_,
  murray_alpha_artery = 3.,
  murray_alpha_vein = 3.,
  scale = 145.,
  max_sprout_radius_artery = 8.,
  max_sprout_radius_vein = 8.,
  generate_more_capillaries = True,
)


paramset5 = dict(
  tip_radius_arterial = 3.,
  tip_radius_capi = 2.9,
  tip_radius_vein = 6.,
  murray_alpha = 3.,
  scale = 130.,
  max_sprout_radius_artery = 8.,
  max_sprout_radius_vein = 8.,
  generate_more_capillaries = True,
)

paramset6 = dict(
  capillariesUntilLevel = 5,
  tip_radius_capi = 3,
  tip_radius_arterial = 3.,
  tip_radius_vein = 3.,
  murray_alpha_vein = 2.3,
  max_sprout_radius_vein = 4.,
  max_sprout_radius_artery = 4.,
  generate_more_capillaries = False,
  full_debug_output = False,
  scale=135.,
)


paramset7 = dict(
  tip_radius_arterial = 3.0,
  tip_radius_capi = 3.0,
  tip_radius_vein = 4.5,
  murray_alpha_vein = 3.,
  murray_alpha_artery = 3.,
  scale = 130.,
  max_sprout_radius_artery = 8.,
  max_sprout_radius_vein = 8.,
)

paramset8 = dict(
  tip_radius_arterial = 3.0,
  tip_radius_capi = 3.0, #2.6
  tip_radius_vein = 4.5, #4
  murray_alpha_vein = 3.,
  murray_alpha_artery = 3.,
  scale = 130.,
  max_sprout_radius_artery = 8.,
  max_sprout_radius_vein = 8.,
  calcflow = dict(
    viscosityPlasma = 1.2e-6,
    rheology = 'RheologyForHuman',
    inletHematocrit = 0.37,
    includePhaseSeparationEffect = 0,
  )
)

paramset10 = dict(
  tip_radius_arterial = 2.5,
  tip_radius_capi = 2.5,
  tip_radius_vein = 3.8,
  murray_alpha_vein = 3.,
  murray_alpha_artery = 3.,
  scale = 130.,
  max_sprout_radius_artery = 8.,
  max_sprout_radius_vein = 8.,
  calcflow = dict(
    viscosityPlasma = 1.2e-6,
    rheology = 'RheologyForHuman',
    inletHematocrit = 0.37,
    includePhaseSeparationEffect = 0,
  )
)

paramset11 = dict(
  seed = 1298762,
  tip_radius_arterial = 2.5,
  tip_radius_capi = 2.5,
  tip_radius_vein = 3.8,
  murray_alpha_vein = 2.9,
  murray_alpha_artery = 2.9,
  scale = 90.,
  max_sprout_radius_artery = 20.,
  max_sprout_radius_vein = 20.,
  o2range = 200.,
  calcflow = dict(
    viscosityPlasma = 1.2e-6,
    rheology = 'RheologyForHuman',
    inletHematocrit = 0.45,
    includePhaseSeparationEffect = 0,
  )
)
paramset12 = dict(
  seed = 1298762,
  tip_radius_arterial = 2.5,
  tip_radius_capi = 2.5,
  tip_radius_vein = 3.8,
  murray_alpha_vein = 2.9,
  murray_alpha_artery = 2.9,
  scale = 300.,
  max_sprout_radius_artery = 20.,
  max_sprout_radius_vein = 20.,
  o2range = 200.,
  generate_more_capillaries = False,
  calcflow = dict(
    viscosityPlasma = 1.2e-6,
    rheology = 'RheologyForHuman',
    inletHematocrit = 0.45,
    includePhaseSeparationEffect = 0,
  )
)
paramset13 = dict(
  seed = 1298762,
  tip_radius_arterial = 3.5,
  tip_radius_capi = 3.,
  tip_radius_vein = 4.5,
  murray_alpha_vein = 2.,
  murray_alpha_artery = 2.,
  scale = 300.,
  max_sprout_radius_artery = 20.,
  max_sprout_radius_vein = 20.,
  o2range = 200.,
  generate_more_capillaries = False,
  calcflow = dict(
    viscosityPlasma = 1.2e-6,
    rheology = 'RheologyForHuman',
    inletHematocrit = 0.45,
    includePhaseSeparationEffect = 0,
  )
)
paramset13 = dict(
  seed = 1298762,
  tip_radius_arterial = 3.5,
  tip_radius_capi = 3.,
  tip_radius_vein = 4.5,
  murray_alpha_vein = 2.,
  murray_alpha_artery = 2.,
  scale = 300.,
  max_sprout_radius_artery = 20.,
  max_sprout_radius_vein = 20.,
  o2range = 200.,
  generate_more_capillaries = False,
  calcflow = dict(
    viscosityPlasma = 1.2e-6,
    rheology = 'RheologyForHuman',
    inletHematocrit = 0.45,
    includePhaseSeparationEffect = 0,
  )
)
paramset14 = dict(
  seed = 1298762,
  tip_radius_arterial = 3.5,
  tip_radius_capi = 3.,
  tip_radius_vein = 4.5,
  murray_alpha_vein = 2.,
  murray_alpha_artery = 2.,
  scale = 300.,
  max_sprout_radius_artery = 100.,
  max_sprout_radius_vein = 100.,
  o2range = 200.,
  generate_more_capillaries = False,
  calcflow = dict(
    viscosityPlasma = 1.2e-6,
    rheology = 'RheologyForHuman',
    inletHematocrit = 0.45,
    includePhaseSeparationEffect = 0,
  )
)
paramset15 = dict(
  seed = 1298762,
  tip_radius_arterial = 3.5,
  tip_radius_capi = 3.,
  tip_radius_vein = 4.5,
  murray_alpha_vein = 2.,
  murray_alpha_artery = 2.,
  scale = 300.,
  max_sprout_radius_artery = 2.,
  max_sprout_radius_vein = 2.,
  o2range = 200.,
  generate_more_capillaries = False,
  calcflow = dict(
    viscosityPlasma = 1.2e-6,
    rheology = 'RheologyForHuman',
    inletHematocrit = 0.45,
    includePhaseSeparationEffect = 0,
  )
)
paramset16 = dict(
  seed = 1298762,
  tip_radius_arterial = 3.5,
  tip_radius_capi = 3.,
  tip_radius_vein = 4.5,
  murray_alpha_vein = 2.,
  murray_alpha_artery = 2.,
  scale = 75.,
  max_sprout_radius_artery = 100.,
  max_sprout_radius_vein = 100.,
  o2range = 200.,
  generate_more_capillaries = False,
  calcflow = dict(
    viscosityPlasma = 1.2e-6,
    rheology = 'RheologyForHuman',
    inletHematocrit = 0.45,
    includePhaseSeparationEffect = 0,
  )
)
paramset17 = dict(
  seed = 1298762,
  tip_radius_arterial = 3.5,
  tip_radius_capi = 3.,
  tip_radius_vein = 4.5,
  murray_alpha_vein = 2.,
  murray_alpha_artery = 2.,
  scale = 75.,
  max_sprout_radius_artery = 100.,
  max_sprout_radius_vein = 100.,
  o2range = 200.,
  generate_more_capillaries = True,
  calcflow = dict(
    viscosityPlasma = 1.2e-6,
    rheology = 'RheologyForHuman',
    inletHematocrit = 0.45,
    includePhaseSeparationEffect = 0,
  )
)
paramset18 = dict(
  seed = 1298762,
  tip_radius_arterial = 3.0,
  tip_radius_capi = 2.5,
  tip_radius_vein = 3.0,
  murray_alpha_vein = 3.,
  murray_alpha_artery = 3.,
  scale = 75.,
  max_sprout_radius_artery = 100.,
  max_sprout_radius_vein = 100.,
  o2range = 200.,
  generate_more_capillaries = True,
  calcflow = dict(
    viscosityPlasma = 1.2e-6,
    rheology = 'RheologyForHuman',
    inletHematocrit = 0.45,
    includePhaseSeparationEffect = 0,
  )
)
paramset19 = dict(
  seed = 1298762,
  tip_radius_arterial = 4.0,
  tip_radius_capi = 4.0,
  tip_radius_vein = 4.0,
  murray_alpha_vein = 3.,
  murray_alpha_artery = 3.,
  scale = 75.,
  max_sprout_radius_artery = 100.,
  max_sprout_radius_vein = 100.,
  o2range = 200.,
  generate_more_capillaries = True,
  calcflow = dict(
    viscosityPlasma = 1.2e-6,
    rheology = 'RheologyForHuman',
    inletHematocrit = 0.45,
    includePhaseSeparationEffect = 0,
  )
)
paramset20 = dict(
  seed = 1298762,
  tip_radius_arterial = 2.0,
  tip_radius_capi = 2.0,
  tip_radius_vein = 2.0,
  murray_alpha_vein = 3.,
  murray_alpha_artery = 3.,
  scale = 75.,
  max_sprout_radius_artery = 100.,
  max_sprout_radius_vein = 100.,
  o2range = 200.,
  generate_more_capillaries = True,
  calcflow = dict(
    viscosityPlasma = 1.2e-6,
    rheology = 'RheologyForHuman',
    inletHematocrit = 0.45,
    includePhaseSeparationEffect = 0,
  )
)
paramset21 = dict(
  seed = 1298762,
  tip_radius_arterial = 2.5, #initial value to start recursive calculation of radii according to murrays law
  tip_radius_capi = 2.5,
  tip_radius_vein = 2.0,
  murray_alpha_vein = 2.5,
  murray_alpha_artery = 2.7,
  scale = 75.,
  max_sprout_radius_artery = 100., #can only sprout if artery from which we sprout is less than this threshold, according to MW too small is not good
  max_sprout_radius_vein = 100.,
  o2range = 200.,
  generate_more_capillaries = False,
  calcflow = dict(
    viscosityPlasma = 1.2e-6,
    rheology = 'RheologyForHuman',
    inletHematocrit = 0.45,
    includePhaseSeparationEffect = 0,
  )
)
paramset22 = dict(
  seed = 1298762,
  tip_radius_arterial = 2.0, #initial value to start recursive calculation of radii according to murrays law
  tip_radius_capi = 2.0,
  tip_radius_vein = 2.5,
  murray_alpha_vein = 3.,
  murray_alpha_artery = 3.,
  scale = 75.,
  max_sprout_radius_artery = 100., #can only sprout if artery from which we sprout is less than this threshold, according to MW too small is not good
  max_sprout_radius_vein = 100.,
  o2range = 200.,
  generate_more_capillaries = False,
  calcflow = dict(
    viscosityPlasma = 1.2e-6,
    rheology = 'RheologyForHuman',
    inletHematocrit = 0.45,
    includePhaseSeparationEffect = 0,
  )
)
paramset23 = dict(
  seed = 1298762,
  tip_radius_arterial = 2.0, #initial value to start recursive calculation of radii according to murrays law
  tip_radius_capi = 2.0,
  tip_radius_vein = 2.5,
  murray_alpha_vein = 2.,
  murray_alpha_artery = 2.,
  scale = 75.,
  max_sprout_radius_artery = 100., #can only sprout if artery from which we sprout is less than this threshold, according to MW too small is not good
  max_sprout_radius_vein = 100.,
  o2range = 200.,
  generate_more_capillaries = False,
  calcflow = dict(
    viscosityPlasma = 1.2e-6,
    rheology = 'RheologyForHuman',
    inletHematocrit = 0.45,
    includePhaseSeparationEffect = 0,
  )
)
paramset24 = dict(
  seed = 1298762,
  tip_radius_arterial = 2.0, #initial value to start recursive calculation of radii according to murrays law
  tip_radius_capi = 2.0,
  tip_radius_vein = 2.5,
  murray_alpha_vein = 2.742,
  murray_alpha_artery = 3.,
  scale = 75.,
  max_sprout_radius_artery = 100., #can only sprout if artery from which we sprout is less than this threshold, according to MW too small is not good
  max_sprout_radius_vein = 100.,
  o2range = 200.,
  generate_more_capillaries = False,
  calcflow = dict(
    viscosityPlasma = 1.2e-6,
    rheology = 'RheologyForHuman',
    inletHematocrit = 0.45,
    includePhaseSeparationEffect = 0,
  )
)
video_create = dict(
  seed = 1298762,
  tip_radius_arterial = 2.0, #initial value to start recursive calculation of radii according to murrays law
  tip_radius_capi = 2.0,
  tip_radius_vein = 2.5,
  murray_alpha_vein = 2.742,
  murray_alpha_artery = 3.,
  scale = 75.,
  max_sprout_radius_artery = 100., #can only sprout if artery from which we sprout is less than this threshold, according to MW too small is not good
  max_sprout_radius_vein = 100.,
  o2range = 200.,
  generate_more_capillaries = False,
  full_debug_output = True,
  calcflow = dict(
    viscosityPlasma = 1.2e-6,
    rheology = 'RheologySecomb2005',
    inletHematocrit = 0.45,
    includePhaseSeparationEffect = 1,
  )
)
'''
these parameters are inspired by the studies
of luedemann et. al
and gain by the calibration runs on snowden
vessel_trees_better/swine/rough_calibration2
'''
swine = dict(
  seed = 1298762,
  tip_radius_arterial = 2.0, #initial value to start recursive calculation of radii according to murrays law
  tip_radius_capi = 2.0,
  tip_radius_vein = 2.5,
  murray_alpha_vein = 2.742,
  murray_alpha_artery = 3.,
  scale = 50.,
  max_sprout_radius_artery = 100., #can only sprout if artery from which we sprout is less than this threshold, according to MW too small is not good
  max_sprout_radius_vein = 100.,
  o2range = 200.,
  generate_more_capillaries = False,
  full_debug_output = False,
  calcflow = dict(
    viscosityPlasma = 1.2e-6,
    rheology = 'RheologySecomb2005',
    inletHematocrit = 0.45,
    includePhaseSeparationEffect = 1,
  )
)

'''
these parameters were used to create the vessel trees
used in the publication:
  http://journals.plos.org/plosone/article?id=10.1371/journal.pone.0161267
'''
plos_one_oxygen = dict(
  tip_radius_arterial = 2.5,
  tip_radius_capi = 2.5,
  tip_radius_vein = 3.8,
  murray_alpha_vein = 3.,
  murray_alpha_artery = 3.,
  scale = 130.,
  max_sprout_radius_artery = 8.,
  max_sprout_radius_vein = 8.,
  calcflow = dict(
    viscosityPlasma = 1.2e-6,
    rheology = 'RheologyForHuman',
    inletHematocrit = 0.37,
    includePhaseSeparationEffect = 0,
  ),
  capillariesUntilLevel = 0,
  full_debug_output = 0,
  generate_more_capillaries=0,
  
)
asymmetric = dict(
  tip_radius_arterial = 7.5,
  tip_radius_capi = 5.5,
  tip_radius_vein = 10.8,
  murray_alpha_vein = 3.,
  murray_alpha_artery = 3.,
  scale = 130.,
  max_sprout_radius_artery = 8.,
  max_sprout_radius_vein = 8.,
  calcflow = dict(
    viscosityPlasma = 1.2e-6,
    rheology = 'RheologyForRats',
    inletHematocrit = 0.37,
    includePhaseSeparationEffect = 1,
  ),
  generate_more_capillaries = True,
  changeRateThreshold = 0.1,
)
