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
 
#include "cmp.h"
#include "emdata.h"
#include "ctf.h"

using namespace EMAN;

template <> Factory < Cmp >::Factory()
{
	force_add(&CccCmp::NEW);
	force_add(&SqEuclideanCmp::NEW);
	force_add(&DotCmp::NEW);
	force_add(&QuadMinDotCmp::NEW);
	force_add(&OptVarianceCmp::NEW);
	force_add(&PhaseCmp::NEW);
	force_add(&FRCCmp::NEW);
}

void Cmp::validate_input_args(const EMData * image, const EMData *with) const
{
	if (!image) {
		throw NullPointerException("compared image");
	}
	if (!with) {
		throw NullPointerException("compare-with image");
	}
	
	if (!EMUtil::is_same_size(image, with)) {
		throw ImageFormatException( "images not same size");
	}

	float *d1 = image->get_data();
	if (!d1) {
		throw NullPointerException("image contains no data");
	}
	
	float *d2 = with->get_data();
	if (!d2) {
		throw NullPointerException("compare-with image data");
	}
}

//  It would be good to add code for complex images!  PAP
float CccCmp::cmp(EMData * image, EMData *with) const
{
	ENTERFUNC;
	if (image->is_complex() || with->is_complex())
		throw ImageFormatException( "Complex images not supported by CMP::CccCmp");
	validate_input_args(image, with);

	float *d1 = image->get_data();
	float *d2 = with->get_data();

	float negative = (float)params.set_default("negative", 1);
	if (negative) negative=-1.0; else negative=1.0;

	double avg1 = 0.0, var1 = 0.0, avg2 = 0.0, var2 = 0.0, ccc = 0.0;
	long n = 0;
	long totsize = image->get_xsize()*image->get_ysize()*image->get_zsize();
	if (params.has_key("mask")) {
		EMData* mask;
		mask = params["mask"];
		float* dm = mask->get_data();
		for (long i = 0; i < totsize; i++) {
			if (dm[i] > 0.5) {
				avg1 += double(d1[i]);
				var1 += d1[i]*double(d1[i]);
				avg2 += double(d2[i]);
				var2 += d2[i]*double(d2[i]);
				ccc += d1[i]*double(d2[i]);
				n++;
			}
		}
	} else {
		for (long i = 0; i < totsize; i++) {
			avg1 += double(d1[i]);
			var1 += d1[i]*double(d1[i]);
			avg2 += double(d2[i]);
			var2 += d2[i]*double(d2[i]);
			ccc += d1[i]*double(d2[i]);
		}
		n = totsize;
	}

	avg1 /= double(n);
	var1 = var1/double(n) - avg1*avg1;
	avg2 /= double(n);
	var2 = var2/double(n) - avg2*avg2;
	ccc = ccc/double(n) - avg1*avg2;
	ccc /= sqrt(var1*var2);
	ccc *= negative;
	return static_cast<float>(ccc);
	EXITFUNC;
}



