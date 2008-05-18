/**
 * $Id$
 */

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

/** This file is a part of "emdata.h", to use functions in this file,
 * you should "#include "emdata.h",
 * NEVER directly include this file. */ 

#ifndef emdata__metadata_h__
#define emdata__metadata_h__ 

public:
/** return the amplitudes of the FFT including the left half
 *
 * @exception ImageFormatException If the image is not a complex image.
 * @return The current FFT image's amplitude image.
 */
EMData *get_fft_amplitude();

/** return the amplitudes of the 2D FFT including the left half
 *     PRB
 * @exception ImageFormatException If the image is not a complex image.
 * @return The current FFT image's amplitude image.
 */
EMData *get_fft_amplitude2D();

/** return the phases of the FFT including the left half
 *
 * @exception ImageFormatException If the image is not a complex image.
 * @return The current FFT image's phase image.
 */
EMData *get_fft_phase();

/** Get the image pixel density data in a 1D float array.
 * @return The image pixel density data.
 */
float *get_data() const;


/** Get the image pixel density data in a 1D float array - const version of get_data
 * @return The image pixel density data.
 */
const float * const get_const_data() const;

/** Mark EMData as changed, statistics, etc will be updated at need.*/
inline void update()
{
	flags |= EMDATA_NEEDUPD;
	changecount++;
}


/** check whether the image physical file has the CTF info or not.
 * @return True if it has the CTF information. Otherwise, false.
*/
inline bool has_ctff() const
{
	if ((flags & EMDATA_HASCTFF)) {
		return true;
	}
		
	return false;
}


/** Calculates the density value at the peak of the
 * image histogram, sort of like the mode of the density.
 * @return The density value at the peak of the image histogram.
*/
float calc_center_density();


/** Calculates sigma above and below the mean and returns the
 * difference between them.
 * @return The difference between sigma above and below the mean.
 */
float calc_sigma_diff();


/** Calculates the coordinates of the minimum-value pixel.
 * @return The coordinates of the minimum-value pixel.
 */
IntPoint calc_min_location() const;

		
/** Calculates the coordinates of the maximum-value pixel.
 * @return The coordinates of the maximum-value pixel.
 */
IntPoint calc_max_location() const;


/** Calculates the index of minimum-value pixel when assuming
 * all pixels are in a 1D array.
 * @return Index of the minimum-value pixel.
 */
int calc_min_index() const;


/** Calculates the index of maximum-value pixel when assuming
 * all pixels are in a 1D array.
 * @return Index of the maximum-value pixel.
 */
int calc_max_index() const;


/** Calculate and return a sorted list of pixels whose values
 * are above a specified threshold. The pixels are sorted 
 * from high to low.
 *
 * @param threshold The specified pixel value. Returned pixels
 *        should have higher values than it.
 * @return A sorted list of pixels with their values, and
 *     locations. Their values are higher than threshold.
 */
vector<Pixel> calc_highest_locations(float threshold);


/** Calculates the mean pixel values around the (1 pixel) edge
 * of the image.
 *
 * @return The mean pixel values around the (1 pixel) edge.
*/
float get_edge_mean() const;


/** Calculates the circular edge mean by applying a circular
 * mask on 'this' image.
 * @return The circular edge mean.
 */
float get_circle_mean();


/** Get ctf parameter of this image.
 * @return The ctf parameter.
 */
Ctf * get_ctf() const;


/** Set the CTF parameter of this image.
 * @param ctf The CTF parameter object.
 */
void set_ctf(Ctf * ctf);


/** Get 'this' image's translation vector from the original
 * location.
 * @return 'this' image's translation vector from the original
 * location.
 */
inline Vec3f get_translation() const
{
	return all_translation;
}


/** Set 'this' images' translation vector from the original
 * location.
 * @param t The new translation vector.
 */
inline void set_translation(const Vec3f &t)
{
	all_translation = t;
}


/** Set 'this' images' translation vector from the original
 * location.
 * @param dx The translation distance in x direction.
 * @param dy The translation distance in y direction.
 * @param dz The translation distance in z direction.
 */
inline void set_translation(float dx, float dy, float dz)
{
	all_translation = Vec3f(dx, dy, dz);
}


/** Get the 3D orientation of 'this' image.
 * @return The 3D orientation of 'this' image.
 */
inline Transform3D get_transform() const
{
	return Transform3D( (float)attr_dict["euler_alt"],
			    (float)attr_dict["euler_az"],
			    (float)attr_dict["euler_phi"]);
} 


/** Define the 3D orientation of this particle, also
 * used to indicate relative rotations for reconstructions
 *
 * @param alt 'alt' Euler angle in EMAN convention.
 * @param az  'az' Euler angle in EMAN convention.
 * @param phi 'phi' Euler angle in EMAN convention.
 */
