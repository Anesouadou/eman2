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

#ifndef emdata__core_h__
#define emdata__core_h__ 

public:
/** Make a copy of this image including both data and header.
 * @return A copy of this image including both data and header.
 */
EMData *copy() const;


/** Make an image with a copy of the current image's header.
 * @return An image with a copy of the current image's header.
 */
EMData *copy_head() const;
		

/** add a number to each pixel value of the image. Image may be real or complex.
 * @param f The number added to 'this' image.
 * @param keepzero If set will not modify pixels that are exactly zero
 */
void add(float f,int keepzero=0);

		
/** add a same-size image to this image pixel by pixel.
 *
 * @param image The image added to 'this' image.
 * @exception ImageFormatException If the 2 images are not same size.
 */
void add(const EMData & image);

		
/** subtract a number to each pixel value of the image.
 * @param f The number subtracted from 'this' image.		 
 */
void sub(float f);

		
/** subtract a same-size image from this image pixel by pixel.
 * @param image The image subtracted  from 'this' image.
 * @exception ImageFormatException If the 2 images are not same size.
 */
void sub(const EMData & image);


/** multiply a number to each pixel value of the image.
 * @param n The number multiplied to 'this' image.
 */
void mult(int n)
{
	mult((float)n);
}


/** multiply a number to each pixel value of the image.
 * @param f The number multiplied to 'this' image.
 */
void mult(float f);

		
/** multiply each pixel of this image with each pixel of some
 * other same-size image.
 *
 * @param image The image multiplied to 'this' image.
 * @param prevent_complex_multiplication if the image is complex, this flag will override complex multiplication and just multiply each pixel by the other
 * @exception ImageFormatException If the 2 images are not same size.
 */
void mult(const EMData & image, bool prevent_complex_multiplication=false);


/** make each pixel value divided by a number.
 * @param f The number 'this' image divided by.
 */
void div(float f);


/** make each pixel value divided by pixel value of another
 * same-size image.
 * @param image The image 'this' image divided by.
 * @exception ImageFormatException If the 2 images are not same size.
 */
void div(const EMData & image);


/** Make all the pixel value = 0. */
void to_zero();

		
/** Make all the pixel value = 1. */
void to_one();


/** Dot product 2 images. The 2 images must be of same size.
 * If 'evenonly' is true, only calculates pixels with even
 * positions assuming all pixels are in a single array. If
 * 'evenonly' is false, calculates all pixels. Shortcut for
 * cmp("dot")
 *
 * @param with The image to do dot product with.
 * @exception NullPointerException if with is a NULL image.
 * @return The dot product result.
 */
float dot(EMData * with);


/** Get one row of a 1D/2D image.
 *
 * @param row_index Index of the row.
 * @exception ImageDimensionException If this image is 3D.
 * @return A 1D image with the row data.
 */
EMData *get_row(int row_index) const;


/** Set one row of a 1D/2D image.
 *
 * @param data The row image data.
 * @param row_index Index of the row.
 * @exception ImageDimensionException If this image is 3D.
 */
void set_row(const EMData * data, int row_index);


/** Get one column of a 2D images.
 *
 * @param col_index Index of the column.
 * @exception ImageDimensionException If this image is not 2D.
 * @return A 1D image with the column data.
 */
EMData *get_col(int col_index) const;


/** Set one column of a 2D image.
 *
 * @param data The column image data.
 * @param col_index Index of the column.
 * @exception ImageDimensionException If this image is not 2D.
 */
void set_col(const EMData * data, int col_index);


/** Get the pixel density value at coordinates (x,y,z).
 * The validity of x, y, and z is not checked.
 *
 * @param x The x cooridinate.
 * @param y The y cooridinate.
 * @param z The z cooridinate.
 * @return The pixel density value at coordinates (x,y,z).
 */
inline float get_value_at(int x, int y, int z) const
{
	return rdata[x + y * nx + z * nxy];
}

		
/** Get the pixel density value at coordinates (x,y). 2D only.
 * The validity of x, y is not checked.
 *
 * @param x The x cooridinate.
 * @param y The y cooridinate.
 * @return The pixel density value at coordinates (x,y).
 */
inline float get_value_at(int x, int y) const
{
	return rdata[x + y * nx];
}