float SqEuclideanCmp::cmp(EMData * image, EMData *with) const
{
	ENTERFUNC;
	validate_input_args(image, with);

	float *y_data = with->get_data();
	float *x_data = image->get_data();
	double result = 0.;
	float n = 0;
	if(image->is_complex() && with->is_complex()) {
	// Implemented by PAP  01/09/06 - please do not change.  If in doubts, write/call me.
		int nx  = with->get_xsize();
		int ny  = with->get_ysize();
		int nz  = with->get_zsize();
		nx = (nx - 2 + with->is_fftodd()); // nx is the real-space size of the input image
		int lsd2 = (nx + 2 - nx%2) ; // Extended x-dimension of the complex image

		int ixb = 2*((nx+1)%2);
		int iyb = ny%2;
		// 
		if(nz == 1) {
		//  it looks like it could work in 3D, but it is not, really.
		for ( int iz = 0; iz <= nz-1; iz++) {
			double part = 0.;
			for ( int iy = 0; iy <= ny-1; iy++) {
				for ( int ix = 2; ix <= lsd2 - 1 - ixb; ix++) {
						int ii = ix + (iy  + iz * ny)* lsd2;
						part += (x_data[ii] - y_data[ii])*double(x_data[ii] - y_data[ii]);
				}
			}
			for ( int iy = 1; iy <= ny/2-1 + iyb; iy++) {
				int ii = (iy  + iz * ny)* lsd2;
				part += (x_data[ii] - y_data[ii])*double(x_data[ii] - y_data[ii]);
				part += (x_data[ii+1] - y_data[ii+1])*double(x_data[ii+1] - y_data[ii+1]);
			}
			if(nx%2 == 0) {
				for ( int iy = 1; iy <= ny/2-1 + iyb; iy++) {
					int ii = lsd2 - 2 + (iy  + iz * ny)* lsd2;
					part += (x_data[ii] - y_data[ii])*double(x_data[ii] - y_data[ii]);
					part += (x_data[ii+1] - y_data[ii+1])*double(x_data[ii+1] - y_data[ii+1]);
				}
			
			}
			part *= 2;
			part += (x_data[0] - y_data[0])*double(x_data[0] - y_data[0]);
			if(ny%2 == 0) {
				int ii = (ny/2  + iz * ny)* lsd2;
				part += (x_data[ii] - y_data[ii])*double(x_data[ii] - y_data[ii]);				
			}
			if(nx%2 == 0) {
				int ii = lsd2 - 2 + (0  + iz * ny)* lsd2;
				part += (x_data[ii] - y_data[ii])*double(x_data[ii] - y_data[ii]);				
				if(ny%2 == 0) {
					int ii = lsd2 - 2 +(ny/2  + iz * ny)* lsd2;
					part += (x_data[ii] - y_data[ii])*double(x_data[ii] - y_data[ii]);				
				}
			}
			result += part;
		}
		n = (float)nx*(float)ny*(float)nz*(float)nx*(float)ny*(float)nz;
		
		}else{ //This 3D code is incorrect, but it is the best I can do now 01/09/06 PAP
		int ky, kz;
		int ny2 = ny/2; int nz2 = nz/2;
		for ( int iz = 0; iz <= nz-1; iz++) {
			if(iz>nz2) kz=iz-nz; else kz=iz;
			for ( int iy = 0; iy <= ny-1; iy++) {
				if(iy>ny2) ky=iy-ny; else ky=iy;
				for ( int ix = 0; ix <= lsd2-1; ix++) {
				// Skip Friedel related values
				if(ix>0 || (kz>=0 && (ky>=0 || kz!=0))) {
						int ii = ix + (iy  + iz * ny)* lsd2;
						result += (x_data[ii] - y_data[ii])*double(x_data[ii] - y_data[ii]);
					}
				}
			}
		}
		n = ((float)nx*(float)ny*(float)nz*(float)nx*(float)ny*(float)nz)/2.0f;
		}
	} else {
		long totsize = image->get_xsize()*image->get_ysize()*image->get_zsize();
		if (params.has_key("mask")) {
		  EMData* mask;
		  mask = params["mask"];
  		  float* dm = mask->get_data();
		  for (long i = 0; i < totsize; i++) {
			   if (dm[i] > 0.5) {
				double temp = x_data[i]- y_data[i];
				result += temp*temp;
				n++;
			   }
		  }
		} else {
		  for (long i = 0; i < totsize; i++) {
				double temp = x_data[i]- y_data[i];
				result += temp*temp;
		   }
		   n = (float)totsize;
		}
	}
	result/=n;
	
	EXITFUNC;
	return static_cast<float>(result);
}