inline void set_rotation(float az, float alt, float phi)
{
    attr_dict["orientation_convention"] = "EMAN";
	attr_dict["euler_alt"]=alt;
	attr_dict["euler_az"]=az;
	attr_dict["euler_phi"]=phi;
}


/** Define the 3D orientation of this particle
 * Orientation information is extracted from a Transform3D object and stored internally
 * in EMAN (az,alt,phi) format
 * @param t3d a Transform3D object containing the particle orientation
 */
inline void set_rotation(const Transform3D& t3d)
{
	Dict d = t3d.get_rotation(Transform3D::EMAN);
	attr_dict["orientation_convention"] = "EMAN";
	attr_dict["euler_alt"] = (float) d["alt"];
	attr_dict["euler_az"] = (float) d["az"];
	attr_dict["euler_phi"] = (float) d["phi"];;
}


/** Resize 'this' image.
 *
 * @param nx  x size of this image.
 * @param ny  y size of this image.
 * @param nz  z size of this image.
 $ @exception BadAllocException if memory allocation returns a null pointer
 */
void set_size(int nx, int ny=1, int nz=1);


/** Resize 'this' complex image.
 *
 * @param nx  x size of this image.
 * @param ny  y size of this image.
 * @param nz  z size of this image.
 */
void set_complex_size(int nx, int ny=1, int nz=1) {
	set_size(nx*2, ny, nz); 
}


/** Set the path
 * @param new_path The new path.
 */
inline void set_path(const string & new_path)
{
	path = new_path;
}


/** Set the number of paths.
 * @param n The number of paths.
 */
inline void set_pathnum(int n)
{
	pathnum = n;
}


/** Get image raw pixel data in a 2D multi-array format. The
 * array shares the memory space with the image data.
 * Notice: the subscription order is d[y][x] in Python, it's d[x][y] in C++
 *
 * It should be used on 2D image only.
 *
 * @return 2D multi-array format of the raw data.
 */
MArray2D get_2dview() const;

	
/** Get image raw pixel data in a 3D multi-array format. The
 * array shares the memory space with the image data.
 * Notice: the subscription order is d[z][y][x] in Python, it's d[x][y][z] in C++ --grant Tang
 *
 * It should be used on 3D image only.
 *
 * @return 3D multi-array format of the raw data.
 */
MArray3D get_3dview() const;

		
/** Get complex image raw pixel data in a 2D multi-array format. 
 * The array shares the memory space with the image data.
 *
 * It should be used on 2D image only.
 *
 * @return 2D multi-array format of the raw data.
 */
MCArray2D get_2dcview() const;

		
/** Get complex image raw pixel data in a 3D multi-array format. 
 * The array shares the memory space with the image data.
 *
 * It should be used on 3D image only.
 *
 * @return 3D multi-array format of the raw data.
 */
MCArray3D get_3dcview() const;

		
/** Get pointer to a complex image raw pixel data in a 3D multi-array format. 
 * The array shares the memory space with the image data.
 *
 * It should be used on 3D image only.
 *
 * @return Pointer to a 3D multi-array format of the raw data.
 */
MCArray3D* get_3dcviewptr() const;

		
/** Get image raw pixel data in a 2D multi-array format. The
 * data coordinates is translated by (x0,y0) such that
 * array[y0][x0] points to the pixel at the origin location.
 * the data coordiates translated by (x0,y0). The
 * array shares the memory space with the image data.
 *
 * It should be used on 2D image only.
 *
 * @param x0 X-axis translation amount.
 * @param y0 Y-axis translation amount.
 * @return 2D multi-array format of the raw data.
 */
MArray2D get_2dview(int x0, int y0) const;


/** Get image raw pixel data in a 3D multi-array format. The
 * data coordinates is translated by (x0,y0,z0) such that
 * array[z0][y0][x0] points to the pixel at the origin location.
 * the data coordiates translated by (x0,y0,z0). The
 * array shares the memory space with the image data.
 *
 * It should be used on 3D image only.
 *
 * @param x0 X-axis translation amount.
 * @param y0 Y-axis translation amount.
 * @param z0 Z-axis translation amount.
 * @return 3D multi-array format of the raw data.
 */
MArray3D get_3dview(int x0, int y0, int z0) const;


/** Get complex image raw pixel data in a 2D multi-array format. The
 * data coordinates is translated by (x0,y0) such that
 * array[y0][x0] points to the pixel at the origin location.
 * the data coordiates translated by (x0,y0). The
 * array shares the memory space with the image data.
 *
 * It should be used on 2D image only.
 *
 * @param x0 X-axis translation amount.
 * @param y0 Y-axis translation amount.
 * @return 2D multi-array format of the raw data.
 */
MCArray2D get_2dcview(int x0, int y0) const;


