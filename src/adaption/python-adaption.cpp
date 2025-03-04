/**
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
*/
#include "../python_krebsutils/python-helpers.h"
#include "numpy.hpp"
#include "adaption_model2.h"
#include "../common/calcflow.h"
#include <algorithm>

#define BOOST_RESULT_OF_USE_DECLTYPE 1

#include <boost/foreach.hpp>
#include <boost/iterator/transform_iterator.hpp>
#include <boost/accumulators/accumulators.hpp>
#include <boost/accumulators/statistics.hpp>

namespace py = boost::python;
namespace nm = boost::python::numeric;
namespace h5 = h5cpp;

/**
 * @brief Calculates radii due to metabolic and topological demand.
 * 
 * Paper by Secomb et al.
 */

namespace Adaption
{
bool IsTrue(bool pbool){return pbool;}
  
void InitParameters(Adaption::Parameters &params, py::dict py_parameters)
{
#define GET_ADAPTION_PARAM_FROM_DICT(TYPE, NAME) py::extract<TYPE>(py_parameters.get(NAME))
#define GET_ADAPTION_PARAM_IF_NONNONE(TARGET, TYPE, NAME) { py::object o(py_parameters.get(NAME)); if (!o.is_none()) TARGET=py::extract<TYPE>(o); }
  
#ifdef DEBUG
  printf("entered InitParameters\n");
#endif
  //this could possibly done for every parameter
  try
  {
    double k_c = GET_ADAPTION_PARAM_FROM_DICT(double,"k_c");
    if(k_c<0)
      throw std::runtime_error("got bad k_c from python2");
    params.k_c = k_c;
  }
  catch(std::runtime_error &e)
  {
    e.what();
  }
  params.k_m = GET_ADAPTION_PARAM_FROM_DICT(double,"k_m");
  params.k_s = GET_ADAPTION_PARAM_FROM_DICT(double,"k_s");
  params.Q_refdot = GET_ADAPTION_PARAM_FROM_DICT(double,"Q_refdot");
  params.S_0 = GET_ADAPTION_PARAM_FROM_DICT(double,"S_0");
  params.max_nun_iterations = GET_ADAPTION_PARAM_FROM_DICT(double,"max_nun_iterations");
  params.qdev = GET_ADAPTION_PARAM_FROM_DICT(double,"qdev");
  params.starting_radii = GET_ADAPTION_PARAM_FROM_DICT(double,"starting_radii");
  params.delta_t = GET_ADAPTION_PARAM_FROM_DICT(double,"delta_t");
  params.cond_length = GET_ADAPTION_PARAM_FROM_DICT(double,"cond_length");
  params.avgRootNodeConductivity = GET_ADAPTION_PARAM_FROM_DICT(double,"avgRootNodeConductivity");
  //std::cout<<params.write2File<<std::endl;
  GET_ADAPTION_PARAM_IF_NONNONE(params.write2File,bool,"write2File")
  //std::cout<<params.write2File<<std::endl;
  //std::cout<<params.tum_manitulate_s1<<std::endl;
  params.tum_manitulate_s1 = GET_ADAPTION_PARAM_FROM_DICT(bool,"tum_manitulate_s1");
  //std::cout<<params.tum_manitulate_s1<<std::endl;
  params.tum_manitulate_s2 = GET_ADAPTION_PARAM_FROM_DICT(bool,"tum_manitulate_s2");
  params.tum_manitulate_s3 = GET_ADAPTION_PARAM_FROM_DICT(bool,"tum_manitulate_s3");
  params.tum_manitulate_s4 = GET_ADAPTION_PARAM_FROM_DICT(bool,"tum_manitulate_s4");
  params.tum_manitulate_s5 = GET_ADAPTION_PARAM_FROM_DICT(bool,"tum_manitulate_s5");
#ifdef DEBUG
  printf("leave InitParameters\n");
#endif
}

/*
 * we will consider the circulated vessels only,
 * therefore we write them, in the h5 file before we starting
 */
static void PyPrepareForAdaptation(std::auto_ptr<VesselList3d> &vl_,h5::Group vesselgroup_, h5::Group out_, BloodFlowParameters bfparams_, Adaption::Parameters adap_params)
{
  vl_ = ReadVesselList3d(vesselgroup_, make_ptree("filter", true));
  CalcFlow(*vl_, bfparams_);
  h5::Group grp_temp;
  if( adap_params.write2File )
  {
    if(not out_.exists("recomputed"))
    {
      grp_temp = out_.create_group("recomputed");
      ptree getEverytingPossible = make_ptree("w_adaption", true);
      WriteVesselList3d(*vl_, grp_temp, getEverytingPossible);
    }
    else
    {
      // dont need this
      //grp_temp = out_.open_group("recomputed");
    }
  }
}

static py::object PyComputeAdaption(py::object py_vesselgroup, py::dict py_parameters, py::object py_bfparams, py::object py_h5outputGroup)
{
  cout<<" PyComputeAdaption is called "<<endl;
  //python specific
  h5::Group vesselgroup = PythonToCppGroup(py_vesselgroup);
  h5::Group vessels_after_adaption = PythonToCppGroup(py_h5outputGroup);
  BloodFlowParameters bfparams = py::extract<BloodFlowParameters>(py_bfparams);
  
  Adaption::Parameters params;
  InitParameters(params, py_parameters);
  
  std::auto_ptr<VesselList3d> vl;
  
  PyPrepareForAdaptation(vl, vesselgroup, vessels_after_adaption, bfparams, params);
  // so kann man es besser machen:
  std::string vesselListClass = "GRAPH";
  try{
    vesselListClass = vesselgroup.attrs().get<string>("CLASS");
  }
  catch(h5::Exception &e)  // will programm abbruch fuer alle fehler ausser wenn CLASS attribute fehlt. Pruefe ob H5 exception. Andere exceptions machen programm abbruch.
  {
    cerr << "PyComputeAdaption: fall back to default vessel list reader (lattice based) due to error: ";
    cerr << e.what();
  }
  
  if(vesselListClass == "REALWORLD")
  {
   // world = true;
  }
  else if (vesselListClass == "GRAPH")
  {
    // nothing to do
  }
  else
  { // output the name of the class, too
    cerr<<"PyComputeAdaption: Unknows CLASS: "<< vesselListClass << "; fall back to lattice based vessellist" << endl;
  }
  
  //gain some topological info for adaptive parameters
  int no_of_roots = 0;
  for(int i=0;i<vl->GetNCount();++i)
  {
    VesselNode *nd = vl->GetNode(i);
    if(nd->IsBoundary())no_of_roots++;
  }
  params.no_of_roots = no_of_roots;
  
  
  //starting with equal radii with parameters starting value is greate than 0.
  //otherwise we use the radii from the input file vary them a little bit
  if(params.starting_radii>0.)
  {
    for(int i=0;i<vl->GetECount();++i)
    {
      vl->GetEdge(i)->r = params.starting_radii;
    }
  }
  else
  {
#if 0
    std::default_random_engine generator;
    double initial_variation = 0.0;
    std::uniform_real_distribution<double> distribution(-initial_variation,initial_variation);
    for(int i=0;i<vl->GetECount();++i)
    {
      Vessel* v=vl->GetEdge(i);
#if 1//leafes boundary radius as they are
      auto it = vl->GetBCMap().find(v->NodeA());
      auto it2 = vl->GetBCMap().find(v->NodeB());
      if(it !=vl->GetBCMap().end() or it2 !=vl->GetBCMap().end())
      {
#ifdef DEBUG
	cout<<"skipping vessel #"<<v->Index()<< " since it has boundary nodes!!!"<<endl;
#endif
	continue;
      }
#endif
      v->r = v->r+v->r*distribution(generator);
    }
#endif
  }


#ifdef DEBUG
  for( auto it = vl->GetBCMap().begin(); it!= vl->GetBCMap().end(); ++it)
  {
    cout << "index: " << it->first->Index() << "bcvalue: " << it->second.val <<endl;
  }
  for(int i=0;i<vl->GetNCount();++i)
  {
    VesselNode* nd = vl->GetNode(i);
    cout << "pressure: " << nd->press <<endl;
  }
  for(int i=0;i<vl->GetECount();++i)
  {
    Vessel *v = vl->GetEdge(i);
    cout << "flow: " << v->q<<endl;
  }
#endif

  CalcFlow(*vl, bfparams);
  
#ifdef DEBUG
#ifndef SILENT
  for( auto it = vl->GetBCMap().begin(); it!= vl->GetBCMap().end(); ++it)
  {
    cout << "index: " << it->first->Index() << "bcvalue: " << it->second.val <<endl;
  }
  for(int i=0;i<vl->GetNCount();++i)
  {
    VesselNode* nd = vl->GetNode(i);
    cout << "pressure: " << nd->press <<endl;
  }
  for(int i=0;i<vl->GetECount();++i)
  {
    Vessel *v = vl->GetEdge(i);
    cout << "flow: " << v->q<<endl;
  }
#endif
#endif
  uint return_state;
  using namespace boost::accumulators;
  return_state = runAdaption_Loop(&params, &bfparams, vl.get(), &vessels_after_adaption, false);
  accumulator_set<double, features<tag::mean, tag::variance>> acc;
#pragma omp parallel for
  for(int i =0;i<vl.get()->GetECount();++i)
  {
    Vessel* v = vl.get()->GetEdge(i);
    acc(v->q);
  }
  return py::make_tuple(return_state,mean(acc),sqrt(variance(acc)));
}  

Adaption::Parameters* AllocateParametersFromDict(const py::dict &d)
{
  std::auto_ptr<Adaption::Parameters> p(new Adaption::Parameters());
  InitParameters(*p, d);
  return p.release();
}

void export_adaption_computation()
{ 
  py::def("AllocateAdaptionParametersFromDict", &AllocateParametersFromDict, py::return_value_policy<py::manage_new_object>());
  py::def("computeAdaption", PyComputeAdaption);
  py::def("testAdaption", TestAdaption);
}
  
}//namespace
#ifdef DEBUG
BOOST_PYTHON_MODULE(libadaption_d)
#else
BOOST_PYTHON_MODULE(libadaption_)
#endif
{
  Adaption::export_adaption_computation();
}