/** Get the pixel density value given an index 'i' assuming
 * the pixles are stored in a 1D array. The validity of i
 * is not checked.
 * 
 * @param i  1D data array index.
 * @return The pixel density value
 */
inline float get_value_at(size_t i) const
{
	return rdata[i];
}


/** Get the pixel density value at coordinates (x,y,z).
 * Should only be called on 3D images - no errors are thrown
 * Wraps pixel values if they are negative - i.e. is circulant
 * For example, if x = -1, then the pixel at nx-1  is returned
 * @param x The x cooridinate.
 * @param y The y cooridinate.
 * @param z The z cooridinate.
 * @return The pixel density value at circulant coordinates (x,y,z).
 */
float get_value_at_wrap(int x, int y, int z) const;
float& get_value_at_wrap(int x, int y, int z);
		
/** Get the pixel density value at coordinates (x,y).
 * Should only be called on 2D images - no errors are thrown
 * Wraps pixel values if they are negative - i.e. is circulant
 * For example, if x = -1, then the pixel at nx-1  is returned
 * @param x The x cooridinate.
 * @param y The y cooridinate.
 * @return The pixel density value at circulant coordinates (x,y).
 */
float get_value_at_wrap(int x, int y) const;
float& get_value_at_wrap(int x, int y);

/** Get the pixel density value at coordinates (x,y).
 * Should only be called on 1D images - no errors are thrown
 * Wraps pixel values if they are negative - i.e. is circulant
 * For example, if x = -1, then the pixel at nx-1  is returned
 * @param x The x cooridinate.
 * @return The pixel density value at circulant coordinates (x).
 */
float get_value_at_wrap(int x) const;
float& get_value_at_wrap(int x);

/** A safer, slower way to get the pixel density value at
 * coordinates (x,y,z). The validity of x, y, and z is checked.
 * If the coordinates are out of range, return 0;
 *
 * @param x The x cooridinate.
 * @param y The y cooridinate.
 * @param z The z cooridinate.
 * @return The pixel density value at coordinates (x,y,z).
 */
float sget_value_at(int x, int y, int z) const;


/** A safer, slower way to get the pixel density value at
 * coordinates (x,y). 2D only. The validity of x, y is checked.
 * If the coordinates are out of range, return 0;
 *
 * @param x The x cooridinate.
 * @param y The y cooridinate.
 * @return The pixel density value at coordinates (x,y).
 */
float sget_value_at(int x, int y) const;


/** A safer, slower way to get the pixel density value
 * given an index 'i' assuming
 * the pixles are stored in a 1D array. The validity of i
 * is checked. If i is out of range, return 0;
 * 
 * @param i  1D data array index.
 * @return The pixel density value
 */
float sget_value_at(size_t i) const;


/** Get pixel density value at interpolation of (x,y).
 * The validity of x, y is checked.2D image only. 
 *
 * @param x The x cooridinate.
 * @param y The y cooridinate.
 * @return The pixel density value at coordinates (x,y).
 */
float sget_value_at_interp(float x, float y) const;


/** Get the pixel density value at interpolation of (x,y,z).
 * The validity of x, y, and z is checked.
 *
 * @param x The x cooridinate.
 * @param y The y cooridinate.
 * @param z The z cooridinate.
 * @return The pixel density value at coordinates (x,y,z).
 */
float sget_value_at_interp(float x, float y, float z) const;


/** Set the pixel density value at coordinates (x,y,z).
 * The validity of x, y, and z is not checked.
 * This implementation does bounds checking.
 * 
 * @param x The x cooridinate.
 * @param y The y cooridinate.
 * @param z The z cooridinate.
 * @param v The pixel density value at coordinates (x,y,z).
 * @exception OutofRangeException wehn index out of image data's range.
 */