// Even though this uses doubles, it might be wise to recode it row-wise
// to avoid numerical errors on large images
float DotCmp::cmp(EMData* image, EMData* with) const
{
	ENTERFUNC;
	validate_input_args(image, with);

	float *x_data = image->get_data();
	float *y_data = with->get_data();

	int normalize = params.set_default("normalize", 0);
	float negative = (float)params.set_default("negative", 1);

	if (negative) negative=-1.0; else negative=1.0;
	double result = 0.;
	long n = 0;
	if(image->is_complex() && with->is_complex()) {
	// Implemented by PAP  01/09/06 - please do not change.  If in doubts, write/call me.
		int nx  = with->get_xsize();
		int ny  = with->get_ysize();
		int nz  = with->get_zsize();
		nx = (nx - 2 + with->is_fftodd()); // nx is the real-space size of the input image
		int lsd2 = (nx + 2 - nx%2) ; // Extended x-dimension of the complex image

		int ixb = 2*((nx+1)%2);
		int iyb = ny%2;
		// 
		if(nz == 1) {
		//  it looks like it could work in 3D, but does not
		for ( int iz = 0; iz <= nz-1; iz++) {
			double part = 0.;
			for ( int iy = 0; iy <= ny-1; iy++) {
				for ( int ix = 2; ix <= lsd2 - 1 - ixb; ix++) {
					int ii = ix + (iy  + iz * ny)* lsd2;
					part += x_data[ii] * double(y_data[ii]);
				}
			}
			for ( int iy = 1; iy <= ny/2-1 + iyb; iy++) {
				int ii = (iy  + iz * ny)* lsd2;
				part += x_data[ii] * double(y_data[ii]);
				part += x_data[ii+1] * double(y_data[ii+1]);
			}
			if(nx%2 == 0) {
				for ( int iy = 1; iy <= ny/2-1 + iyb; iy++) {
					int ii = lsd2 - 2 + (iy  + iz * ny)* lsd2;
					part += x_data[ii] * double(y_data[ii]);
					part += x_data[ii+1] * double(y_data[ii+1]);
				}
			
			}
			part *= 2;
			part += x_data[0] * double(y_data[0]);
			if(ny%2 == 0) {
				int ii = (ny/2  + iz * ny)* lsd2;
				part += x_data[ii] * double(y_data[ii]);				
			}
			if(nx%2 == 0) {
				int ii = lsd2 - 2 + (0  + iz * ny)* lsd2;
				part += x_data[ii] * double(y_data[ii]);				
				if(ny%2 == 0) {
					int ii = lsd2 - 2 +(ny/2  + iz * ny)* lsd2;
					part += x_data[ii] * double(y_data[ii]);				
				}
			}
			result += part;
		}
		if( normalize ) {
		//  it looks like it could work in 3D, but does not
		double square_sum1 = 0., square_sum2 = 0.;
		for ( int iz = 0; iz <= nz-1; iz++) {
			for ( int iy = 0; iy <= ny-1; iy++) {
				for ( int ix = 2; ix <= lsd2 - 1 - ixb; ix++) {
					int ii = ix + (iy  + iz * ny)* lsd2;
					square_sum1 += x_data[ii] * double(x_data[ii]);
					square_sum2 += y_data[ii] * double(y_data[ii]);
				}
			}
			for ( int iy = 1; iy <= ny/2-1 + iyb; iy++) {
				int ii = (iy  + iz * ny)* lsd2;
				square_sum1 += x_data[ii] * double(x_data[ii]);
				square_sum1 += x_data[ii+1] * double(x_data[ii+1]);
				square_sum2 += y_data[ii] * double(y_data[ii]);
				square_sum2 += y_data[ii+1] * double(y_data[ii+1]);
			}
			if(nx%2 == 0) {
				for ( int iy = 1; iy <= ny/2-1 + iyb; iy++) {
					int ii = lsd2 - 2 + (iy  + iz * ny)* lsd2;
					square_sum1 += x_data[ii] * double(x_data[ii]);
					square_sum1 += x_data[ii+1] * double(x_data[ii+1]);
					square_sum2 += y_data[ii] * double(y_data[ii]);
					square_sum2 += y_data[ii+1] * double(y_data[ii+1]);
				}
			
			}
			square_sum1 *= 2;
			square_sum1 += x_data[0] * double(x_data[0]);
			square_sum2 *= 2;
			square_sum2 += y_data[0] * double(y_data[0]);
			if(ny%2 == 0) {
				int ii = (ny/2  + iz * ny)* lsd2;
				square_sum1 += x_data[ii] * double(x_data[ii]);				
				square_sum2 += y_data[ii] * double(y_data[ii]);				
			}
			if(nx%2 == 0) {
				int ii = lsd2 - 2 + (0  + iz * ny)* lsd2;
				square_sum1 += x_data[ii] * double(x_data[ii]);				
				square_sum2 += y_data[ii] * double(y_data[ii]);				
				if(ny%2 == 0) {
					int ii = lsd2 - 2 +(ny/2  + iz * ny)* lsd2;
					square_sum1 += x_data[ii] * double(x_data[ii]);				
					square_sum2 += y_data[ii] * double(y_data[ii]);				
				}
			}
		}
		result /= sqrt(square_sum1*square_sum2);
		} else  result /= ((float)nx*(float)ny*(float)nz*(float)nx*(float)ny*(float)nz);
		
		} else { //This 3D code is incorrect, but it is the best I can do now 01/09/06 PAP
		int ky, kz;
		int ny2 = ny/2; int nz2 = nz/2;
		for ( int iz = 0; iz <= nz-1; iz++) {
			if(iz>nz2) kz=iz-nz; else kz=iz;
			for ( int iy = 0; iy <= ny-1; iy++) {
				if(iy>ny2) ky=iy-ny; else ky=iy;
				for ( int ix = 0; ix <= lsd2-1; ix++) {
					// Skip Friedel related values
					if(ix>0 || (kz>=0 && (ky>=0 || kz!=0))) {
						int ii = ix + (iy  + iz * ny)* lsd2;
						result += x_data[ii] * double(y_data[ii]);
					}
				}
			}
		}
		if( normalize ) {
		//  still incorrect
		double square_sum1 = 0., square_sum2 = 0.;
		int ky, kz;
		int ny2 = ny/2; int nz2 = nz/2;
		for ( int iz = 0; iz <= nz-1; iz++) {
			if(iz>nz2) kz=iz-nz; else kz=iz;
			for ( int iy = 0; iy <= ny-1; iy++) {
				if(iy>ny2) ky=iy-ny; else ky=iy;
				for ( int ix = 0; ix <= lsd2-1; ix++) {
					// Skip Friedel related values
					if(ix>0 || (kz>=0 && (ky>=0 || kz!=0))) {
						int ii = ix + (iy  + iz * ny)* lsd2;
						square_sum1 += x_data[ii] * double(x_data[ii]);
						square_sum2 += y_data[ii] * double(y_data[ii]);
					}
				}
			}
		}
		result /= sqrt(square_sum1*square_sum2);
		} else result /= ((float)nx*(float)ny*(float)nz*(float)nx*(float)ny*(float)nz/2);
		}
	} else {
		long totsize = (long int)image->get_xsize() * (long int)image->get_ysize() * (long int)image->get_zsize();

		double square_sum1 = 0., square_sum2 = 0.;

		if (params.has_key("mask")) {
			EMData* mask;
			mask = params["mask"];
			float* dm = mask->get_data();
			if (normalize) {
				for (long i = 0; i < totsize; i++) {
					if (dm[i] > 0.5) {
						square_sum1 += x_data[i]*double(x_data[i]);
						square_sum2 += y_data[i]*double(y_data[i]);
						result += x_data[i]*double(y_data[i]);
					}
				}
			} else {
				for (long i = 0; i < totsize; i++) {
					if (dm[i] > 0.5) {
						result += x_data[i]*double(y_data[i]);
						n++;
					}
				}
			}
		} else {
			for (long i = 0; i < totsize; i++) {
				result += x_data[i]*double(y_data[i]);
			}
			if (normalize) {
				square_sum1 = image->get_attr("square_sum");
				square_sum2 = with->get_attr("square_sum");
			} else n = totsize;
		}
		if (normalize) result /= (sqrt(square_sum1*square_sum2)); else result /= n;
	}
	
			
	EXITFUNC;
	return (float) (negative*result);
}

