/*
 * Author: Steven Ludtke, 04/10/2003 (sludtke@bcm.edu)
 * Copyright (c) 2000-2006 Baylor College of Medicine
 * 
 * This software is issued under a joint BSD/GNU license. You may use the
 * source code in this file under either license. However, note that the
 * complete EMAN2 and SPARX software packages have some GPL dependencies,
 * so you are responsible for compliance with the licenses of these packages
 * if you opt to use BSD licensing. The warranty disclaimer below holds
 * in either instance.
 * 
 * This complete copyright notice must be included in any revised version of the
 * source code. Additional authorship citations may be added, but existing
 * author citations must be preserved.
 * 
 * This program is free software; you can redistribute it and/or modify
 * it under the terms of the GNU General Public License as published by
 * the Free Software Foundation; either version 2 of the License, or
 * (at your option) any later version.
 * 
 * This program is distributed in the hope that it will be useful,
 * but WITHOUT ANY WARRANTY; without even the implied warranty of
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
 * GNU General Public License for more details.
 * 
 * You should have received a copy of the GNU General Public License
 * along with this program; if not, write to the Free Software
 * Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA 02111-1307 USA
 * 
 * */

#ifndef eman__typeconverter_h__
#define eman__typeconverter_h__ 1

#define PY_ARRAY_UNIQUE_SYMBOL PyArrayHandle

#include "emobject.h"
#include "transform.h"
#include "geometry.h"
#include "emdata.h"
#include "xydata.h"
#include "exception.h"

#include <boost/python.hpp>
#include <boost/python/to_python_converter.hpp>
#include <boost/python/detail/api_placeholder.hpp>
#include <numpy/arrayobject.h>

#include <vector>
#include <map>
#include <string>


namespace python = boost::python;
using std::vector;
using std::map;

#include <iostream>
using std::cout;
using std::endl;


namespace EMAN {

    python::numeric::array make_numeric_array(float * data, vector<int> dims);
    python::numeric::array make_numeric_complex_array(std::complex<float> * data,
                                                      vector<int> dims);
	class EMNumPy {
	public:
		/** Get an EMData image's pixel data as a numeric numpy array.
		 * The array and EMData image share the same memory block.
		 */
		static python::numeric::array em2numpy(EMData *image);

		/** Create an EMData image from a numeric numpy array.
		 * The array data is copied to image element by element, 
		 * since Python float use 8 bytes but EMData always use 4 byte float.
		 * Note: the array size is (nz,ny,nx) corresponding to image (nx,ny,nz).
		 */
		static void numpy2em(python::numeric::array& array, EMData* image);
    };

	
    template <class T>
    struct vector_to_python : python::to_python_converter<vector<T>,
														  vector_to_python<T> >
    {
		static PyObject* convert(vector<T> const& v)
		{
			python::list result;
	    
			for (size_t i = 0; i < v.size(); i++) {
				result.append(v[i]);
			}
	    
			return python::incref(python::list(result).ptr());
		}
    };

	template <class T>
	struct tuple3_to_python : python::to_python_converter<T, tuple3_to_python<T> >
	{
		static PyObject* convert(T const& p)
		{
			python::tuple result = python::make_tuple(p[0], p[1], p[2]);
			return python::incref(python::tuple(result).ptr());
		}
	};
	
	
    template <class T>
    struct map_to_python : python::to_python_converter<map<std::string, T>,
													   map_to_python<T> >
    {
		static PyObject* convert(map<std::string, T> const& d)
		{
			python::dict result;

			typedef typename map<std::string, T>::const_iterator MI;
			for (MI p = d.begin(); p != d.end(); p++) {
				result[p->first] = p->second;
			}
	
			return python::incref(python::dict(result).ptr());
		}
    };

	template <class S,class T>
	struct map_to_python_2 : python::to_python_converter<map<S, T>,
 													     map_to_python_2<S,T> >
   {
	   static PyObject* convert(map<S, T> const& d)
	   {
		   python::dict result;

		   typedef typename map<S, T>::const_iterator MI;
		   for (MI p = d.begin(); p != d.end(); p++) {
			   result[p->first] = p->second;
		   }
	
		   return python::incref(python::dict(result).ptr());
	   }
   };
	