inline void set_value_at(int x, int y, int z, float v)
{
	if( x>=nx || x<0 )
	{
		throw OutofRangeException(0, nx-1, x, "x dimension index");
	}
	else if( y>=ny || y<0 )
	{
		throw OutofRangeException(0, ny-1, y, "y dimension index");
	}
	else if( z>=nz || z<0 )
	{
		throw OutofRangeException(0, nz-1, z, "z dimension index");
	}
	else
	{
		rdata[x + y * nx + z * nxy] = v;
		flags |= EMDATA_NEEDUPD;
		changecount++;
	}
}

	
/** Set the pixel density value at coordinates (x,y,z).
 * The validity of x, y, and z is not checked.
 * This implementation has no bounds checking.
 * 
 * @param x The x cooridinate.
 * @param y The y cooridinate.
 * @param z The z cooridinate.
 * @param v The pixel density value at coordinates (x,y,z).
 */
inline void set_value_at_fast(int x, int y, int z, float v)
{
	rdata[x + y * nx + z * nxy] = v;
	flags |= EMDATA_NEEDUPD;
	changecount++;
}

		
/** Set the pixel density value at coordinates (x,y).
 * 2D image only. The validity of x, y, and z is not checked.
 *
 * @param x The x cooridinate.
 * @param y The y cooridinate.
 * @param v The pixel density value at coordinates (x,y).
 * @exception OutofRangeException wehn index out of image data's range.
 */
inline void set_value_at(int x, int y, float v)
{
	if( x>=nx || x<0 )
	{
		throw OutofRangeException(0, nx-1, x, "x dimension index");
	}
	else if( y>=ny || y<0 )
	{
		throw OutofRangeException(0, ny-1, y, "y dimension index");
	}
	else
	{
		rdata[x + y * nx] = v;
		flags |= EMDATA_NEEDUPD;
		changecount++;
	}
}

		
/** Set the pixel density value at coordinates (x,y).
 * 2D image only. The validity of x, y, and z is not checked.
 *
 * @param x The x cooridinate.
 * @param y The y cooridinate.
 * @param v The pixel density value at coordinates (x,y).
 */
inline void set_value_at_fast(int x, int y, float v)
{
	rdata[x + y * nx] = v;
	flags |= EMDATA_NEEDUPD;
	changecount++;
}


/** Set the pixel density value at coordinate (x).
 * 1D image only. 
 *
 * @param x The x cooridinate.
 * @param v The pixel density value at coordinate (x).
 * @exception OutofRangeException wehn index out of image data's range.
 */
inline void set_value_at(int x, float v)
{
	if( x>=nx || x<0 )
	{
		throw OutofRangeException(0, nx-1, x, "x dimension index");
	}
	else
	{
		rdata[x] = v;
		flags |= EMDATA_NEEDUPD;
		changecount++;
	}
}

/** Set the pixel density value at coordinate (x).
 * 1D image only. 
 *
 * @param x The x cooridinate.
 * @param v The pixel density value at coordinate (x).
 */
inline void set_value_at_fast(int x, float v)
{
	rdata[x] = v;
	flags |= EMDATA_NEEDUPD;
	changecount++;
}


/** Free memory associated with this EMData
 * Called in destructor and in assignment operator
 */
void free_memory();

EMData & operator+=(float n);
EMData & operator-=(float n);
EMData & operator*=(float n);
EMData & operator/=(float n);

EMData & operator+=(const EMData & em);
EMData & operator-=(const EMData & em);
EMData & operator*=(const EMData & em);
EMData & operator/=(const EMData & em);


/** Overload operator() for array indexing. */
inline float& operator()(const int ix, const int iy, const int iz) const {
	ptrdiff_t pos = (ix-xoff) + ((iy-yoff) + (iz-zoff)*ny)*nx;
#ifdef BOUNDS_CHECKING
	if (pos < 0 || pos >= nx*ny*nz) {
		throw OutofRangeException(0, nx*ny*nz-1, pos, "EMData");
	}
#endif // BOUNDS_CHECKING
	return *(rdata + pos);
}

inline float& operator()(const int ix, const int iy) const {
	ptrdiff_t pos = (ix - xoff) + (iy-yoff)*nx;
#ifdef BOUNDS_CHECKING
	if (pos < 0 || pos >= nx*ny*nz)
	{
		throw OutofRangeException(0, nx*ny*nz-1, pos, "EMData");
	}
#endif // BOUNDS_CHECKING
	return *(rdata + pos);
}