/** Get complex image raw pixel data in a 3D multi-array format. The
 * data coordinates is translated by (x0,y0,z0) such that
 * array[z0][y0][x0] points to the pixel at the origin location.
 * the data coordiates translated by (x0,y0,z0). The
 * array shares the memory space with the image data.
 *
 * It should be used on 3D image only.
 *
 * @param x0 X-axis translation amount.
 * @param y0 Y-axis translation amount.
 * @param z0 Z-axis translation amount.
 * @return 3D multi-array format of the raw data.
 */
MCArray3D get_3dcview(int x0, int y0, int z0) const;


/** The generic way to get any image header information
 * given a header attribute name. If the attribute does not exist,
 * it will raise an exception.
 *
 * @param attr_name The header attribute name.
 * @return The attribute value.
 * @exception NotExistingObjectException when attribute not exist
 */
EMObject get_attr(const string & attr_name) const;

/** The generic way to get any image header information
 * given a header attribute name. If the attribute does not exist,
 * it will return a default EMObject() object, which will be converted
 * to None in Python. Or return any object user want.
 *
 * @param attr_name The header attribute name.
 * @param em_obj the default attribute to return when this attr_name not exist in attr_dict
 * @return The attribute value, default to None.
 */
EMObject get_attr_default(const string & attr_name, const EMObject & em_obj = EMObject()) const;
		
/** Set a header attribute's value.
 *
 * @param key The header attribute name.
 * @param val The attribute value.
 */
inline void set_attr(const string & key, EMObject val)
{
	attr_dict[key] = val;
}


/** Get the image attribute dictionary containing all the
 * image attribute names and attribute values.
 *
 * @return The image attribute dictionary containing all
 * attribute names and values.
 */
Dict get_attr_dict() const;


/** Merge the new values with the existing dictionary.
 *
 * @param new_dict The new attribute dictionary.
 */
void set_attr_dict(const Dict & new_dict);


/** Delete the attribute from dictionary.
 * 
 * @param attr_name the attribute name to be removed
 * */
 void del_attr(const string & attr_name);

 
 /** Delete the attributes from the dictionary.
  * 
  * @param del_keys the attrutes' names to be removed
  * */
 void del_attr_dict(const vector<string> & del_keys);


/** Get the image x-dimensional size.
 * @return Image x-dimensional size.
 */
inline int get_xsize() const
{
	return nx;
}

		
/** Get the image y-dimensional size.
 * @return Image y-dimensional size.
 */
inline int get_ysize() const
{
	return ny;
}

		
/** Get the image z-dimensional size.
 * @return Image z-dimensional size.
 */
inline int get_zsize() const
{
	return nz;
}


/** Get image dimension.
 * @return image dimension.
 */
inline int get_ndim() const
{
	if (nz <= 1) {
		if (ny <= 1) {
			return 1;
		}
		else {
			return 2;
		}
	}

	return 3;
}


/** Has this image been shuffled?
 * @return Whether this image has been shuffled to put origin in the center.
 */
inline bool is_shuffled() const
{  //     PRB
	if (flags & EMDATA_SHUFFLE) {
		return true;
	}
	else {
		return false;
	}
}

	
/** Is this a FH image?
 * @return Whether this is a FH image or not.
 */
inline bool is_FH() const
{  //     PRB
	if (flags & EMDATA_FH) {
		return true;
	}
	else {
		return false;
	}
}

		
/** Is this a complex image?
 * @return Whether this is a complex image or not.
 */
inline bool is_complex() const
{
	if(attr_dict.has_key("is_complex")) {
		if (int(attr_dict["is_complex"])) {
			return true;
		}
		else {
			return false;
		}
	}
	else {
		return false;
	}
}


/** Is this a real image?
 * @return Whether this is image is real (not complex) or not.
 */
inline bool is_real() const
{
	return !is_complex();
}


/** Mark this image as a shuffled image.
 * @param is_shuffled If true, a shuffled image. If false, not 
 *          a shuffled image.
 */
inline void set_shuffled(bool is_shuffled)
{ // PRB
	if (is_shuffled) {
//		printf("entered correct part of set_shuffled \n");
		flags |=  EMDATA_SHUFFLE;
	}
	else {
		flags &= ~EMDATA_SHUFFLE;
	}
}


/** Mark this complex image as a FH image.
 * @param is_FH If true, a FH image. If false, 
 *        not a FH image.
 */
inline void set_FH(bool is_FH)
{ // PRB
	if (is_FH) {
		flags |=  EMDATA_FH;
	}
	else {
		flags &= ~EMDATA_FH;
	}
}


/** Mark this image as a complex image.
 * @param is_complex If true, a complex image. If false, a real
 * image.
 */
inline void set_complex(bool is_complex)
{
	if (is_complex) {
		set_attr("is_complex", int(1));
	}
	else {
		set_attr("is_complex", int(0));
	}
}


