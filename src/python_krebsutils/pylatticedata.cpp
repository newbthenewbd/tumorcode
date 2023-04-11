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

#include "pylatticedata.h"
#include "lattice-data-polymorphic.h"

class PyLd : public PyObject
{
  typedef polymorphic_latticedata::LatticeData LatticeData;
  std::unique_ptr<LatticeData> ld;
  PyLd() {}
public:
  const LatticeData& get() const { return *ld; }
  
  PyLd(const std::string &type, const py::object &bbox, float scale)
  {
    ld = polymorphic_latticedata::Make_ld(type.c_str(), BBoxFromPy<int,3>(bbox), scale);
  }
  
  PyLd(const std::string &type, const BBox3 &bbox, float scale)
  {
    ld = polymorphic_latticedata::Make_ld(type.c_str(), bbox, scale);
  }

  PyLd(const PyLd &other)
  {
    ld = other.ld->Clone();
  }

  //virtual ~PyLd() {}
//   ~PyLd() 
//   {
//     auto manual_ptr = ld.release();
//     delete manual_ptr;
//   }

  // takes ownership of the pointer
//   PyLd(std::auto_ptr<LatticeData> ld_)
//   {
//     ld = ld_.get();
//     ld_.release();
//   }
  
  float Scale() const { return ld->Scale(); }

  void SetScale(float s) { ld->SetScale(s); }

  void SetCellCentering(const Vec<bool, 3> &cc) {
    ld->SetCellCentering(cc);
  }
  
  py::object Box() const {
    return BBoxToPy<int,3>(ld->Box());
  }

  void SetOriginPosition(const Float3 &pos) {
    ld->SetOriginPosition(pos);
  }
  
  py::tuple GetOriginPosition() 
  {
    auto anyInstanceOfVector = ld->GetOriginPosition();
    return py::make_tuple(anyInstanceOfVector[0],anyInstanceOfVector[1],anyInstanceOfVector[2]);
  }
  
  py::object GetWorldBox() const {
    return BBoxToPy<float,3>(ld->GetWorldBox());
  }

  int NbCount() const { return ld->NbCount(); }

  Int3 NbLattice(const Int3 &p, int dir) const {
    return (ld->NbLattice(p, dir));
  }

  Float3 LatticeToWorld(const Int3 &p) const {
    return (ld->LatticeToWorld(p));
  }

  bool IsInsideLattice(const Int3 &p) const {
    return ld->IsInsideLattice((p));
  }
  
  int LatticeToSite(const Int3 &p) const{
    return (ld->LatticeToSite(p));
  }

  Int3 WorldToLattice(const Float3 &p) const {
    return ld->WorldToLattice(p);
  }
  
  py::tuple GetAxisDirLen(const Int3 &p1, const Int3 &p2 ) const
  {
    AxisDirLen q = ld->GetAxisDirLen(p1, p2);
    if (q.isValid())
      return py::make_tuple(q.dir, q.len);
    else
      return py::make_tuple(py::object(), py::object());
  }

  Int3 SiteToLattice(int64 site) const
  {
    return ld->SiteToLattice(site);
  }
  
  std::string toString() const {
    std::ostringstream os;
    get().print(os);
    return os.str();
  }
};

namespace mw_py_impl
{


template<class LatticeDataType>
struct LdToPy
{
  static PyObject* convert(const LatticeDataType& ld)
  {
//     PyLd pyld(new polymorphic_latticedata::Derived<LatticeDataType>(ld));
//     py::object r(pyld);
//     return py::incref(r.ptr());
  }
  
  static void Register()
  {
    py::to_python_converter<LatticeDataType, LdToPy<LatticeDataType> >();
  }
};



template<class LatticeDataType>
struct LdFromPy
{
    typedef LatticeDataType TheCppType;
    static void Register()
    {
      boost::python::converter::registry::push_back(
        &convertible,
        &construct,
        boost::python::type_id<TheCppType>());
    }
    