// Even though this uses doubles, it might be wise to recode it row-wise
// to avoid numerical errors on large images
float QuadMinDotCmp::cmp(EMData * image, EMData *with) const
{
	ENTERFUNC;
	validate_input_args(image, with);

	if (image->get_zsize()!=1) throw InvalidValueException(0, "QuadMinDotCmp supports 2D only");
	
	int nx=image->get_xsize();
	int ny=image->get_ysize();

	int normalize = params.set_default("normalize", 0);
	float negative = (float)params.set_default("negative", 1);
	
	if (negative) negative=-1.0; else negative=1.0;

	double result[4] = { 0,0,0,0 }, sq1[4] = { 0,0,0,0 }, sq2[4] = { 0,0,0,0 } ;

	vector<int> image_saved_offsets = image->get_array_offsets();
	vector<int> with_saved_offsets = with->get_array_offsets();
	image->set_array_offsets(-nx/2,-ny/2);
	with->set_array_offsets(-nx/2,-ny/2);
	int i,x,y;
	for (y=-ny/2; y<ny/2; y++) {
		for (x=-nx/2; x<nx/2; x++) {
			int quad=(x<0?0:1) + (y<0?0:2);
			result[quad]+=(*image)(x,y)*(*with)(x,y);
			if (normalize) {
				sq1[quad]+=(*image)(x,y)*(*image)(x,y);
				sq2[quad]+=(*with)(x,y)*(*with)(x,y);
			}
		}
	}
	image->set_array_offsets(image_saved_offsets);
	with->set_array_offsets(with_saved_offsets);
	
	if (normalize) {
		for (i=0; i<4; i++) result[i]/=sqrt(sq1[i]*sq2[i]);
	} else {
		for (i=0; i<4; i++) result[i]/=nx*ny/4;
	}
	
	float worst=static_cast<float>(result[0]);
	for (i=1; i<4; i++) if (static_cast<float>(result[i])<worst) worst=static_cast<float>(result[i]);
	
	EXITFUNC;
	return (float) (negative*worst);
}