    struct Dict_to_python : python::to_python_converter<Dict, Dict_to_python>
    {
		static PyObject* convert(Dict const& dd)
		{
			python::dict result;
			vector<std::string> keys = dd.keys();
			vector<EMObject> values = dd.values();
			for (unsigned int i = 0; i < keys.size(); i++) {
				result[keys[i]] = values[i];
			}
	
			return python::incref(python::dict(result).ptr());
		}
    };


	struct EMObject_to_python : python::to_python_converter<EMObject,
                                EMObject_to_python>
	{
		static PyObject* convert(EMObject const& emobj);
	};

    template<std::size_t NumDims>
    struct MArrayND_to_python : python::to_python_converter<
        boost::multi_array_ref<float, NumDims>, 
        MArrayND_to_python<NumDims> >
    {
        static PyObject* convert(boost::multi_array_ref<float, NumDims> const & marray)
        {
            vector<int> dims; 
            const size_t * shape = marray.shape();
            int ndim = marray.num_dimensions();
            for (int i = ndim-1; i >= 0; i--) {
                dims.push_back(shape[i]);
            }

            float * data = (float*)marray.data();
            python::numeric::array numarray = make_numeric_array(data, dims);
    
            return python::incref(numarray.ptr());
        }
    };
    
    
    template<std::size_t NumDims>
    struct MCArrayND_to_python : python::to_python_converter<
        boost::multi_array_ref<std::complex<float>, NumDims>, 
        MCArrayND_to_python<NumDims> >
    {
        static PyObject* convert(boost::multi_array_ref<std::complex<float>, NumDims> const & mcarray)
        {
            vector<int> dims;
            const size_t * shape = mcarray.shape();
            int ndim = mcarray.num_dimensions();
            for (int i = ndim-1; i >= 0; i--) {
                dims.push_back(shape[i]);
            }
            
            std::complex<float> * data = (std::complex<float>*)mcarray.data();
            python::numeric::array numarray = make_numeric_complex_array(data, dims);
    
            return python::incref(numarray.ptr());
        }
    };
    
    

    
    template <class T>
    struct vector_from_python
    {
		vector_from_python()
		{
			python::converter::registry::push_back(&convertible, &construct,
												   python::type_id<vector<T> >());
		}
    
		static void* convertible(PyObject* obj_ptr)
		{
			if (!(PyList_Check(obj_ptr) || PyTuple_Check(obj_ptr)
				  || PyIter_Check(obj_ptr)  || PyRange_Check(obj_ptr))) {
				return 0;
			}
	
			return obj_ptr;
		}

    
		static void construct(PyObject* obj_ptr,
							  python::converter::rvalue_from_python_stage1_data* data)
		{
			void* storage = ((python::converter::rvalue_from_python_storage<vector<T> >*)
							 data)->storage.bytes;
			new (storage) vector<T>();

			data->convertible = storage;

			vector<T>& result = *((vector<T>*) storage);
	
			python::handle<> obj_iter(PyObject_GetIter(obj_ptr));
	
			while(1) {
				python::handle<> py_elem_hdl(python::allow_null(PyIter_Next(obj_iter.get())));
				if (PyErr_Occurred()) {
					python::throw_error_already_set();
				}
	    
				if (!py_elem_hdl.get()) {
					break;
				}
	    
				python::object py_elem_obj(py_elem_hdl);
				python::extract<T> elem_proxy(py_elem_obj);
				result.push_back(elem_proxy());
			}
		}
    };
    
    template <class T>
    struct map_from_python
    {
		map_from_python()
		{
			python::converter::registry::push_back(&convertible, &construct,
												   python::type_id<map<std::string, T> >());
		}
    
		static void* convertible(PyObject* obj_ptr)
		{
			if (!(PyDict_Check(obj_ptr))) {
				return 0;
			}
	
			return obj_ptr;
		}

    
		static void construct(PyObject* obj_ptr,
							  python::converter::rvalue_from_python_stage1_data* data)
		{
			void* storage = ((python::converter::rvalue_from_python_storage<map<std::string, T> >*)
							 data)->storage.bytes;
			new (storage) map<std::string, T>();
			data->convertible = storage;
			map<std::string, T>& result = *((map<std::string, T>*) storage);

			python::dict d = python::extract<python::dict>(obj_ptr);
			
			python::list k = d.keys();
			python::list v = d.values();
			long l = python::len(k);
	
			for(long i = 0; i < l; i++) {
				std::string key = python::extract<std::string>(k[i]);
				T val = python::extract<T>(v[i]);
				result[key] = val;
			}

		}
    };