inline float& operator()(const int ix) const {
	ptrdiff_t pos = ix - xoff;
#ifdef BOUNDS_CHECKING
	if (pos < 0 || pos >= nx*ny*nz)
		throw OutofRangeException(0, nx*ny*nz-1, pos, "EMData");
#endif // BOUNDS_CHECKING
	return *(rdata + pos);
}
		

/** Set the array offsets */
void set_array_offsets(const int xoff_=0, const int yoff_=0, 
		               const int zoff_=0) {
	xoff=xoff_; yoff=yoff_; zoff=zoff_;
}


void set_array_offsets(vector<int> offsets) {
	set_array_offsets(offsets[0],offsets[1],offsets[2]);
}


vector<int> get_array_offsets() {
	vector<int> offsets;
	offsets.push_back(xoff); 
	offsets.push_back(yoff); 
	offsets.push_back(zoff);
	return offsets;
}		


/** Return reference to complex elements */
std::complex<float>& cmplx(const int ix, const int iy, const int iz) {
	ptrdiff_t pos = 2*(ix-xoff)+((iy-yoff)+(iz-zoff)*ny)*nx;
#ifdef BOUNDS_CHECKING
	if (pos < 0 || pos >= nx*ny*nz)
		throw OutofRangeException(0, nx*ny*nz-1, pos, "EMData");
#endif // BOUNDS_CHECKING
	float* begin = rdata + pos;
	return *(reinterpret_cast<std::complex<float>* >(begin));
}


std::complex<float>& cmplx(const int ix, const int iy) {
	ptrdiff_t pos = 2*(ix-xoff)+(iy-yoff)*nx;
#ifdef BOUNDS_CHECKING
	if (pos < 0 || pos >= nx*ny*nz)
		throw OutofRangeException(0, nx*ny*nz-1, pos, "EMData");
#endif // BOUNDS_CHECKING
	float* begin = rdata + pos;
	return *(reinterpret_cast<std::complex<float>* >(begin));
}


std::complex<float>& cmplx(const int ix) {
	ptrdiff_t pos = 2*(ix-xoff);
#ifdef BOUNDS_CHECKING
	if (pos < 0 || pos >= nx*ny*nz)
		throw OutofRangeException(0, nx*ny*nz-1, pos, "EMData");
#endif // BOUNDS_CHECKING
	float* begin = rdata + pos;
	return *(reinterpret_cast<std::complex<float>* >(begin));
}


/** return a image to the power of n
 * @param n	the power of this simage
 * @return a image which is the nth power of this image
 * @exception InvalidValueException n must be >= 0
 */
EMData * power(int n) const;		

/**return square root of current image
 * @return a image which is the square root of this image
 * @exception ImageFormatException real image only
 * */
EMData * sqrt() const;

		
/** return natural logarithm image for a image 
 * @return a image which is the natural logarithm of this image
 * @exception InvalidValueException pixel value must be >= 0
 * @exception ImageFormatException real image only
 */
EMData * log() const;

		
/** return base 10 logarithm image for a image 
 * @return a image which is the base 10 logarithm of this image
 * @exception InvalidValueException pixel value must be >= 0
 * @exception ImageFormatException real image only
 */
EMData * log10() const;


/** return real part of a complex image as a real image format,
 * if this image is a real image, return a copy of this image.
 * @return a real image which is the real part of this image.
 */
EMData * real() const;

		
/** return imaginary part of a complex image as a real image format.
 * for a real image, just return itself.
 * @return a real image which is the imaginary part of this image.
 * @exception InvalidCallException if this image is a real image
 */
EMData * imag() const;

EMData * absi() const;


/** return amplitude part of a complex image as a real image format
 * @return EMData * a real image which is the amplitude part of this image
 * @exception InvalidCallException if this image is a real image or is in real/imaginary format
 * */
EMData * amplitude() const;


/** return phase part of a complex image as a real image format
 * @return EMData * a real image which is the phase part of this image
 * @exception InvalidCallException if this image is a real image or is in real/imaginary format
 * */
EMData * phase() const;

		
/** create a complex image from a real image, this complex image is in real/imaginary format
 * @param img give an artificial imaginary part
 * @return a complex image which is generated from a real image
 * @exception InvalidCallException this function can not be called by complex image 
 */
EMData * real2complex(float img = 0.0f) const;

#endif	//emdata__core_h__