float OptVarianceCmp::cmp(EMData * image, EMData *with) const
{
	ENTERFUNC;
	validate_input_args(image, with);

	int keepzero = params.set_default("keepzero", 1);
	int invert = params.set_default("invert",0);
	int matchfilt = params.set_default("matchfilt",1);
	int matchamp = params.set_default("matchamp",0);
	int radweight = params.set_default("radweight",0);
	int dbug = params.set_default("debug",0);
	
	size_t size = image->get_xsize() * image->get_ysize() * image->get_zsize();
	
	
	EMData *with2=NULL;
	if (matchfilt) {
		EMData *a = image->do_fft();
		EMData *b = with->do_fft();
		
		vector <float> rfa=a->calc_radial_dist(a->get_ysize()/2,0.0f,1.0f,1);
		vector <float> rfb=b->calc_radial_dist(b->get_ysize()/2,0.0f,1.0f,1);
		
		for (size_t i=0; i<a->get_ysize()/2.0f; i++) rfa[i]/=(rfb[i]==0?1.0f:rfb[i]);
		
		b->apply_radial_func(0.0f,1.0f/a->get_ysize(),rfa);
		with2=b->do_ift();

		delete a;
		delete b;	
		if (dbug) with2->write_image("a.hdf",-1);

//		with2->process_inplace("matchfilt",Dict("to",this));
//		x_data = with2->get_data();
	}

	// This applies the individual Fourier amplitudes from 'image' and 
	// applies them to 'with'
	if (matchamp) {
		EMData *a = image->do_fft();
		EMData *b = with->do_fft();
		size_t size2 = a->get_xsize() * a->get_ysize() * a->get_zsize();
		
		a->ri2ap();
		b->ri2ap();
		
		float *ad=a->get_data();
		float *bd=b->get_data();
		
		for (size_t i=0; i<size2; i+=2) bd[i]=ad[i];
		b->update();
	
		b->ap2ri();
		with2=b->do_ift();
//with2->write_image("a.hdf",-1);
		delete a;
		delete b;
	}
	
	float *x_data;
	if (with2) x_data=with2->get_data();
	else x_data = with->get_data();
	float *y_data = image->get_data();
	
	size_t nx = image->get_xsize();
	float m = 0;
	float b = 0;
	
	// This will write the x vs y file used to calculate the density
	// optimization. This behavior may change in the future
	if (dbug) {
		FILE *out=fopen("dbug.optvar.txt","w");
		if (out) {
			for (size_t i=0; i<size; i++) {
				if ( !keepzero || (x_data[i] && y_data[i])) fprintf(out,"%g\t%g\n",x_data[i],y_data[i]);
			}
			fclose(out);
		}
	}


	Util::calc_least_square_fit(size, x_data, y_data, &m, &b, keepzero);
	if (m == 0) {
		m = FLT_MIN;
	}
	b = -b / m;
	m = 1.0f / m;

	// While negative slopes are really not a valid comparison in most cases, we
	// still want to detect these instances, so this if is removed
/*	if (m < 0) {
		b = 0;
		m = 1000.0;
	}*/

	double  result = 0;
	int count = 0;

	if (radweight) {
		if (image->get_zsize()!=1) throw ImageDimensionException("radweight option is 2D only");
		if (keepzero) {
			for (size_t i = 0,y=0; i < size; y++) {
				for (size_t x=0; x<nx; i++,x++) {
					if (y_data[i] && x_data[i]) {
#ifdef	_WIN32
						if (invert) result += Util::square(x_data[i] - (y_data[i]-b)/m)*(_hypot((float)x,(float)y)+nx/4.0);
						else result += Util::square((x_data[i] * m) + b - y_data[i])*(_hypot((float)x,(float)y)+nx/4.0);
#else
						if (invert) result += Util::square(x_data[i] - (y_data[i]-b)/m)*(hypot((float)x,(float)y)+nx/4.0);
						else result += Util::square((x_data[i] * m) + b - y_data[i])*(hypot((float)x,(float)y)+nx/4.0);
#endif
						count++;
					}
				}
			}
			result/=count;
		}
		else {
			for (size_t i = 0,y=0; i < size; y++) {
				for (size_t x=0; x<nx; i++,x++) {
#ifdef	_WIN32
					if (invert) result += Util::square(x_data[i] - (y_data[i]-b)/m)*(_hypot((float)x,(float)y)+nx/4.0);
					else result += Util::square((x_data[i] * m) + b - y_data[i])*(_hypot((float)x,(float)y)+nx/4.0);
#else
					if (invert) result += Util::square(x_data[i] - (y_data[i]-b)/m)*(hypot((float)x,(float)y)+nx/4.0);
					else result += Util::square((x_data[i] * m) + b - y_data[i])*(hypot((float)x,(float)y)+nx/4.0);
#endif
				}
			}
			result = result / size;
		}
	}
	else {
		if (keepzero) {
			for (size_t i = 0; i < size; i++) {
				if (y_data[i] && x_data[i]) {
					if (invert) result += Util::square(x_data[i] - (y_data[i]-b)/m);
					else result += Util::square((x_data[i] * m) + b - y_data[i]);
					count++;
				}
			}
			result/=count;
		}
		else {
			for (size_t i = 0; i < size; i++) {
				if (invert) result += Util::square(x_data[i] - (y_data[i]-b)/m);
				else result += Util::square((x_data[i] * m) + b - y_data[i]);
			}
			result = result / size;
		}
	}
	scale = m;
	shift = b;
	
	image->set_attr("ovcmp_m",m);
	image->set_attr("ovcmp_b",b);
	if (with2) delete with2;
	EXITFUNC;
	
#if 0
	return (1 - result);
#endif
	
	return static_cast<float>(result);
}