    static void* convertible(PyObject* obj_ptr)
    {
      py::object o(py::handle<>(py::borrowed(obj_ptr)));
      py::extract<PyLd> ex(o);
      if (!ex.check()) return 0;
      PyLd pld = ex;
      if (NULL==dynamic_cast<const polymorphic_latticedata::Derived<LatticeDataType>*>(&pld.get())) return 0;
      return obj_ptr;
    }
    
    static void construct(PyObject* obj_ptr, boost::python::converter::rvalue_from_python_stage1_data* data)
    {
      py::object o(py::handle<>(py::borrowed(obj_ptr)));
      PyLd pld = py::extract<PyLd>(o);

      void* storage = ((boost::python::converter::rvalue_from_python_storage<TheCppType>*)data)->storage.bytes;
      new (storage) TheCppType(dynamic_cast<const polymorphic_latticedata::Derived<LatticeDataType>*>(&pld.get())->get());
      data->convertible = storage;
    }
};
}

PyLd* read_lattice_data_from_hdf_by_filename(const string fn, const string path)
{
  //h5cpp::Group g_ld = PythonToCppGroup(ld_grp_obj);
  H5::H5File readInFile;
  H5::Group g_ld;
  try{
    readInFile = H5::H5File(fn, H5F_ACC_RDONLY);
    //h5cpp::Group g_ld = h5cpp::Group(readInFile->root().open_group(path));
    g_ld = readInFile.openGroup(path);
  }
  catch(H5::Exception &e)
  {
    e.printErrorStack();
  }
  string TYPE;
  readAttrFromH5(g_ld, string("TYPE"), TYPE);
  float SCALE;
  readAttrFromH5(g_ld, string("SCALE"), SCALE);
  Int6 bb;
  readAttrFromH5(g_ld, "BOX", bb);
  Float3 WORLD_OFFSET;
  readAttrFromH5(g_ld, string("WORLD_OFFSET"), WORLD_OFFSET);
#ifndef NDEBUG
  std::printf("if you read this, lattice data in c++ is %s\n", TYPE.c_str());
#endif
  readInFile.close();

  //T xmin,T ymin, T zmin,T xmax,T ymax, T zmax
  BBox3 bbox(bb[0],bb[2],bb[4],bb[1],bb[3],bb[5]);
  
  //allocate memory and let boost::python handle it by the return!
  PyLd *pyld= new PyLd(TYPE, bbox, SCALE);
  pyld->SetOriginPosition(WORLD_OFFSET);
  //py::tuple bla = pyld->GetOriginPosition();
  //printf("1: %f, 2: %f, 3: %f\n", bla[0],bla[1],bla[2]);
  return pyld;
}

//pointer issue changed to boost::shared_ptr
#if 0 //depricate since H5Cpp
PyLd* read_lattice_data_from_hdf(const py::object &ld_grp_obj)
{
  h5cpp::Group g_ld = PythonToCppGroup(ld_grp_obj);
  std::printf("if you read this, lattice data is in c++\n");
  typedef polymorphic_latticedata::LatticeData LD;
//  return new PyLd(new LD(ld));
  std::auto_ptr<LD> ldp(LD::ReadHdf(g_ld));
// 
//   typedef polymorphic_latticedata::Derived<LatticeDataQuad3d> LD1;
//   typedef polymorphic_latticedata::Derived<LatticeDataFCC> LD2;
    return new PyLd(ldp.release()); //this is for std::auto_ptr
//  return new PyLd(ldp.get());
//  return new PyLd(ldp.get());
}
#endif

#if 0 //depricated since H5Cpp
void write_lattice_data_to_hdf(py::object py_h5grp, const std::string &name, const PyLd *cpp_py_ld)
{
  h5cpp::Group g = PythonToCppGroup(py_h5grp);
  h5cpp::Group g_ld = g.create_group(name);
  cpp_py_ld->get().WriteHdf(g_ld);
}
#endif