    struct Dict_from_python
    {
		Dict_from_python()
		{
			python::converter::registry::push_back(&convertible, &construct,
												   python::type_id<Dict>());
		}
    
		static void* convertible(PyObject* obj_ptr)
		{
			if (!(PyDict_Check(obj_ptr))) {
				return 0;
			}
	
			return obj_ptr;
		}

    
		static void construct(PyObject* obj_ptr,
							  python::converter::rvalue_from_python_stage1_data* data)
		{
			void* storage = ((python::converter::rvalue_from_python_storage<Dict>*)
							 data)->storage.bytes;
			new (storage) Dict();
			data->convertible = storage;
			Dict& result = *((Dict*) storage);

			python::dict d = python::extract<python::dict>(obj_ptr);
			
			python::list k = d.keys();
			python::list v = d.values();
			long l = python::len(k);
	
			for(long i = 0; i < l; i++) {
				std::string key = python::extract<std::string>(k[i]);
				EMObject val = python::extract<EMObject>(v[i]);
				result.put(key, val);
			}

		}
    };
	
	template<class T, class T2>
	struct tuple2_from_python
	{
		tuple2_from_python()
		{
			python::converter::registry::push_back(&convertible, &construct,
					python::type_id<T>());
		}

		static void* convertible(PyObject* obj_ptr)
		{
			if (!(PyList_Check(obj_ptr) || PyTuple_Check(obj_ptr)
									|| PyIter_Check(obj_ptr)  || PyRange_Check(obj_ptr))) {
				return 0;
			}

			return obj_ptr;
		}


		static void construct(PyObject* obj_ptr,
								python::converter::rvalue_from_python_stage1_data* data)
		{
			void* storage = ((python::converter::rvalue_from_python_storage<T>*)
					data)->storage.bytes;
			new (storage) T();

			data->convertible = storage;

			T& result = *((T*) storage);

			python::handle<> obj_iter(PyObject_GetIter(obj_ptr));
			int i = 0;
	
			while(1) {
				python::handle<> py_elem_hdl(python::allow_null(PyIter_Next(obj_iter.get())));
				if (PyErr_Occurred()) {
					python::throw_error_already_set();
				}

				if (!py_elem_hdl.get()) {
					break;
				}

				python::object py_elem_obj(py_elem_hdl);
				python::extract<T2> elem_proxy(py_elem_obj);
				result[i] = elem_proxy();
				i++;
			}
		}
	};


	template<class T, class T2>
	struct tuple3_from_python
    {
		tuple3_from_python()
		{
			python::converter::registry::push_back(&convertible, &construct,
												   python::type_id<T>());
		}
    
		static void* convertible(PyObject* obj_ptr)
		{
			if (!(PyList_Check(obj_ptr) || PyTuple_Check(obj_ptr)
				  || PyIter_Check(obj_ptr)  || PyRange_Check(obj_ptr))) {
				return 0;
			}
	
			return obj_ptr;
		}

    
		static void construct(PyObject* obj_ptr,
							  python::converter::rvalue_from_python_stage1_data* data)
		{
			void* storage = ((python::converter::rvalue_from_python_storage<T>*)
							 data)->storage.bytes;
			new (storage) T();

			data->convertible = storage;

			T& result = *((T*) storage);
	
			python::handle<> obj_iter(PyObject_GetIter(obj_ptr));
			int i = 0;
			
			while(1) {
				python::handle<> py_elem_hdl(python::allow_null(PyIter_Next(obj_iter.get())));
				if (PyErr_Occurred()) {
					python::throw_error_already_set();
				}
	    
				if (!py_elem_hdl.get()) {
					break;
				}
	    
				python::object py_elem_obj(py_elem_hdl);
				python::extract<T2> elem_proxy(py_elem_obj);
				result[i] = elem_proxy();
				i++;
			}
		}
    };

	
    struct emobject_array_from_python
    {
		emobject_array_from_python()
		{
			python::converter::registry::push_back(&convertible, &construct,
												   python::type_id<EMObject>());
		}
    