float PhaseCmp::cmp(EMData * image, EMData *with) const
{
	ENTERFUNC;
	validate_input_args(image, with);

	static float *dfsnr = 0;
	static int nsnr = 0;

// 	if (image->get_zsize() > 1) {
// 		throw ImageDimensionException("2D only");
// 	}

	int nx = image->get_xsize();
	int ny = image->get_ysize();
	int nz = image->get_zsize();

	int np = (int) ceil(Ctf::CTFOS * sqrt(2.0f) * ny / 2) + 2;

	if (nsnr != np) {
		nsnr = np;
		dfsnr = (float *) realloc(dfsnr, np * sizeof(float));

		//float w = Util::square(nx / 8.0f); // <- Not used currently

		for (int i = 0; i < np; i++) {
//			float x2 = Util::square(i / (float) Ctf::CTFOS);
//			dfsnr[i] = (1.0f - exp(-x2 / 4.0f)) * exp(-x2 / w);
			float x2 = 10.0f*i/np;
			dfsnr[i] = x2 * exp(-x2);
		}

//		Util::save_data(0, 1.0f / Ctf::CTFOS, dfsnr, np, "filt.txt");
	}

	EMData *image_fft = image->do_fft();
	image_fft->ri2ap();
	EMData *with_fft = with->do_fft();
	with_fft->ri2ap();

	float *image_fft_data = image_fft->get_data();
	float *with_fft_data = with_fft->get_data();
	double sum = 0;
	double norm = FLT_MIN;
	int i = 0;

	for (float z = 0; z < nz; ++z){
		for (float y = 0; y < ny; y++) {
			for (int x = 0; x < nx + 2; x += 2) {
				int r;
#ifdef	_WIN32
				if (y<ny/2) r = Util::round(_hypot(x / 2, y) * Ctf::CTFOS);
				else r = Util::round(_hypot(x / 2, y-ny) * Ctf::CTFOS);
#else
				if (y<ny/2) r = Util::round(hypot(x / 2, y) * Ctf::CTFOS);
				else r = Util::round(hypot(x / 2, y-ny) * Ctf::CTFOS);
#endif
				float a = dfsnr[r] * with_fft_data[i];
// 				cout << a << " " << Util::angle_sub_2pi(image_fft_data[i + 1], with_fft_data[i + 1]) << " " <<image_fft_data[i + 1] << " " << with_fft_data[i + 1] << endl;
				sum += Util::angle_sub_2pi(image_fft_data[i + 1], with_fft_data[i + 1]) * a;
				norm += a;
				i += 2;
			}
		}
	}
	EXITFUNC;
	
	if( image_fft )
	{
		delete image_fft;
		image_fft = 0;
	}
	if( with_fft )
	{
		delete with_fft;
		with_fft = 0;
	}
#if 0
	return (1.0f - sum / norm);
#endif
	return (float)(sum / norm);
}