/** Is this image a 1D FFT image in X direction?
 * @return Whether this image is a 1D FFT image in X
 * direction.
 */
inline bool is_complex_x() const
{
	if(attr_dict.has_key("is_complex_x")) {
		if (int(attr_dict["is_complex_x"])) {
			return true;
		}
		else {
			return false;
		}
	}
	else {
		return false;
	}
}


/** Marks this image a 1D FFT image in X direction.
 * @param is_complex_x If true, a 1D FFT image in X direction;
 * If false, not such an image.
 */;
inline void set_complex_x(bool is_complex_x)
{
	if (is_complex_x) {
		set_attr("is_complex_x", int(1));
	}
	else {
		set_attr("is_complex_x", int(0));
	}
}


/** Is this image flipped?
 * @return Whether this image is flipped or not.
 */
inline bool is_flipped() const
{
	if (flags & EMDATA_FLIP) {
		return true;
	}
	else {
		return false;
	}
}


/** Mark this image as flipped.
 * @param is_flipped If true, mark this image as flipped;
 * If false, mark this image as not flipped.
 */
inline void set_flipped(bool is_flipped)
{
	if (is_flipped) {
		flags |= EMDATA_FLIP;
	}
	else {
		flags &= ~EMDATA_FLIP;
	}
}


/** Is this image a real/imaginary format complex image?
 * @return Whether this image is real/imaginary format complex
 * image.
 */
inline bool is_ri() const
{
	if(attr_dict.has_key("is_complex_ri")) {
		if (int(attr_dict["is_complex_ri"])) {
			return true;	
		}
		else {
			return false;
		}
	}
	else {
		return false;
	}
}


/** Mark this image as a real/imaginary format complex image.
 * @param is_ri If true, mark as real/imaginary format; If
 * false, mark as amp/phase format.
 */
inline void set_ri(bool is_ri)
{
	if (is_ri) {
		set_attr("is_complex_ri", int(1));
	}
	else {
		set_attr("is_complex_ri", int(0));
	}
}


/** Is this image already extended along x for ffts?
 * @return Whether this image is extended along x for ffts.
 */
inline bool is_fftpadded() const
{
	if (flags & EMDATA_PAD) {
		return true;	
	}
	else {
		return false;
	}
}


/** Mark this image as already extended along x for ffts.
 * @param is_fftpadded If true, mark as padded along x; If
 * false, mark as not padded along x.
 */
inline void set_fftpad(bool is_fftpadded)
{
	if (is_fftpadded) {
		flags |= EMDATA_PAD;
		set_attr("is_fftpad", int(1));
	}
	else {
		flags &= ~EMDATA_PAD;
		set_attr("is_fftpad", int(0));
	}
}


/** Does this image correspond to a (real-space) odd nx?
 * @return Whether this image has a (real-space) odd nx.
 */
inline bool is_fftodd() const
{
	if (flags & EMDATA_FFTODD) {
		return true;	
	}
	else {
		return false;
	}
}


/** Mark this image as having (real-space) odd nx.
 * @param is_fftodd If true, mark as nx odd; If
 * false, mark as nx not odd.
 */
inline void set_fftodd(bool is_fftodd)
{
	if (is_fftodd) {
		flags |= EMDATA_FFTODD;
		set_attr("is_fftodd", int(1));
	}
	else {
		flags &= ~EMDATA_FFTODD;
		set_attr("is_fftodd", int(0));
	}
}


/** Set the number of complex elements along x.
 * @param nxc is the number of complex elements along x.
 */
inline void set_nxc(int nxc)
{
	attr_dict["nxc"] = nxc;
}

/******************************************************************************
 ** These functions are used for EMData's pickling, do not use it for         *
 *  other purpose, e.g. get flags of a EMData object                          *
 * ***************************************************************************/
inline int get_flags() const
{
	return flags;
}

inline void set_flags(int f)
{
	flags = f;
}

inline int get_changecount() const
{
	return changecount;
}

inline void set_changecount(int c)
{
	changecount = c;
}

inline int get_xoff() const
{
	return xoff;
}

inline int get_yoff() const
{
	return yoff;
}

inline int get_zoff() const
{
	return zoff;
}

inline void set_xyzoff(int x, int y, int z)
{
	xoff = x;
	yoff = y;
	zoff = z;
}

inline string get_path() const
{
	return path;
}

inline int get_pathnum() const
{
	return pathnum;
}

//vector<float> get_data_pickle() const;
std::string get_data_pickle() const;

//void set_data_pickle(const vector<float>& vf);
void set_data_pickle(std::string vf);

//we don't actually pickle supp, just a place holder to set supp to NULL
int get_supp_pickle() const;

void set_supp_pickle(int i);


/*****************************************************************************/

#endif	//emdata__metadata_h__