		static void* convertible(PyObject* obj_ptr)
		{
#if 0
			if (!(PyList_Check(obj_ptr) || PyTuple_Check(obj_ptr)
				  || PyIter_Check(obj_ptr)  || PyRange_Check(obj_ptr))) {
				return 0;
			}
#endif
            if (!(PyList_Check(obj_ptr) || PyTuple_Check(obj_ptr))) {
                return 0;
            }
			return obj_ptr;
		}

    
		static void construct(PyObject* obj_ptr,
							  python::converter::rvalue_from_python_stage1_data* data)
		{
			void* storage = ((python::converter::rvalue_from_python_storage<EMObject>*)
							 data)->storage.bytes;
			new (storage) EMObject();

			data->convertible = storage;

			EMObject& result = *((EMObject*) storage);
			
			PyObject * first_obj = PyObject_GetItem(obj_ptr, PyInt_FromLong(0));
			EMObject::ObjectType object_type;
			if( PyObject_TypeCheck(first_obj, &PyInt_Type) ) {
				object_type = EMObject::INTARRAY;
			}
			else if( PyObject_TypeCheck(first_obj, &PyFloat_Type) ) {
				object_type = EMObject::FLOATARRAY;
			}
			else if( PyObject_TypeCheck(first_obj, &PyString_Type) ) {
				object_type = EMObject::STRINGARRAY;
			}
			else {
				object_type = EMObject::UNKNOWN;
			}
			
			python::handle<> obj_iter(PyObject_GetIter(obj_ptr));
			vector<int> iarray;
			vector<float> farray;
			vector<string> strarray;
			
			while(1) {
				python::handle<> py_elem_hdl(python::allow_null(PyIter_Next(obj_iter.get())));
				if (PyErr_Occurred()) {
					python::throw_error_already_set();
				}
	    
				if (!py_elem_hdl.get()) {
					break;
				}
	    
				python::object py_elem_obj(py_elem_hdl);
				if (object_type == EMObject::INTARRAY) {
					python::extract<int> elem_proxy1(py_elem_obj);
					iarray.push_back(elem_proxy1());
				}
				else if (object_type == EMObject::FLOATARRAY) {
					python::extract<float> elem_proxy1(py_elem_obj);
					farray.push_back(elem_proxy1());
				}
				else if (object_type == EMObject::STRINGARRAY) {
					python::extract<string> elem_proxy2(py_elem_obj);
					strarray.push_back(elem_proxy2());
				}
				else if (object_type == EMObject::UNKNOWN) {
					LOGERR("Unknown array type ");
				}
			}
			if (object_type == EMObject::INTARRAY) {
				result = EMObject(iarray);
			}
			else if (object_type == EMObject::FLOATARRAY) {
				result = EMObject(farray);
			}
			else if (object_type == EMObject::STRINGARRAY) {
				result = EMObject(strarray);
			}
		}
    };


    	
	struct emobject_string_from_python
    {
		emobject_string_from_python()
		{
			python::converter::registry::push_back(&convertible, &construct,
												   python::type_id<EMObject>());
		}
    
		static void* convertible(PyObject* obj_ptr)
		{
			const char * type_name = obj_ptr->ob_type->tp_name;
			if (type_name == 0 || strcmp(type_name, "str") != 0) {
				return 0;
			}
			return obj_ptr;
		}
    
		static void construct(PyObject* obj_ptr,
							  python::converter::rvalue_from_python_stage1_data* data)
		{
			void* storage =
				((python::converter::rvalue_from_python_storage<EMObject>*)
				 data)->storage.bytes;
			new (storage) EMObject();

			data->convertible = storage;
			EMObject& result = *((EMObject*) storage);
			string str = python::extract<string>(obj_ptr);	   
			result = EMObject(str);
		}
    };
    
	struct emobject_emdata_from_python
    {
		emobject_emdata_from_python()
		{
			python::converter::registry::push_back(&convertible, &construct,
												   python::type_id<EMObject>());
		}
    
		static void* convertible(PyObject* obj_ptr)
		{
			const char * type_name = obj_ptr->ob_type->tp_name;
			if (type_name == 0 || strcmp(type_name, "EMData") != 0) {
				return 0;
			}
			return obj_ptr;
		}
    