float FRCCmp::cmp(EMData * image, EMData * with) const
{
	ENTERFUNC;
	validate_input_args(image, with);

	if (!image->is_complex()) { image=image->do_fft(); image->set_attr("free_me",1); }
	if (!with->is_complex()) { with=with->do_fft(); with->set_attr("free_me",1); }
	
	int snrweight = params.set_default("snrweight", 0);
	int ampweight = params.set_default("ampweight", 1);
	int sweight = params.set_default("sweight", 1);
	int nweight = params.set_default("nweight", 0);

	static vector < float >default_snr;

// 	if (image->get_zsize() > 1) {
// 		throw ImageDimensionException("2D only");
// 	}

	//int nx = image->get_xsize(); // <- not currently used
	int ny = image->get_ysize();

	vector < float >fsc;

	fsc = image->calc_fourier_shell_correlation(with,1);

	vector<float> snr;
	if (snrweight) {
		if (!image->has_attr("ctf")) throw InvalidCallException("SNR weight with no CTF parameters");
		Ctf *ctf=image->get_attr("ctf");
		float ds=1.0/(ctf->apix*ny);
		snr=ctf->compute_1d(ny/2,ds,Ctf::CTF_SNR);
	}
	
	vector<float> amp;
	if (ampweight) amp=image->calc_radial_dist(ny/2,0,1,0);

	double sum=0.0, norm=0.0;
	
	for (int i=0; i<ny/2; i++) {
		double weight=1.0;
		if (sweight) weight*=fsc[(ny/2+1)*2+i];
		if (ampweight) weight*=amp[i];
		if (snrweight) weight*=snr[i];
		sum+=weight*fsc[ny/2+1+i];
		norm+=weight;
//		printf("%d\t%f\t%f\n",i,weight,fsc[ny/2+1+i]);
	}

	if (image->has_attr("free_me")) delete image;
	if (with->has_attr("free_me")) delete with;

	EXITFUNC;
	
	// This performs a weighting that tries to normalize FRC by correcting from the number of particles represented by the average
	sum/=norm;
	if (nweight && with->get_attr_default("ptcl_repr",0) && sum>=0 && sum<1.0) {
		sum=sum/(1.0-sum);							// convert to SNR
		sum/=(float)with->get_attr_default("ptcl_repr",0);	// divide by ptcl represented
		sum=sum/(1.0+sum);							// convert back to correlation
	}
	
	//.Note the negative! This is because EMAN2 follows the convention that
	// smaller return values from comparitors indicate higher similarity -
	// this enables comparitors to be used in a generic fashion.
	return (float)-sum;
}

void EMAN::dump_cmps()
{
	dump_factory < Cmp > ();
}

map<string, vector<string> > EMAN::dump_cmps_list()
{
	return dump_factory_list < Cmp > ();
}

/* vim: set ts=4 noet: */