void write_lattice_data_to_hdf_by_filename(const string fn, const string path, const PyLd *cpp_py_ld)
{
  try {
    H5::H5File *writeToFile = new H5::H5File(fn, H5F_ACC_RDWR);
    H5::Group g = writeToFile->createGroup(path);
    //cpp_py_ld->get().WriteHdf(g);
    cpp_py_ld->get().Lattice2Hdf(g);
    //h5cpp::Group g = PythonToCppGroup(py_h5grp);
    //h5cpp::Group g_ld = g.create_group(name);
    //cpp_py_ld->get().WriteHdf(g_ld);
  } catch(H5::Exception &e) {
    e.printErrorStack();
  }
}

void SetupFieldLattice(const FloatBBox3 &wbbox, int dim, float spacing, float safety_spacing, LatticeDataQuad3d &ld);

PyLd* PySetupFieldLattice(const py::object &py_wbbox, int dim, float spacing, float safety_spacing)
{
  cout << "setting up lattice field in python" << endl;
  FloatBBox3 wbbox = BBoxFromPy<float, 3>(py_wbbox);  
  LatticeDataQuad3d ld;
  SetupFieldLattice(wbbox, dim, spacing, safety_spacing, ld);
  typedef polymorphic_latticedata::Derived<LatticeDataQuad3d> LD;
  //PyLd pyld(new polymorphic_latticedata::Derived<LatticeDataQuad3d>(ld));
  BBox3 bbox_of_input = ld.Box();
#ifdef DEBUG
  cout << bbox_of_input << endl;
#endif
  PyLd *pyld = new PyLd("QUAD3D",bbox_of_input, spacing); 
  return pyld;
}



namespace mw_py_impl
{


void exportLatticeData()
{
  py::class_<PyLd>("LatticeData",
                   py::init<std::string, py::object, float>())
    .def(py::init<PyLd>())
    .def("GetScale", &PyLd::Scale)
    .def("SetScale", &PyLd::SetScale)
    .def("GetBoxRavel", &PyLd::Box)
    .def("SetOriginPosition", &PyLd::SetOriginPosition)
    .def("GetOriginPosition", &PyLd::GetOriginPosition)
    .def("GetWorldBoxRavel", &PyLd::GetWorldBox)
    .def("NbCount", &PyLd::NbCount)
    .def("NbLattice", &PyLd::NbLattice)
    .def("LatticeToWorld", &PyLd::LatticeToWorld)
    .def("LatticeToSite", &PyLd::LatticeToSite)
    .def("WorldToLattice", &PyLd::WorldToLattice)
    .def("IsInsideLattice", &PyLd::IsInsideLattice)
    .def("GetAxisDirLen", &PyLd::GetAxisDirLen)
    .def("SetCellCentering", &PyLd::SetCellCentering)
    .def("SiteToLattice", &PyLd::SiteToLattice)
    .def("__str__", &PyLd::toString)
    ;

//   py::def("read_lattice_data_from_hdf", read_lattice_data_from_hdf,
//           py::return_value_policy<py::manage_new_object>());
  py::def("read_lattice_data_from_hdf_by_filename", read_lattice_data_from_hdf_by_filename,
          py::return_value_policy<py::manage_new_object>());
//      py::def("read_lattice_data_from_hdf_by_filename", read_lattice_data_from_hdf_by_filename);
//   py::def("write_lattice_data_to_hdf", write_lattice_data_to_hdf);
  py::def("write_lattice_data_to_hdf_by_filename", write_lattice_data_to_hdf_by_filename);
  py::def("SetupFieldLattice", PySetupFieldLattice, py::return_value_policy<py::manage_new_object>());
  
  //serialize fuck
  mw_py_impl::LdFromPy<LatticeDataQuad3d>::Register();
  mw_py_impl::LdFromPy<LatticeDataFCC>::Register();
  mw_py_impl::LdToPy<LatticeDataQuad3d>::Register();
  mw_py_impl::LdToPy<LatticeDataFCC>::Register();
}

}