		static void construct(PyObject* obj_ptr,
							  python::converter::rvalue_from_python_stage1_data* data)
		{
			void* storage =
				((python::converter::rvalue_from_python_storage<EMObject>*)
				 data)->storage.bytes;
			new (storage) EMObject();

			data->convertible = storage;
			EMObject& result = *((EMObject*) storage);
//			std::auto_ptr<EMData> emdata = python::extract< std::auto_ptr<EMData> >(obj_ptr);   
//			result = EMObject(emdata.get());
//			emdata.release();
			EMData * emdata = python::extract<EMData*>(obj_ptr);   
			result = EMObject(emdata);
		}
    };

//     struct emobject_transform3d_from_python
//     {
//     	emobject_transform3d_from_python()
//     	{
//     		python::converter::registry::push_back(&convertible, &construct,
// 												   python::type_id<EMObject>());
//     	}
//     	
//     	static void* convertible(PyObject* obj_ptr)
// 		{
// 			const char * type_name = obj_ptr->ob_type->tp_name;
// 			if (type_name == 0 || strcmp(type_name, "Transform3D") != 0) {
// 				return 0;
// 			}
// 			return obj_ptr;
// 		}
// 		
// 		static void construct(PyObject* obj_ptr,
// 							  python::converter::rvalue_from_python_stage1_data* data)
// 		{
// 			void* storage =
// 				((python::converter::rvalue_from_python_storage<EMObject>*)
// 				 data)->storage.bytes;
// 			new (storage) EMObject();
// 
// 			data->convertible = storage;
// 			EMObject& result = *((EMObject*) storage);
// 			Transform3D * trans = python::extract<Transform3D*>(obj_ptr);   
// 			result = EMObject(trans);
// 		}
//     };
	
    struct emobject_transform_from_python
    {
    	emobject_transform_from_python()
    	{
    		python::converter::registry::push_back(&convertible, &construct,
												   python::type_id<EMObject>());
    	}
    	
    	static void* convertible(PyObject* obj_ptr)
		{
			const char * type_name = obj_ptr->ob_type->tp_name;
			if (type_name == 0 || strcmp(type_name, "Transform") != 0) {
				return 0;
			}
			return obj_ptr;
		}
		
		static void construct(PyObject* obj_ptr,
							  python::converter::rvalue_from_python_stage1_data* data)
		{
			void* storage =
				((python::converter::rvalue_from_python_storage<EMObject>*)
				 data)->storage.bytes;
			new (storage) EMObject();

			data->convertible = storage;
			EMObject& result = *((EMObject*) storage);
			std::auto_ptr<Transform> trans = python::extract< std::auto_ptr<Transform> >(obj_ptr);
			result = EMObject(trans.get());
			trans.release();
		}
    };
    
	struct emobject_xydata_from_python
    {
		emobject_xydata_from_python()
		{
			python::converter::registry::push_back(&convertible, &construct,
												   python::type_id<EMObject>());
		}
    
		static void* convertible(PyObject* obj_ptr)
		{
			const char * type_name = obj_ptr->ob_type->tp_name;
			if (type_name == 0 || strcmp(type_name, "XYData") != 0) {
				return 0;
			}
			return obj_ptr;
		}
    
		static void construct(PyObject* obj_ptr,
							  python::converter::rvalue_from_python_stage1_data* data)
		{
			void* storage =
				((python::converter::rvalue_from_python_storage<EMObject>*)
				 data)->storage.bytes;
			new (storage) EMObject();

			data->convertible = storage;
			EMObject& result = *((EMObject*) storage);
			XYData * xydata = python::extract<XYData*>(obj_ptr);	   
			result = EMObject(xydata);
		}
    };
    
    struct emobject_null_from_python
    {
    	emobject_null_from_python()
    	{
    		python::converter::registry::push_back(&convertible, &construct,
												   python::type_id<EMObject>());
    	}
    	
    	static void* convertible(PyObject* obj_ptr)
		{
			const char * type_name = obj_ptr->ob_type->tp_name;
			
			if(string(type_name) == "NoneType") {
				return obj_ptr;
			}
			else {
				return 0;
			}
		}
		
		static void construct(PyObject* obj_ptr,
							  python::converter::rvalue_from_python_stage1_data* data)
		{
			void* storage =
				((python::converter::rvalue_from_python_storage<EMObject>*)
				 data)->storage.bytes;
			new (storage) EMObject();
			
			data->convertible = storage;
			//EMObject& result = *((EMObject*) storage);
		}
    	
    };

}


#endif

/* vim: set ts=4 noet nospell: */
