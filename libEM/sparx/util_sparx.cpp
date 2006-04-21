/**
 * $Id$
 */
#include <iostream>

#include "emdata.h"
#include "util.h"

#include <gsl/gsl_sf_bessel.h>
#include <gsl/gsl_sf_bessel.h>

using namespace EMAN;
using namespace std;

vector<float> Util::infomask(EMData* Vol, EMData* mask)
{
	ENTERFUNC;
	vector<float> stats;
	float *Volptr, *maskptr,MAX,MIN;
	long double Sum1,Sum2;	
	long count;
	
	MAX = FLT_MIN;
	MIN = FLT_MAX;
	count = 0L;
	Sum1 = 0.L;
	Sum2 = 0.L;
		
	
	if (mask == NULL)	
          {
	   //Vol->update_stat();	
	   stats.push_back(Vol->get_attr("mean"));
	   stats.push_back(Vol->get_attr("sigma"));
	   stats.push_back(Vol->get_attr("minimum"));
	   stats.push_back(Vol->get_attr("maximum"));
	   return stats;
	  }		
	
	/* Check if the sizes of the mask and image are same */
		
	size_t nx = Vol->get_xsize();
	size_t ny = Vol->get_ysize();
	size_t nz = Vol->get_zsize();		
	 
	Volptr = Vol->get_data();
	maskptr = mask->get_data();		 
	
	
	/* Calculation of the Statistics */
			       
	for (size_t i = 0;i < nx*ny*nz; i++)
	    {
	      if (maskptr[i]>0.5f)
	      {
	       Sum1 += Volptr[i];	       
	       Sum2 += Volptr[i]*Volptr[i];	       
	       MAX = (MAX < Volptr[i])?Volptr[i]:MAX;
	       MIN = (MIN > Volptr[i])?Volptr[i]:MIN;
	       count++;	       
	      }
	    }
	
       if (count==0) count++;
    
       float avg = static_cast<float>(Sum1/count);
       float sig2 = static_cast<float>(Sum2/count - avg*avg);
       float sig = sqrt(sig2);
                            
       stats.push_back(avg);
       stats.push_back(sig);
       stats.push_back(MIN);
       stats.push_back(MAX);

       return stats;
}
 
 
//---------------------------------------------------------------------------------------------------------- 
 
Dict Util::im_diff(EMData* V1, EMData* V2, EMData* mask)
{
	ENTERFUNC;
	
	size_t nx = V1->get_xsize();
	size_t ny = V1->get_ysize();
	size_t nz = V1->get_zsize();
	size_t size = nx*ny*nz;
	
	EMData *BD = new EMData();
 	BD->set_size(nx, ny, nz);
	
	float *params = new float[2];	 	 
  	
	float *V1ptr, *V2ptr, *MASKptr, *BDptr, A, B; 
	long double S1=0.L,S2=0.L,S3=0.L,S4=0.L;
	int nvox = 0L;
	
        V1ptr = V1->get_data();
	V2ptr = V2->get_data();
	MASKptr = mask->get_data();
	BDptr = BD->get_data();
	
	
//	 calculation of S1,S2,S3,S3,nvox
			       
	for (size_t i = 0L;i < size; i++) {
	      if (MASKptr[i]>0.5f) {
	       S1 += V1ptr[i]*V2ptr[i];
	       S2 += V2ptr[i]*V2ptr[i];
	       S3 += V2ptr[i]; 
	       S4 += V1ptr[i];
	       nvox ++;
	      }
	}       
	 
			
	A = static_cast<float> (nvox*S1 - S3*S4)/(nvox*S2 - S3*S3);
	B = static_cast<float> (A*S3  -  S4)/nvox;
        
	// calculation of the difference image
	
	for (size_t i = 0L;i < size; i++) {
	     if (MASKptr[i]>0.5f) {
	       BDptr[i] = A*V2ptr[i] -  B  - V1ptr[i];
	     }  else  {
               BDptr[i] = 0.f;
	     }
	}
	
	BD->update();
 
	params[0] = A;
	params[1] = B;
	
	Dict BDnParams;
	BDnParams["imdiff"] = BD;
	BDnParams["A"] = params[0];
	BDnParams["B"] = params[1];
		
	return BDnParams;
 }

//----------------------------------------------------------------------------------------------------------



EMData *Util::TwoDTestFunc(int Size, float p, float q,  float a, float b, int flag, float alphaDeg) //PRB
{
    int Mid= (Size+1)/2;

    if (flag<0 || flag>4) {
    	cout <<" flat must be 0,1,2,3, or 4";
    }
    if (flag==0) { // This is the real function
	   EMData* ImBW = new EMData();
	   ImBW->set_size(Size,Size,1);
	   ImBW->to_zero();
	   
	   float tempIm;
	   float x,y;
	
	   for (int ix=(1-Mid);  ix<Mid; ix++){
	        for (int iy=(1-Mid);  iy<Mid; iy++){
		  x = ix;
		  y = iy;
	       	  tempIm= (1/(2*M_PI)) * cos(p*x)* cos(q*y) * exp(-.5*x*x/(a*a))* exp(-.5*y*y/(b*b)) ;
		  (*ImBW)(ix+Mid-1,iy+Mid-1) = tempIm * exp(.5*p*p*a*a)* exp(.5*q*q*b*b);
	   	}
	   }
	   ImBW->done_data();
	   ImBW->set_complex(false);
	   ImBW->set_ri(true);
	
	
	   return ImBW;
   	}
   	if (flag==1) {  // This is the Fourier Transform
	   EMData* ImBWFFT = new EMData();
	   ImBWFFT ->set_size(2*Size,Size,1);
	   ImBWFFT ->to_zero();
	   
	   float r,s;
	
	   for (int ir=(1-Mid);  ir<Mid; ir++){
	        for (int is=(1-Mid);  is<Mid; is++){
		   r = ir;
		   s = is;
	       	   (*ImBWFFT)(2*(ir+Mid-1),is+Mid-1)= cosh(p*r*a*a) * cosh(q*s*b*b) *
		            exp(-.5*r*r*a*a)* exp(-.5*s*s*b*b);
	   	}
	   }
	   ImBWFFT->done_data();
	   ImBWFFT->set_complex(true);
	   ImBWFFT->set_ri(true);
	   ImBWFFT->set_shuffled(true);
	   ImBWFFT->set_fftodd(true);
	
	   return ImBWFFT;
   	}   		
   	if (flag==2 || flag==3) { //   This is the projection in Real Space
		float alpha =alphaDeg*M_PI/180.0;
		float C=cos(alpha);
		float S=sin(alpha);
		float D= sqrt(S*S*b*b + C*C*a*a);
		//float D2 = D*D;   PAP - to get rid of warning
			
		float P = p * C *a*a/D ;
		float Q = q * S *b*b/D ;

		if (flag==2) {
			EMData* pofalpha = new EMData();
			pofalpha ->set_size(Size,1,1);
			pofalpha ->to_zero();

			float Norm0 =  D*sqrt(2*pi);
			float Norm1 =  exp( .5*(P+Q)*(P+Q)) / Norm0 ;
			float Norm2 =  exp( .5*(P-Q)*(P-Q)) / Norm0 ;
			float sD;

			for (int is=(1-Mid);  is<Mid; is++){
				sD = is/D ;
				(*pofalpha)(is+Mid-1) =  Norm1 * exp(-.5*sD*sD)*cos(sD*(P+Q))
                         + Norm2 * exp(-.5*sD*sD)*cos(sD*(P-Q));
			}
			pofalpha-> done_data();
			pofalpha-> set_complex(false);
			pofalpha-> set_ri(true);

			return pofalpha;
		}   		
		if (flag==3) { // This is the projection in Fourier Space
			float vD;
		
			EMData* pofalphak = new EMData();
			pofalphak ->set_size(2*Size,1,1);
			pofalphak ->to_zero();
		
			for (int iv=(1-Mid);  iv<Mid; iv++){
				vD = iv*D ;
		 		(*pofalphak)(2*(iv+Mid-1)) =  exp(-.5*vD*vD)*(cosh(vD*(P+Q)) + cosh(vD*(P-Q)) );
			}
			pofalphak-> done_data();
			pofalphak-> set_complex(false);
			pofalphak-> set_ri(true);
		
			return pofalphak;
   		}
   	}   		
    if (flag==4) {
		cout <<" FH under construction";
   		EMData* OutFT= TwoDTestFunc(Size, p, q, a, b, 1);
   		EMData* TryFH= OutFT -> real2FH(4.0);
   		return TryFH;
   	}   			
}


void Util::spline_mat(float *x, float *y, int n,  float *xq, float *yq, int m) //PRB
{

	float x0= x[0];
	float x1= x[1];
	float x2= x[2];
	float y0= y[0];
	float y1= y[1];
	float y2= y[2];
	float yp1 =  (y1-y0)/(x1-x0) +  (y2-y0)/(x2-x0) - (y2-y1)/(x2-x1)  ;
	float xn  = x[n];
	float xnm1= x[n-1];
	float xnm2= x[n-2];
	float yn  = y[n];
	float ynm1= y[n-1];
	float ynm2= y[n-2];
	float ypn=  (yn-ynm1)/(xn-xnm1) +  (yn-ynm2)/(xn-xnm2) - (ynm1-ynm2)/(xnm1-xnm2) ;
	float *y2d = new float[n];
	Util::spline(x,y,n,yp1,ypn,y2d);
	Util::splint(x,y,y2d,n,xq,yq,m); //PRB
	delete [] y2d;
	return;
}


void Util::spline(float *x, float *y, int n, float yp1, float ypn, float *y2) //PRB
{
	int i,k;
	float p, qn, sig, un, *u;
	u=new float[n-1];

	if (yp1 > .99e30){
		y2[0]=u[0]=0.0;
	}else{
		y2[0]=-.5f;
		u[0] =(3.0f/ (x[1] -x[0]))*( (y[1]-y[0])/(x[1]-x[0]) -yp1);
	}

	for (i=1; i < n-1; i++) {
		sig= (x[i] - x[i-1])/(x[i+1] - x[i-1]);
		p = sig*y2[i-1] + 2.0f;
		y2[i]  = (sig-1.0f)/p;
		u[i] = (y[i+1] - y[i] )/(x[i+1]-x[i] ) -  (y[i] - y[i-1] )/(x[i] -x[i-1]);
		u[i] = (6.0f*u[i]/ (x[i+1]-x[i-1]) - sig*u[i-1])/p;
	}

	if (ypn>.99e30){
		qn=0; un=0;
	} else {
		qn= .5f;
		un= (3.0f/(x[n-1] -x[n-2])) * (ypn -  (y[n-1]-y[n-2])/(x[n-1]-x[n-2]));
	}
	y2[n-1]= (un - qn*u[n-2])/(qn*y2[n-2]+1.0f);
	for (k=n-2; k>=0; k--){
		y2[k]=y2[k]*y2[k+1]+u[k];
	}
	delete [] u;
}


void Util::splint( float *xa, float *ya, float *y2a, int n,  float *xq, float *yq, int m) //PRB
{
	int klo, khi, k;
	float h, b, a;

//	klo=0; // can try to put here
	for (int j=0; j<m;j++){
		klo=0;
		khi=n-1;
		while (khi-klo >1) {
			k=(khi+klo) >>1;
			if  (xa[k]>xq[j]){ khi=k;}
			else { klo=k;}
		}
		h=xa[khi]- xa[klo];
		if (h==0.0) printf("Bad XA input to routine SPLINT \n");
		a =(xa[khi]-xq[j])/h;
		b=(xq[j]-xa[klo])/h;
		yq[j]=a*ya[klo] + b*ya[khi]
			+ ((a*a*a-a)*y2a[klo]
			     +(b*b*b-b)*y2a[khi]) *(h*h)/6.0f;
	}
//	printf("h=%f, a = %f, b=%f, ya[klo]=%f, ya[khi]=%f , yq=%f\n",h, a, b, ya[klo], ya[khi],yq[0]);
}


void Util::Radialize(int *PermMatTr, float *kValsSorted,   // PRB
               float *weightofkValsSorted, int Size, int *SizeReturned)
{
	int iMax = (int) floor( (Size-1.0)/2 +.01);
	int CountMax = (iMax+2)*(iMax+1)/2;
	int Count=-1;
	float *kVals     = new float[CountMax];
	float *weightMat = new float[CountMax];
	int *PermMat     = new   int[CountMax];
	SizeReturned[0] = CountMax;

//	printf("Aa \n");	fflush(stdout);
	for (int jkx=0; jkx< iMax+1; jkx++) {
		for (int jky=0; jky< jkx+1; jky++) {
			Count++;
			kVals[Count] = sqrtf((float) (jkx*jkx +jky*jky));
			weightMat[Count]=  1.0;
			if (jkx!=0)  { weightMat[Count] *=2;}
			if (jky!=0)  { weightMat[Count] *=2;}
			if (jkx!=jky){ weightMat[Count] *=2;}
			PermMat[Count]=Count+1;
	}}

	int lkVals = Count+1;
//	printf("Cc \n");fflush(stdout);

	sort_mat(&kVals[0],&kVals[Count],
	     &PermMat[0],  &PermMat[Count]);  //PermMat is
				//also returned as well as kValsSorted
	fflush(stdout);

	int newInd;

        for (int iP=0; iP < lkVals ; iP++ ) {
		newInd =  PermMat[iP];
		PermMatTr[newInd-1] = iP+1;
	}

//	printf("Ee \n"); fflush(stdout);

	int CountA=-1;
	int CountB=-1;

	while (CountB< (CountMax-1)) {
		CountA++;
		CountB++;
//		printf("CountA=%d ; CountB=%d \n", CountA,CountB);fflush(stdout);
		kValsSorted[CountA] = kVals[CountB] ;
		if (CountB<(CountMax-1) ) {
			while (fabs(kVals[CountB] -kVals[CountB+1])<.0000001  ) {
				SizeReturned[0]--;
				for (int iP=0; iP < lkVals; iP++){
//					printf("iP=%d \n", iP);fflush(stdout);
					if  (PermMatTr[iP]>CountA+1) {
						PermMatTr[iP]--;
		    			}
		 		}
				CountB++;
	    		}
		}
	}
	

	for (int CountD=0; CountD < CountMax; CountD++) {
	    newInd = PermMatTr[CountD];
	    weightofkValsSorted[newInd-1] += weightMat[CountD];
        }

}


vector<float>
Util::voea(float delta, float t1, float t2, float p1, float p2)
{
	vector<float> angles;
	float psi = 0.0;
	if ((0.0 == t1)&&(0.0 == t2)||(t1 >= t2)) {
		t1 = 0.0f;
		t2 = 90.0f;
	}
	if ((0.0 == p1)&&(0.0 == p2)||(p1 >= p2)) {
		p1 = 0.0f;
		p2 = 359.9f;
	}
	bool skip = ((t1 < 90.0)&&(90.0 == t2)&&(0.0 == p1)&&(p2 > 180.0));
	for (float theta = t1; theta <= t2; theta += delta) {
		float detphi;
		int lt;
		if ((0.0 == theta)||(180.0 == theta)) {
			detphi = 360.0f;
			lt = 1;
		} else {
			detphi = delta/sin(theta*static_cast<float>(dgr_to_rad));
			lt = int((p2 - p1)/detphi)-1;
			if (lt < 1) lt = 1;
			detphi = (p2 - p1)/lt;
		}
		for (int i = 0; i < lt; i++) {
			float phi = p1 + i*detphi;
			if (skip&&(90.0 == theta)&&(phi > 180.0)) continue;
			angles.push_back(phi);
			angles.push_back(theta);
			angles.push_back(psi);
		}
	}
	return angles;
}


float Util::triquad(double r, double s, double t, float f[]) {
	const float c2 = 1.0f / 2.0f;
	const float c4 = 1.0f / 4.0f;
	const float c8 = 1.0f / 8.0f;
	float rs = (float)(r*s);
	float st = (float)(s*t);
	float rt = (float)(r*t);
	float rst = (float)(r*st);
	float rsq = (float)(1 - r*r);
	float ssq = (float)(1 - s*s);
	float tsq = (float)(1 - t*t);
	float rm1 = (float)(1 - r);
	float sm1 = (float)(1 - s);
	float tm1 = (float)(1 - t);
	float rp1 = (float)(1 + r);
	float sp1 = (float)(1 + s);
	float tp1 = (float)(1 + t);

	return (float)(
		(-c8) * rst * rm1  * sm1  * tm1 * f[ 0] +
		( c4) * st	* rsq  * sm1  * tm1 * f[ 1] +
		( c8) * rst * rp1  * sm1  * tm1 * f[ 2] +
		( c4) * rt	* rm1  * ssq  * tm1 * f[ 3] +
		(-c2) * t	* rsq  * ssq  * tm1 * f[ 4] +
		(-c4) * rt	* rp1  * ssq  * tm1 * f[ 5] +
		( c8) * rst * rm1  * sp1  * tm1 * f[ 6] +
		(-c4) * st	* rsq  * sp1  * tm1 * f[ 7] +
		(-c8) * rst * rp1  * sp1  * tm1 * f[ 8] +

		( c4) * rs	* rm1  * sm1  * tsq * f[ 9] +
		(-c2) * s	* rsq  * sm1  * tsq * f[10] +
		(-c4) * rs	* rp1  * sm1  * tsq * f[11] +
		(-c2) * r	* rm1  * ssq  * tsq * f[12] +
					  rsq  * ssq  * tsq * f[13] +
		( c2) * r	* rp1  * ssq  * tsq * f[14] +
		(-c4) * rs	* rm1  * sp1  * tsq * f[15] +
		( c2) * s	* rsq  * sp1  * tsq * f[16] +
		( c4) * rs	* rp1  * sp1  * tsq * f[17] +

		( c8) * rst * rm1  * sm1  * tp1 * f[18] +
		(-c4) * st	* rsq  * sm1  * tp1 * f[19] +
		(-c8) * rst * rp1  * sm1  * tp1 * f[20] +
		(-c4) * rt	* rm1  * ssq  * tp1 * f[21] +
		( c2) * t	* rsq  * ssq  * tp1 * f[22] +
		( c4) * rt	* rp1  * ssq  * tp1 * f[23] +
		(-c8) * rst * rm1  * sp1  * tp1 * f[24] +
		( c4) * st	* rsq  * sp1  * tp1 * f[25] +
		( c8) * rst * rp1  * sp1  * tp1 * f[26]);
}

#define  fdata(i,j)      fdata  [ i-1 + (j-1)*nxdata ]
float Util::quadri(float xx, float yy, int nxdata, int nydata, float* fdata)
{
/*
c  purpose: quadratic interpolation 
c 
c  parameters:       xx,yy treated as circularly closed.
c                    fdata - image 1..nxdata, 1..nydata
c
c                    f3    fc       f0, f1, f2, f3 are the values
c                     +             at the grid points.  x is the
c                     + x           point at which the function
c              f2++++f0++++f1       is to be estimated. (it need
c                     +             not be in the first quadrant).
c                     +             fc - the outer corner point
c                    f4             nearest x.
c
c                                   f0 is the value of the fdata at
c                                   fdata(i,j), it is the interior mesh
c                                   point nearest  x.
c                                   the coordinates of f0 are (x0,y0),
c                                   the coordinates of f1 are (xb,y0),
c                                   the coordinates of f2 are (xa,y0),
c                                   the coordinates of f3 are (x0,yb),
c                                   the coordinates of f4 are (x0,ya),
c                                   the coordinates of fc are (xc,yc),
c
c                   o               hxa, hxb are the mesh spacings
c                   +               in the x-direction to the left
c                  hyb              and right of the center point.
c                   +
c            ++hxa++o++hxb++o       hyb, hya are the mesh spacings
c                   +               in the y-direction.
c                  hya
c                   +               hxc equals either  hxb  or  hxa
c                   o               depending on where the corner
c                                   point is located.
c
c                                   construct the interpolant
c                                   f = f0 + c1*(x-x0) +
c                                       c2*(x-x0)*(x-x1) +
c                                       c3*(y-y0) + c4*(y-y0)*(y-y1)
c                                       + c5*(x-x0)*(y-y0)
c
c
*/
    float x, y, dx0, dy0, f0, c1, c2, c3, c4, c5, dxb, dyb;
    float quadri;
    int   i, j, ip1, im1, jp1, jm1, ic, jc, hxc, hyc;
    
    x = xx;
    y = yy;

    // circular closure
    if (x < 1.0)               x = x+(1 - floor(x) / nxdata) * nxdata;
    if (x > (float)nxdata+0.5) x = fmod(x-1.0f,(float)nxdata) + 1.0f;
    if (y < 1.0)               y = y+(1 - floor(y) / nydata) * nydata;
    if (y > (float)nydata+0.5) y = fmod(y-1.0f,(float)nydata) + 1.0f;


    i   = (int) floor(x);
    j   = (int) floor(y);

    dx0 = x - i;
    dy0 = y - j;

    ip1 = i + 1;
    im1 = i - 1;
    jp1 = j + 1;
    jm1 = j - 1;

    if (ip1 > nxdata) ip1 = ip1 - nxdata;
    if (im1 < 1)      im1 = im1 + nxdata;
    if (jp1 > nydata) jp1 = jp1 - nydata;
    if (jm1 < 1)      jm1 = jm1 + nydata;

    f0  = fdata(i,j);
    c1  = fdata(ip1,j) - f0;
    c2  = (c1 - f0 + fdata(im1,j)) * 0.5;
    c3  = fdata(i,jp1) - f0;
    c4  = (c3 - f0 + fdata(i,jm1)) * 0.5;

    dxb = dx0 - 1;
    dyb = dy0 - 1;

    // hxc & hyc are either 1 or -1
    if (dx0 >= 0) {
       hxc = 1;
    }
    else {
       hxc = -1;
    }
    if (dy0 >= 0) {
       hyc = 1;
    }
    else {
       hyc = -1;
    }
 
    ic  = i + hxc;
    jc  = j + hyc;

    if (ic > nxdata) {
       ic = ic - nxdata;
    }
    else if (ic < 1) {
       ic = ic + nxdata;
    }

    if (jc > nydata) {
       jc = jc - nydata;
    }
    else if (jc < 1) {
       jc = jc + nydata;
    }

    c5  =  ( (fdata(ic,jc) - f0 - hxc * c1 - (hxc * (hxc - 1.0)) * c2 
            - hyc * c3 - (hyc * (hyc - 1.0)) * c4) * (hxc * hyc));

    quadri = f0 + dx0 * (c1 + dxb * c2 + dy0 * c5) + dy0 * (c3 + dyb * c4);

    return quadri; 
}
#undef fdata










Util::KaiserBessel::KaiserBessel(float alpha_, int K_, float r_, float v_,
		                         int N_, float vtable_, int ntable_) 
		: alpha(alpha_), v(v_), r(r_), N(N_), K(K_), vtable(vtable_), 
		  ntable(ntable_) {
	// Default values are alpha=1.25, K=6, r=0.5, v = K/2
	if (0.f == v) v = float(K)/2;
	if (0.f == vtable) vtable = v;
	alphar = alpha*r;
	fac = static_cast<float>(twopi)*alphar*v;
	vadjust = 1.0f*v;
	facadj = static_cast<float>(twopi)*alphar*vadjust;
	build_I0table();
}

float Util::KaiserBessel::i0win(float x) const {
	float val0 = float(gsl_sf_bessel_I0(facadj));
	float absx = fabs(x);
	if (absx > vadjust) return 0.f;
	float rt = sqrt(1.f - pow(absx/vadjust, 2));
	float res = gsl_sf_bessel_I0(facadj*rt)/val0;
	return res;
}

void Util::KaiserBessel::build_I0table() {
	i0table.resize(ntable+1); // i0table[0:ntable]
	int ltab = int(round(float(ntable)/1.25f));
	fltb = float(ltab)/(K/2);
	float val0 = gsl_sf_bessel_I0(facadj);
	for (int i=ltab+1; i <= ntable; i++) i0table[i] = 0.f;
	for (int i=0; i <= ltab; i++) {
		float s = float(i)/fltb/N;
		if (s < vadjust) {
			float rt = sqrt(1.f - pow(s/vadjust, 2));
			i0table[i] = gsl_sf_bessel_I0(facadj*rt)/val0;
		} else {
			i0table[i] = 0.f;
		}
//		cout << "  "<<s*N<<"  "<<i0table[i] <<endl;
	}
}

float Util::KaiserBessel::I0table_maxerror() {
	float maxdiff = 0.f;
	for (int i = 1; i <= ntable; i++) {
		float diff = fabs(i0table[i] - i0table[i-1]);
		if (diff > maxdiff) maxdiff = diff;
	}
	return maxdiff;
}

float Util::KaiserBessel::sinhwin(float x) const {
	float val0 = sinh(fac)/fac;
	float absx = fabs(x);
	if (0.0 == x) {
		float res = 1.0f;
		return res;
	} else if (absx == alphar) {
		return 1.0f/val0;
	} else if (absx < alphar) {
		float rt = sqrt(1.0f - pow((x/alphar), 2));
		float facrt = fac*rt;
		float res = (sinh(facrt)/facrt)/val0;
		return res;
	} else {
		float rt = sqrt(pow((x/alphar),2) - 1.f);
		float facrt = fac*rt;
		float res = (sin(facrt)/facrt)/val0;
		return res;
	}
}

float Util::FakeKaiserBessel::i0win(float x) const {
	float val0 = sqrt(facadj)*float(gsl_sf_bessel_I1(facadj));
	float absx = fabs(x);
	if (absx > vadjust) return 0.f;
	float rt = sqrt(1.f - pow(absx/vadjust, 2));
	float res = sqrt(facadj*rt)*float(gsl_sf_bessel_I1(facadj*rt))/val0;
	return res;
}

void Util::FakeKaiserBessel::build_I0table() {
	i0table.resize(ntable+1); // i0table[0:ntable]
	int ltab = int(round(float(ntable)/1.1f));
	fltb = float(ltab)/(K/2);
	float val0 = sqrt(facadj)*gsl_sf_bessel_I1(facadj);
	for (int i=ltab+1; i <= ntable; i++) i0table[i] = 0.f;
	for (int i=0; i <= ltab; i++) {
		float s = float(i)/fltb/N;
		if (s < vadjust) {
			float rt = sqrt(1.f - pow(s/vadjust, 2));
			i0table[i] = sqrt(facadj*rt)*gsl_sf_bessel_I1(facadj*rt)/val0;
		} else {
			i0table[i] = 0.f;
		}
	}
}

float Util::FakeKaiserBessel::sinhwin(float x) const {
	float val0 = sinh(fac)/fac;
	float absx = fabs(x);
	if (0.0 == x) {
		float res = 1.0f;
		return res;
	} else if (absx == alphar) {
		return 1.0f/val0;
	} else if (absx < alphar) {
		float rt = sqrt(1.0f - pow((x/alphar), 2));
		float facrt = fac*rt;
		float res = (sinh(facrt)/facrt)/val0;
		return res;
	} else {
		float rt = sqrt(pow((x/alphar),2) - 1.f);
		float facrt = fac*rt;
		float res = (sin(facrt)/facrt)/val0;
		return res;
	}
}

#if 0 // 1-st order KB window
float Util::FakeKaiserBessel::sinhwin(float x) const {
	//float val0 = sinh(fac)/fac;
	float prefix = 2*facadj*vadjust/float(gsl_sf_bessel_I1(facadj));
	float val0 = prefix*(cosh(facadj) - sinh(facadj)/facadj);
	float absx = fabs(x);
	if (0.0 == x) {
		//float res = 1.0f;
		float res = val0;
		return res;
	} else if (absx == alphar) {
		//return 1.0f/val0;
		return prefix;
	} else if (absx < alphar) {
		float rt = sqrt(1.0f - pow((x/alphar), 2));
		//float facrt = fac*rt;
		float facrt = facadj*rt;
		//float res = (sinh(facrt)/facrt)/val0;
		float res = prefix*(cosh(facrt) - sinh(facrt)/facrt);
		return res;
	} else {
		float rt = sqrt(pow((x/alphar),2) - 1.f);
		//float facrt = fac*rt;
		float facrt = facadj*rt;
		//float res = (sin(facrt)/facrt)/val0;
		float res = prefix*(sin(facrt)/facrt - cos(facrt));
		return res;
	}
}
#endif // 0



EMData* Util::Polar2D(EMData* image, vector<int> numr, string mode){
   int nsam = image->get_xsize();
   int nrow = image->get_ysize();
   int nring = numr.size()/3;
   int lcirc = numr[3*nring-2]+numr[3*nring-1]-1;
   EMData* out = new EMData();
   char cmode = (mode == "F" || mode == "f") ? 'f' : 'h';
   out->set_size(lcirc,1,1);
   alrq(image->get_data(), nsam, nrow, &numr[0], out->get_data(), lcirc, nring, cmode);
   return out;
}

#define  circ(i)         circ   [(i)-1]
#define  numr(i,j)       numr   [((j)-1)*3 + (i)-1]
#define  xim(i,j)        xim    [((j)-1)*nsam + (i)-1]
void Util::alrq(float *xim,  int nsam , int nrow , int *numr,
          float *circ, int lcirc, int nring, char mode)
{
/* 
c                                                                     
c  purpose:                                                          
c                                                                   
c  resmaple to polar coordinates
c                                                                  
*/
   //  dimension         xim(nsam,nrow),circ(lcirc)
   //  integer           numr(3,nring)

   double dfi, dpi;
   int    ns2, nr2, i, inr, l, nsim, kcirc, lt, j;
   float  yq, xold, yold, fi, x, y;

   ns2 = nsam/2+1;
   nr2 = nrow/2+1;
   dpi = 2.0*atan(1.0);

   for (i=1;i<=nring;i++) {
     // radius of the ring
     inr = numr(1,i);
     yq  = inr;
     l   = numr(3,i);
     if (mode == 'h' || mode == 'H') {
        lt = l/2;
     }
     else  {    //if (mode == 'f' || mode == 'F' )
        lt = l/4;
     }

     nsim           = lt-1;
     dfi            = dpi/(nsim+1);
     kcirc          = numr(2,i);
     xold           = 0.0;
     yold           = inr;
     circ(kcirc)    = quadri(xold+ns2,yold+nr2,nsam,nrow,xim);
     xold           = inr;
     yold           = 0.0;
     circ(lt+kcirc) = quadri(xold+ns2,yold+nr2,nsam,nrow,xim);

     if (mode == 'f' || mode == 'F') {
        xold              = 0.0;
        yold              = -inr;
        circ(lt+lt+kcirc) = quadri(xold+ns2,yold+nr2,nsam,nrow,xim);
        xold              = -inr;
        yold              = 0.0;
        circ(lt+lt+lt+kcirc) = quadri(xold+ns2,yold+nr2,nsam,nrow,xim);
     }

     for (j=1;j<=nsim;j++) {
        fi               = dfi*j;
        x                = sin(fi)*yq;
        y                = cos(fi)*yq;
        xold             = x;
        yold             = y;
        circ(j+kcirc)    = quadri(xold+ns2,yold+nr2,nsam,nrow,xim);
        xold             =  y;
        yold             = -x;
        circ(j+lt+kcirc) = quadri(xold+ns2,yold+nr2,nsam,nrow,xim);

        if (mode == 'f' || mode == 'F')  {
           xold                = -x;
           yold                = -y;
           circ(j+lt+lt+kcirc) = quadri(xold+ns2,yold+nr2,nsam,nrow,xim);
           xold                = -y;
           yold                =  x;
           circ(j+lt+lt+lt+kcirc) = quadri(xold+ns2,yold+nr2,nsam,nrow,xim);
        };
     }
   }
 
}




EMData* Util::Polar2Dm(EMData* image, float cns2, float cnr2, vector<int> numr, string mode){
   int nsam = image->get_xsize();
   int nrow = image->get_ysize();
   int nring = numr.size()/3;
   int lcirc = numr[3*nring-2]+numr[3*nring-1]-1;
   EMData* out = new EMData();
   char cmode = (mode == "F" || mode == "f") ? 'f' : 'h';
   out->set_size(lcirc,1,1);
   alrq_ms(image->get_data(), nsam, nrow, cns2, cnr2, &numr[0], out->get_data(), lcirc, nring, cmode);
   return out;
}
void Util::alrq_ms(float *xim, int    nsam, int  nrow, float cns2, float cnr2,
             int  *numr, float *circ, int lcirc, int  nring, char  mode)
{
   double dpi, dfi;
   int    it, jt, inr, l, nsim, kcirc, lt;
   float  yq, xold, yold, fi, x, y;

   //     cns2 and cnr2 are predefined centers
   //     no need to set to zero, all elements are defined

   dpi = 2*atan(1.0);
   for (it=1;it<=nring;it++) {
      // radius of the ring
      inr = numr(1,it);
      yq  = inr;

      l = numr(3,it);
      if ( mode == 'h' || mode == 'H' ) { 
         lt = l / 2;
      }
      else { // if ( mode == 'f' || mode == 'F' )
         lt = l / 4;
      } 

      nsim  = lt - 1;
      dfi   = dpi / (nsim+1);
      kcirc = numr(2,it);
      xold  = 0.0;
      yold  = inr;

      circ(kcirc) = quadri(xold+cns2,yold+cnr2,nsam,nrow,xim);

      xold  = inr;
      yold  = 0.0;
      circ(lt+kcirc) = quadri(xold+cns2,yold+cnr2,nsam,nrow,xim);

      if ( mode == 'f' || mode == 'F' ) {
         xold = 0.0;
         yold = -inr;
         circ(lt+lt+kcirc) = quadri(xold+cns2,yold+cnr2,nsam,nrow,xim);

         xold = -inr;
         yold = 0.0;
         circ(lt+lt+lt+kcirc) = quadri(xold+cns2,yold+cnr2,nsam,nrow,xim);
      }
      
      for (jt=1;jt<=nsim;jt++) {
         fi   = dfi * jt;
         x    = sin(fi) * yq;
         y    = cos(fi) * yq;

         xold = x;
         yold = y;
         circ(jt+kcirc) = quadri(xold+cns2,yold+cnr2,nsam,nrow,xim);

         xold = y;
         yold = -x;
         circ(jt+lt+kcirc) = quadri(xold+cns2,yold+cnr2,nsam,nrow,xim);

         if ( mode == 'f' || mode == 'F' ) {
            xold = -x;
            yold = -y;
            circ(jt+lt+lt+kcirc) = quadri(xold+cns2,yold+cnr2,nsam,nrow,xim);

            xold = -y;
            yold = x;
            circ(jt+lt+lt+lt+kcirc) = quadri(xold+cns2,yold+cnr2,nsam,nrow,xim);
         }
      } // end for jt
   } //end for it
}
#undef  xim

EMData* Util::Polar2Dmi(EMData* image, float cns2, float cnr2, vector<int> numr, string mode, Util::KaiserBessel& kb){
// input image is twice the size of the original image
   int nring = numr.size()/3;
   int lcirc = numr[3*nring-2]+numr[3*nring-1]-1;
   EMData* out = new EMData();
   char cmode = (mode == "F" || mode == "f") ? 'f' : 'h';
   out->set_size(lcirc,1,1);
   Util::alrq_msi(image, cns2, cnr2, &numr[0], out->get_data(), lcirc, nring, cmode, kb);
   return out;
}

EMData* Util::alrq_msi(EMData* image, float cns2, float cnr2,
             int  *numr, float *circ, int lcirc, int  nring, char  mode, Util::KaiserBessel& kb)
{
   double dpi, dfi;
   int    it, jt, inr, l, nsim, kcirc, lt;
   float  yq, xold, yold, fi, x, y;

   //     cns2 and cnr2 are predefined centers
   //     no need to set to zero, all elements are defined

   dpi = 2*atan(1.0);
   for (it=1;it<=nring;it++) {
      // radius of the ring
      inr = numr(1,it);
      yq  = inr;

      l = numr(3,it);
      if ( mode == 'h' || mode == 'H' ) { 
         lt = l / 2;
      }
      else { // if ( mode == 'f' || mode == 'F' )
         lt = l / 4;
      } 

      nsim  = lt - 1;
      dfi   = dpi / (nsim+1);
      kcirc = numr(2,it);
      xold  = 0.0;
      yold  = inr;
      circ(kcirc) = image->get_pixel_conv(xold+cns2-1.0f,yold+cnr2-1.0f,0,kb);
      
      xold  = inr;
      yold  = 0.0;
      circ(lt+kcirc) = image->get_pixel_conv(xold+cns2-1.0f,yold+cnr2-1.0f,0,kb);

      if ( mode == 'f' || mode == 'F' ) {
         xold = 0.0;
         yold = -inr;
         circ(lt+lt+kcirc) = image->get_pixel_conv(xold+cns2-1.0f,yold+cnr2-1.0f,0,kb);

         xold = -inr;
         yold = 0.0;
         circ(lt+lt+lt+kcirc) = image->get_pixel_conv(xold+cns2-1.0f,yold+cnr2-1.0f,0,kb);
      }
      
      for (jt=1;jt<=nsim;jt++) {
         fi   = dfi * jt;
         x    = sin(fi) * yq;
         y    = cos(fi) * yq;

         xold = x;
         yold = y;
         circ(jt+kcirc) = image->get_pixel_conv(xold+cns2-1.0f,yold+cnr2-1.0f,0,kb);

         xold = y;
         yold = -x;
         circ(jt+lt+kcirc) = image->get_pixel_conv(xold+cns2-1.0f,yold+cnr2-1.0f,0,kb);

         if ( mode == 'f' || mode == 'F' ) {
            xold = -x;
            yold = -y;
            circ(jt+lt+lt+kcirc) = image->get_pixel_conv(xold+cns2-1.0f,yold+cnr2-1.0f,0,kb);

            xold = -y;
            yold = x;
            circ(jt+lt+lt+lt+kcirc) = image->get_pixel_conv(xold+cns2-1.0f,yold+cnr2-1.0f,0,kb);
         }
      } // end for jt
   } //end for it
}

/*

        A set of 1-D power-of-two FFTs
	Pawel & Chao 01/20/06
	
fftr_q(xcmplx,nv)
  single precision

 dimension xcmplx(2,iabs(nv)/2);
 xcmplx(1,1) --- R(0), xcmplx(2,1) --- R(NV/2)
 xcmplx(1,i) --- real, xcmplx(2,i) --- imaginary


fftr_d(xcmplx,nv)
  double precision

 dimension xcmplx(2,iabs(nv)/2);
 xcmplx(1,1) --- R(0), xcmplx(2,1) --- R(NV/2)
 xcmplx(1,i) --- real, xcmplx(2,i) --- imaginary



*/
#define  tab1(i)      tab1[i-1]
#define  xcmplx(i,j)  xcmplx [((j)-1)*2 + (i)-1]
#define  br(i)        br     [(i)-1]
#define  bi(i)        bi     [(i)-1]
//-----------------------------------------
void Util::fftc_d(double *br, double *bi, int ln, int ks)
{
   double rni,sgn,tr1,tr2,ti1,ti2;
   double cc,c,ss,s,t,x2,x3,x4,x5;
   int    b3,b4,b5,b6,b7,b56;
   int    n, k, l, j, i, ix0, ix1, status=0;

   const double tab1[] = {
   9.58737990959775e-5,
   1.91747597310703e-4,
   3.83495187571395e-4,
   7.66990318742704e-4,
   1.53398018628476e-3,
   3.06795676296598e-3,
   6.13588464915449e-3,
   1.22715382857199e-2,
   2.45412285229123e-2,
   4.90676743274181e-2,
   9.80171403295604e-2,
   1.95090322016128e-1,
   3.82683432365090e-1,
   7.07106781186546e-1,
   1.00000000000000,
   };

   n=(int)pow(2.f,ln);

   k=abs(ks);
   l=16-ln;
   b3=n*k;
   b6=b3;
   b7=k;
   if (ks > 0) {
      sgn=1.0;
   }
   else {
      sgn=-1.0;
      rni=1.0/(float)(n);
      j=1;
      for (i=1;i<=n;i++) {
         br(j)=br(j)*rni;
         bi(j)=bi(j)*rni;
         j=j+k;
      }
   }

L12:
   b6=b6/2;
   b5=b6;
   b4=2*b6;
   b56=b5-b6;

L14:
   tr1=br(b5+1);
   ti1=bi(b5+1);
   tr2=br(b56+1);
   ti2=bi(b56+1);

   br(b5+1)=tr2-tr1;
   bi(b5+1)=ti2-ti1;
   br(b56+1)=tr1+tr2;
   bi(b56+1)=ti1+ti2;

   b5=b5+b4;
   b56=b5-b6;
   if ( b5 <= b3 )  goto  L14;
   if ( b6 == b7 )  goto  L20;

   b4=b7;
   cc=2.0*pow(tab1(l),2);
   c=1.0-cc;
   l++;
   ss=sgn*tab1(l);
   s=ss;

L16:
   b5=b6+b4;
   b4=2*b6;
   b56=b5-b6;

L18:
   tr1=br(b5+1);
   ti1=bi(b5+1);
   tr2=br(b56+1);
   ti2=bi(b56+1);
   br(b5+1)=c*(tr2-tr1)-s*(ti2-ti1);
   bi(b5+1)=s*(tr2-tr1)+c*(ti2-ti1);
   br(b56+1)=tr1+tr2;
   bi(b56+1)=ti1+ti2;

   b5=b5+b4;
   b56=b5-b6;
   if ( b5 <= b3 )  goto  L18;
   b4=b5-b6;
   b5=b4-b3;
   c=-c;
   b4=b6-b5;
   if ( b5 < b4 )  goto  L16;
   b4=b4+b7;
   if ( b4 >= b5 ) goto  L12;

   t=c-cc*c-ss*s;
   s=s+ss*c-cc*s;
   c=t;
   goto  L16;

L20:
   ix0=b3/2;
   b3=b3-b7;
   b4=0;
   b5=0;
   b6=ix0;
   ix1=0;
   if (b6 == b7) goto EXIT;

L22:
   b4=b3-b4;
   b5=b3-b5;
   x2=br(b4+1);
   x3=br(b5+1);
   x4=bi(b4+1);
   x5=bi(b5+1);
   br(b4+1)=x3;
   br(b5+1)=x2;
   bi(b4+1)=x5;
   bi(b5+1)=x4;
   if(b6 < b4)  goto  L22;

L24:
   b4=b4+b7;
   b5=b6+b5;
   x2=br(b4+1);
   x3=br(b5+1);
   x4=bi(b4+1);
   x5=bi(b5+1);
   br(b4+1)=x3;
   br(b5+1)=x2;
   bi(b4+1)=x5;
   bi(b5+1)=x4;
   ix0=b6;

L26:
   ix0=ix0/2;
   ix1=ix1-ix0;
   if( ix1 >= 0)  goto L26;

   ix0=2*ix0;
   b4=b4+b7;
   ix1=ix1+ix0;
   b5=ix1;
   if ( b5 >= b4)  goto  L22;
   if ( b4 < b6)   goto  L24;

EXIT:
   status = 0;
}

// -----------------------------------------------------------------
void Util::fftc_q(float *br, float *bi, int ln, int ks)
{
   //  dimension  br(1),bi(1)

   int b3,b4,b5,b6,b7,b56;
   int n, k, l, j, i, ix0, ix1; 
   float rni, tr1, ti1, tr2, ti2, cc, c, ss, s, t, x2, x3, x4, x5, sgn;
   int status=0;

   const float tab1[] = {
   9.58737990959775e-5,
   1.91747597310703e-4,
   3.83495187571395e-4,
   7.66990318742704e-4,
   1.53398018628476e-3,
   3.06795676296598e-3,
   6.13588464915449e-3,
   1.22715382857199e-2,
   2.45412285229123e-2,
   4.90676743274181e-2,
   9.80171403295604e-2,
   1.95090322016128e-1,
   3.82683432365090e-1,
   7.07106781186546e-1,
   1.00000000000000,
   };

   n=(int)pow(2.f,ln);

   k=abs(ks);
   l=16-ln;
   b3=n*k;
   b6=b3;
   b7=k;
   if( ks > 0 ) {
      sgn=1.0;
   } 
   else {
      sgn=-1.0;
      rni=1.0/(float)n;
      j=1;
      for (i=1; i<=n;i++) {
         br(j)=br(j)*rni;
         bi(j)=bi(j)*rni;
         j=j+k;
      }
   }
L12:
   b6=b6/2;
   b5=b6;
   b4=2*b6;
   b56=b5-b6;
L14:
   tr1=br(b5+1);
   ti1=bi(b5+1);

   tr2=br(b56+1);
   ti2=bi(b56+1);

   br(b5+1)=tr2-tr1;
   bi(b5+1)=ti2-ti1;
   br(b56+1)=tr1+tr2;
   bi(b56+1)=ti1+ti2;

   b5=b5+b4;
   b56=b5-b6;
   if (b5 <= b3)  goto  L14;
   if (b6 == b7)  goto  L20;

   b4=b7;
   cc=2.0*pow(tab1(l),2);
   c=1.0-cc;
   l=l+1;
   ss=sgn*tab1(l);
   s=ss;
L16: 
   b5=b6+b4;
   b4=2*b6;
   b56=b5-b6;
L18:
   tr1=br(b5+1);
   ti1=bi(b5+1);
   tr2=br(b56+1);
   ti2=bi(b56+1);
   br(b5+1)=c*(tr2-tr1)-s*(ti2-ti1);
   bi(b5+1)=s*(tr2-tr1)+c*(ti2-ti1);
   br(b56+1)=tr1+tr2;
   bi(b56+1)=ti1+ti2;

   b5=b5+b4;
   b56=b5-b6;
   if(b5 <= b3)  goto L18;
   b4=b5-b6;
   b5=b4-b3;
   c=-c;
   b4=b6-b5;
   if(b5 < b4)  goto  L16;
   b4=b4+b7;
   if(b4 >= b5) goto  L12;

   t=c-cc*c-ss*s;
   s=s+ss*c-cc*s;
   c=t;
   goto  L16;
L20:
   ix0=b3/2;
   b3=b3-b7;
   b4=0;
   b5=0;
   b6=ix0;
   ix1=0;
   if ( b6 == b7) goto EXIT;
L22:
   b4=b3-b4;
   b5=b3-b5;
   x2=br(b4+1);
   x3=br(b5+1);
   x4=bi(b4+1);
   x5=bi(b5+1);
   br(b4+1)=x3;
   br(b5+1)=x2;
   bi(b4+1)=x5;
   bi(b5+1)=x4;
   if (b6 < b4) goto  L22;
L24:
   b4=b4+b7;
   b5=b6+b5;
   x2=br(b4+1);
   x3=br(b5+1);
   x4=bi(b4+1);
   x5=bi(b5+1);
   br(b4+1)=x3;
   br(b5+1)=x2;
   bi(b4+1)=x5;
   bi(b5+1)=x4;
   ix0=b6;
L26:
   ix0=ix0/2;
   ix1=ix1-ix0;
   if(ix1 >= 0)  goto  L26;

   ix0=2*ix0;
   b4=b4+b7;
   ix1=ix1+ix0;
   b5=ix1;
   if (b5 >= b4)  goto  L22;
   if (b4 < b6)   goto  L24;
EXIT:
   status = 0; 
}

void  Util::fftr_q(float *xcmplx, int nv) 
{
   // dimension xcmplx(2,1); xcmplx(1,i) --- real, xcmplx(2,i) --- imaginary

   int nu, inv, nu1, n, isub, n2, i1, i2, i;
   float ss, cc, c, s, tr, ti, tr1, tr2, ti1, ti2, t;

   const float tab1[] = {
   9.58737990959775e-5,
   1.91747597310703e-4,
   3.83495187571395e-4,
   7.66990318742704e-4,
   1.53398018628476e-3,
   3.06795676296598e-3,
   6.13588464915449e-3,
   1.22715382857199e-2,
   2.45412285229123e-2,
   4.90676743274181e-2,
   9.80171403295604e-2,
   1.95090322016128e-1,
   3.82683432365090e-1,
   7.07106781186546e-1,
   1.00000000000000,
   };

   nu=abs(nv);
   inv=nv/nu;
   nu1=nu-1;
   n=(int)pow(2.f,nu1);
   isub=16-nu1;

   ss=-tab1(isub);
   cc=-2.0*pow(tab1(isub-1),2.f);
   c=1.0;
   s=0.0;
   n2=n/2;
   if ( inv > 0) {
      fftc_q(&xcmplx(1,1),&xcmplx(2,1),nu1,2);
      tr=xcmplx(1,1);
      ti=xcmplx(2,1);
      xcmplx(1,1)=tr+ti;
      xcmplx(2,1)=tr-ti;
      for (i=1;i<=n2;i++) {
         i1=i+1;
         i2=n-i+1;
         tr1=xcmplx(1,i1);
         tr2=xcmplx(1,i2);
         ti1=xcmplx(2,i1);
         ti2=xcmplx(2,i2);
         t=(cc*c-ss*s)+c;
         s=(cc*s+ss*c)+s;
         c=t;
         xcmplx(1,i1)=0.5*((tr1+tr2)+(ti1+ti2)*c-(tr1-tr2)*s);
         xcmplx(1,i2)=0.5*((tr1+tr2)-(ti1+ti2)*c+(tr1-tr2)*s);
         xcmplx(2,i1)=0.5*((ti1-ti2)-(ti1+ti2)*s-(tr1-tr2)*c);
         xcmplx(2,i2)=0.5*(-(ti1-ti2)-(ti1+ti2)*s-(tr1-tr2)*c);
     }
   }
   else {
     tr=xcmplx(1,1);
     ti=xcmplx(2,1);
     xcmplx(1,1)=0.5*(tr+ti);
     xcmplx(2,1)=0.5*(tr-ti);
     for (i=1; i<=n2; i++) {
        i1=i+1;
        i2=n-i+1;
        tr1=xcmplx(1,i1);
        tr2=xcmplx(1,i2);
        ti1=xcmplx(2,i1);
        ti2=xcmplx(2,i2);
        t=(cc*c-ss*s)+c;
        s=(cc*s+ss*c)+s;
        c=t;
        xcmplx(1,i1)=0.5*((tr1+tr2)-(tr1-tr2)*s-(ti1+ti2)*c);
        xcmplx(1,i2)=0.5*((tr1+tr2)+(tr1-tr2)*s+(ti1+ti2)*c);
        xcmplx(2,i1)=0.5*((ti1-ti2)+(tr1-tr2)*c-(ti1+ti2)*s);
        xcmplx(2,i2)=0.5*(-(ti1-ti2)+(tr1-tr2)*c-(ti1+ti2)*s);
     }
     fftc_q(&xcmplx(1,1),&xcmplx(2,1),nu1,-2);
   }
}

// -------------------------------------------
void  Util::fftr_d(double *xcmplx, int nv) 
{
   // double precision  x(2,1)
   int    i1, i2,  nu, inv, nu1, n, isub, n2, i;
   double tr1,tr2,ti1,ti2,tr,ti;
   double cc,c,ss,s,t;
   const double tab1[] = {
   9.58737990959775e-5,
   1.91747597310703e-4,
   3.83495187571395e-4,
   7.66990318742704e-4,
   1.53398018628476e-3,
   3.06795676296598e-3,
   6.13588464915449e-3,
   1.22715382857199e-2,
   2.45412285229123e-2,
   4.90676743274181e-2,
   9.80171403295604e-2,
   1.95090322016128e-1,
   3.82683432365090e-1,
   7.07106781186546e-1,
   1.00000000000000,
   };
/*
   tab1(1)=9.58737990959775e-5;
   tab1(2)=1.91747597310703e-4;
   tab1(3)=3.83495187571395e-4;
   tab1(4)=7.66990318742704e-4;
   tab1(5)=1.53398018628476e-3;
   tab1(6)=3.06795676296598e-3;
   tab1(7)=6.13588464915449e-3;
   tab1(8)=1.22715382857199e-2;
   tab1(9)=2.45412285229123e-2;
   tab1(10)=4.90676743274181e-2;
   tab1(11)=9.80171403295604e-2;
   tab1(12)=1.95090322016128e-1;
   tab1(13)=3.82683432365090e-1;
   tab1(14)=7.07106781186546e-1;
   tab1(15)=1.00000000000000;
*/
   nu=abs(nv);
   inv=nv/nu;
   nu1=nu-1;
   n=(int)pow(2.f,nu1);
   isub=16-nu1;
   ss=-tab1(isub);
   cc=-2.0*pow(tab1(isub-1),2);
   c=1.0;
   s=0.0;
   n2=n/2;

   if ( inv > 0 ) {
      fftc_d(&xcmplx(1,1),&xcmplx(2,1),nu1,2);
      tr=xcmplx(1,1);
      ti=xcmplx(2,1);
      xcmplx(1,1)=tr+ti;
      xcmplx(2,1)=tr-ti;
      for (i=1;i<=n2;i++) {
         i1=i+1;
         i2=n-i+1;
         tr1=xcmplx(1,i1);
         tr2=xcmplx(1,i2);
         ti1=xcmplx(2,i1);
         ti2=xcmplx(2,i2);
         t=(cc*c-ss*s)+c;
         s=(cc*s+ss*c)+s;
         c=t;
         xcmplx(1,i1)=0.5*((tr1+tr2)+(ti1+ti2)*c-(tr1-tr2)*s);
         xcmplx(1,i2)=0.5*((tr1+tr2)-(ti1+ti2)*c+(tr1-tr2)*s);
         xcmplx(2,i1)=0.5*((ti1-ti2)-(ti1+ti2)*s-(tr1-tr2)*c);
         xcmplx(2,i2)=0.5*(-(ti1-ti2)-(ti1+ti2)*s-(tr1-tr2)*c);
      }
   }
   else {
      tr=xcmplx(1,1);
      ti=xcmplx(2,1);
      xcmplx(1,1)=0.5*(tr+ti);
      xcmplx(2,1)=0.5*(tr-ti);
      for (i=1;i<=n2;i++) {
         i1=i+1;
         i2=n-i+1;
         tr1=xcmplx(1,i1);
         tr2=xcmplx(1,i2);
         ti1=xcmplx(2,i1);
         ti2=xcmplx(2,i2);
         t=(cc*c-ss*s)+c;
         s=(cc*s+ss*c)+s;
         c=t;
         xcmplx(1,i1)=0.5*((tr1+tr2)-(tr1-tr2)*s-(ti1+ti2)*c);
         xcmplx(1,i2)=0.5*((tr1+tr2)+(tr1-tr2)*s+(ti1+ti2)*c);
         xcmplx(2,i1)=0.5*((ti1-ti2)+(tr1-tr2)*c-(ti1+ti2)*s);
         xcmplx(2,i2)=0.5*(-(ti1-ti2)+(tr1-tr2)*c-(ti1+ti2)*s);
      } 
      fftc_d(&xcmplx(1,1),&xcmplx(2,1),nu1,-2);
   } 
} 
#undef  tab1
#undef  xcmplx
#undef  br
#undef  bi

void Util::Frngs(EMData* circ, vector<int> numr){
   int nring = numr.size()/3;
   frngs(circ->get_data(), &numr[0],  nring);
}
void Util::frngs(float *circ, int *numr, int nring){
   int i, l; 
   for (i=1; i<=nring;i++) {
     l=(int)(log2(numr(3,i)));
     fftr_q(&circ(numr(2,i)),l);
   }
}
#undef  circ
//---------------------------------------------------
#define  b(i)            b      [(i)-1]
void Util::prb1d(double *b, int npoint, float *pos)
{
   double  c2,c3;
   int     nhalf;

   nhalf = npoint/2 + 1;
   *pos  = 0.0;

   if (npoint == 7) {
      c2 = 49.*b(1) + 6.*b(2) - 21.*b(3) - 32.*b(4) - 27.*b(5)
         - 6.*b(6) + 31.*b(7);
      c3 = 5.*b(1) - 3.*b(3) - 4.*b(4) - 3.*b(5) + 5.*b(7);
   } 
   else if (npoint == 5) {
      c2 = (74.*b(1) - 23.*b(2) - 60.*b(3) - 37.*b(4)
         + 46.*b(5) ) / (-70.);
      c3 = (2.*b(1) - b(2) - 2.*b(3) - b(4) + 2.*b(5) ) / 14.0;
   }
   else if (npoint == 3) {
      c2 = (5.*b(1) - 8.*b(2) + 3.*b(3) ) / (-2.0);
      c3 = (b(1) - 2.*b(2) + b(3) ) / 2.0;
   }
   else if (npoint == 9) {
      c2 = (1708.*b(1) + 581.*b(2) - 246.*b(3) - 773.*b(4)
         - 1000.*b(5) - 927.*b(6) - 554.*b(7) + 119.*b(8)
         + 1092.*b(9) ) / (-4620.);
      c3 = (28.*b(1) + 7.*b(2) - 8.*b(3) - 17.*b(4) - 20.*b(5)
         - 17.*b(6) - 8.*b(7) + 7.*b(8) + 28.*b(9) ) / 924.0;
   }
   if (c3 != 0.0)  *pos = c2/(2.0*c3) - nhalf;
}
#undef  b
boost::tuple<double, float, int> Util::Crosrng_e(EMData*  circ1, EMData* circ2, vector<int> numr, int neg) {
   int nring = numr.size()/3;
   int lcirc = numr[3*nring-2]+numr[3*nring-1]-1;
   int maxrin = numr[numr.size()-1];
   double qn;   float  tot;
   crosrng_e(circ1->get_data(), circ2->get_data(), lcirc, nring, maxrin, &numr[0], 
		      &qn, &tot, neg);
   return boost::make_tuple(qn, tot, neg);
}
#define  circ1(i)        circ1  [(i)-1]
#define  circ2(i)        circ2  [(i)-1]
#define  t(i)            t      [(i)-1]
#define  q(i)            q      [(i)-1]
#define  b(i)            b      [(i)-1]
#define  t7(i)           t7     [(i)-1]


//-----------------------------------------------
void Util::crosrng_e(float *circ1, float *circ2, int lcirc,
                     int    nring, int   maxrin, int *numr,
                     double *qn, float *tot, int neg)
{
/*
c checks single position, neg is flag for checking mirrored position
c
c  input - fourier transforms of rings!
c  first set is conjugated (mirrored) if neg
c  circ1 already multiplied by weights!
c       automatic arrays
	dimension         t(maxrin)  removed +2 as it is only needed for other ffts
	double precision  q(maxrin)
	double precision  t7(-3:3)
*/
   float *t;
   double t7[7], *q;
   int    i, j, k, ip, jc, numr3i, numr2i, jtot;
   float  pos;

   ip = -(int) (log2(maxrin));
   q = (double*)calloc(maxrin, sizeof(double));
   t = (float*)calloc(maxrin, sizeof(float));
     
//   cout << *qn <<"  " <<*tot<<"  "<<ip<<endl;
   for (i=1;i<=nring;i++) {
      numr3i = numr(3,i);
      numr2i = numr(2,i);

      t(1) = (circ1(numr2i)) * circ2(numr2i);

      if (numr3i != maxrin) {
         // test .ne. first for speed on some compilers
	 t(numr3i+1) = circ1(numr2i+1) * circ2(numr2i+1);
	 t(2)        = 0.0;

         if (neg) {
            // first set is conjugated (mirrored)
	    for (j=3;j<=numr3i;j=j+2) {
	       jc = j+numr2i-1;
	       t(j) =(circ1(jc))*circ2(jc)-(circ1(jc+1))*circ2(jc+1);
	       t(j+1) = -(circ1(jc))*circ2(jc+1)-(circ1(jc+1))*circ2(jc);
	    } 
         } 
         else {
	    for (j=3;j<=numr3i;j=j+2) {
	       jc = j+numr2i-1;
	       t(j) = (circ1(jc))*circ2(jc) + (circ1(jc+1))*circ2(jc+1);
	       t(j+1) = -(circ1(jc))*circ2(jc+1) + (circ1(jc+1))*circ2(jc);
	    }
         } 
         for (j=1;j<=numr3i+1;j++) q(j) = q(j) + t(j);
      }
      else {
	 t(2) = circ1(numr2i+1) * circ2(numr2i+1);
         if (neg) {
            // first set is conjugated (mirrored)
	    for (j=3;j<=maxrin;j=j+2) {
	       jc = j+numr2i-1;
	       t(j) = (circ1(jc))*circ2(jc) - (circ1(jc+1))*circ2(jc+1);
	       t(j+1) = -(circ1(jc))*circ2(jc+1) - (circ1(jc+1))*circ2(jc);
	    }
         }
         else {
	    for (j=3;j<=maxrin;j=j+2) {
	       jc = j+numr2i-1;
	       t(j) = (circ1(jc))*circ2(jc) + (circ1(jc+1))*circ2(jc+1);
	       t(j+1) = -(circ1(jc))*circ2(jc+1) + (circ1(jc+1))*circ2(jc);
	    } 
         }
         for (j = 1; j <= maxrin; j++) q(j) = q(j) + t(j);
      }
   }

   fftr_d(q,ip);

   *qn = -1.0e20;
   for (j=1;j<=maxrin;j++) {
      if (q(j) >= *qn) {
         *qn = q(j);
	 jtot = j;
      }
   } 

   for (k=-3;k<=3;k++) {
      j = (jtot+k+maxrin-1)%maxrin + 1;
      t7(k+4) = q(j);
   }

   prb1d(t7,7,&pos);

   *tot = (float)jtot + pos;

   if (q) free(q);
   if (t) free(t);
}

Dict Util::Crosrng_ms(EMData* circ1, EMData* circ2, vector<int> numr) {
   int nring = numr.size()/3;
   int lcirc = numr[3*nring-2]+numr[3*nring-1]-1;
   int maxrin = numr[numr.size()-1];
   double qn; float tot; double qm; float tmt;
   crosrng_ms(circ1->get_data(), circ2->get_data(), lcirc, nring, maxrin, 
              &numr[0], &qn, &tot, &qm, &tmt);
   Dict retvals;
   retvals["qn"] = qn;
   retvals["tot"] = tot;
   retvals["qm"] = qm;
   retvals["tmt"] = tmt;
   return retvals;
}

//---------------------------------------------------
void Util::crosrng_ms(float *circ1, float *circ2, int  lcirc, int  nring,
                      int   maxrin, int   *numr , double *qn, float *tot,
                      double   *qm, float *tmt)
{
/*
c
c  checks both straight & mirrored positions
c
c  input - fourier transforms of rings!!
c  circ1 already multiplied by weights!
c
c  notes: aug 04 attempted speedup using 
c       premultiply  arrays ie( circ12 = circ1 * circ2) much slower
c       various  other attempts  failed to yield improvement
c       this is a very important compute demand in alignmen & refine.
c       optional limit on angular search should be added.
*/

   // dimension         circ1(lcirc),circ2(lcirc)

   // t(maxrin), q(maxrin), t7(-3:3)  //maxrin+2 removed
   double *t, *q, t7[7];

   int   ip, jc, numr3i, numr2i, i, j, k, jtot;
   float t1, t2, t3, t4, c1, c2, d1, d2, pos;

   *qn  = 0.0;
   *qm  = 0.0;
   *tot = 0.0;
   *tmt = 0.0; 

   ip = -(int)(log2(maxrin));

   //  c - straight  = circ1 * conjg(circ2)
   //  zero q array
  
   q = (double*)calloc(maxrin,sizeof(double));  

   //   t - mirrored  = conjg(circ1) * conjg(circ2)
   //   zero t array
   t = (double*)calloc(maxrin,sizeof(double));

   //   premultiply  arrays ie( circ12 = circ1 * circ2) much slower

   for (i=1;i<=nring;i++) {

      numr3i = numr(3,i);
      numr2i = numr(2,i);

      t1   = circ1(numr2i) * circ2(numr2i);
      q(1) = q(1)+t1;
      t(1) = t(1)+t1;

      if (numr3i == maxrin)  {
         t1   = circ1(numr2i+1) * circ2(numr2i+1);
         q(2) = q(2)+t1;
         t(2) = t(2)+t1;
      }
      else {
	 t1          = circ1(numr2i+1) * circ2(numr2i+1);
	 q(numr3i+1) = q(numr3i+1)+t1;
      }

      for (j=3;j<=numr3i;j=j+2) {
	 jc     = j+numr2i-1;

 	 c1     = circ1(jc);
 	 c2     = circ1(jc+1);
         d1     = circ2(jc);
         d2     = circ2(jc+1);

  	 t1     = c1 * d1;
 	 t3     = c1 * d2;
 	 t2     = c2 * d2;
 	 t4     = c2 * d1;

	 q(j)   = q(j)   + t1 + t2;
	 q(j+1) = q(j+1) - t3 + t4;
	 t(j)   = t(j)   + t1 - t2;
	 t(j+1) = t(j+1) - t3 - t4;
      } 
  }

  fftr_d(q,ip);

  jtot = 0;
  *qn  = -1.0e20;
  for (j=1; j<=maxrin; j++) {
     if (q(j) >= *qn) {
        *qn  = q(j);
        jtot = j;
     }
  }

 
  for (k=-3;k<=3;k++) {
    j = ((jtot+k+maxrin-1)%maxrin)+1;
    t7(k+4) = q(j);
  }

  // interpolate
  prb1d(t7,7,&pos);
  *tot = (float)(jtot)+pos;

  // mirrored
  fftr_d(t,ip);

  // find angle
  *qm = -1.0e20;
  for (j=1; j<=maxrin;j++) {
     if ( t(j) >= *qm ) {
        *qm   = t(j);
        jtot = j;
     }
  }

  // find angle
  for (k=-3;k<=3;k++) {
    j       = ((jtot+k+maxrin-1)%maxrin) + 1;
    t7(k+4) = t(j);
  }

  // interpolate

  prb1d(t7,7,&pos);
  *tmt = float(jtot) + pos;

  free(t);
  free(q);
}
//  Try rotational gridding

Dict Util::Crosrng_msr(EMData* circ1, EMData* circ2, vector<int> numr) {
   int nring = numr.size()/3;
   int lcirc = numr[3*nring-2]+numr[3*nring-1]-1;
   int maxrin = numr[numr.size()-1];
   float qn; float tot; float qm; float tmt;
   crosrng_msr(circ1->get_data(), circ2->get_data(), lcirc, nring, maxrin, 
              &numr[0], &qn, &tot, &qm, &tmt);
   Dict retvals;
   retvals["qn"] = qn;
   retvals["tot"] = tot;
   retvals["qm"] = qm;
   retvals["tmt"] = tmt;
   return retvals;
}
#define  temp(i)            temp      [(i)-1]

//---------------------------------------------------
void Util::crosrng_msr(float *circ1, float *circ2, int  lcirc, int  nring,
                      int   maxrin, int   *numr , float *qn, float *tot,
                      float   *qm, float *tmt)
{
/*
c
c  checks both straight & mirrored positions
c
c  input - fourier transforms of rings!!
c  circ1 already multiplied by weights!
c
c  notes: aug 04 attempted speedup using 
c       premultiply  arrays ie( circ12 = circ1 * circ2) much slower
c       various  other attempts  failed to yield improvement
c       this is a very important compute demand in alignmen & refine.
c       optional limit on angular search should be added.
*/

   // dimension         circ1(lcirc),circ2(lcirc)

   // t(maxrin), q(maxrin), t7(-3:3)  //maxrin+2 removed
   double *t, *q, t7[7];
   float *temp;

   int   ip, jc, numr3i, numr2i, i, j, k, jtot;
   float t1, t2, t3, t4, c1, c2, d1, d2, pos;

   *qn  = 0.0;
   *qm  = 0.0;
   *tot = 0.0;
   *tmt = 0.0; 

   ip = -(int)(log2(maxrin));

   //  c - straight  = circ1 * conjg(circ2)
   //  zero q array
  
   q = (double*)calloc(maxrin,sizeof(double));  

   //   t - mirrored  = conjg(circ1) * conjg(circ2)
   //   zero t array
   t = (double*)calloc(maxrin,sizeof(double));


   temp = (float*)calloc(maxrin,sizeof(float));

   //   premultiply  arrays ie( circ12 = circ1 * circ2) much slower

   for (i=1;i<=nring;i++) {

      numr3i = numr(3,i);
      numr2i = numr(2,i);

      t1   = circ1(numr2i) * circ2(numr2i);
      q(1) = q(1)+t1;
      t(1) = t(1)+t1;

      if (numr3i == maxrin)  {
         t1   = circ1(numr2i+1) * circ2(numr2i+1);
         q(2) = q(2)+t1;
         t(2) = t(2)+t1;
      }
      else {
	 t1          = circ1(numr2i+1) * circ2(numr2i+1);
	 q(numr3i+1) = q(numr3i+1)+t1;
      }

      for (j=3;j<=numr3i;j=j+2) {
	 jc     = j+numr2i-1;

 	 c1     = circ1(jc);
 	 c2     = circ1(jc+1);
         d1     = circ2(jc);
         d2     = circ2(jc+1);

  	 t1     = c1 * d1;
 	 t3     = c1 * d2;
 	 t2     = c2 * d2;
 	 t4     = c2 * d1;

	 q(j)   = q(j)   + t1 + t2;
	 q(j+1) = q(j+1) - t3 + t4;
	 t(j)   = t(j)   + t1 - t2;
	 t(j+1) = t(j+1) - t3 - t4;
      } 
  }

  // straight
  for (i=1; i<=maxrin; i++) {temp(i)=q(i);}
  fftr_q(temp,ip);

  jtot = 0;
  *qn  = -1.0e20;
  for (j=1; j<=maxrin; j++) {
     if (temp(j) >= *qn) {
        *qn  = temp(j);
        jtot = j;
     }
  }
  
 
  for (k=-3;k<=3;k++) {
    j = ((jtot+k+maxrin-1)%maxrin)+1;
    t7(k+4) = temp(j);
  }

  // interpolate
  prb1d(t7,7,&pos);
  *tot = (float)(jtot)+pos;

  // mirrored
  for (i=1; i<=maxrin; i++) {temp(i)=t(i);}
  fftr_q(temp,ip);

  // find angle
  *qm = -1.0e20;
  for (j=1; j<=maxrin;j++) {
     if ( temp(j) >= *qm ) {
        *qm   = temp(j);
        jtot = j;
     }
  }

  // find angle
  for (k=-3;k<=3;k++) {
    j       = ((jtot+k+maxrin-1)%maxrin) + 1;
    t7(k+4) = t(j);
  }

  // interpolate

  prb1d(t7,7,&pos);
  *tmt = float(jtot) + pos;

  free(t);
  free(q);
  free(temp);
}
#undef temp


#define  dout(i,j)   dout[i+maxrin*j]
EMData* Util::Crosrng_msg(EMData* circ1, EMData* circ2, vector<int> numr) {
   int nring = numr.size()/3;
   int lcirc = numr[3*nring-2]+numr[3*nring-1]-1;
   int maxrin = numr[numr.size()-1];

   // t(maxrin), q(maxrin)  // removed +2
   double *t, *q;

   //  q - straight  = circ1 * conjg(circ2)
   //  zero q array
   q = (double*)calloc(maxrin,sizeof(double));

   //   t - mirrored  = conjg(circ1) * conjg(circ2)
   //   zero t array
   t = (double*)calloc(maxrin,sizeof(double));

   crosrng_msg(circ1->get_data(), circ2->get_data(), &q[0], &t[0], lcirc, nring, maxrin, &numr[0]);
   EMData* out = new EMData();
   out->set_size(maxrin,2,1);
   float *dout = out->get_data();
   for (int i=0; i<maxrin; i++) {dout(i,0)=q[i]; dout(i,1)=t[i];}
   /*out->set_size(maxrin,1,1);
   float *dout = out->get_data();
   for (int i=0; i<maxrin; i++) {dout(i,0)=q[i];}*/
   free(t);
   free(q);
   return out;
}
#undef out
//---------------------------------------------------
void Util::crosrng_msg(float *circ1, float *circ2, double *q, double *t, int  lcirc, int  nring,
                      int  maxrin, int   *numr )
{
/*
c
c  checks both straight & mirrored positions
c
c  input - fourier transforms of rings!!
c  circ1 already multiplied by weights!
c
c  notes: aug 04 attempted speedup using 
c       premultiply  arrays ie( circ12 = circ1 * circ2) much slower
c       various  other attempts  failed to yield improvement
c       this is a very important compute demand in alignmen & refine.
c       optional limit on angular search should be added.
*/

   // dimension         circ1(lcirc),circ2(lcirc)

   int   ip, jc, numr3i, numr2i, i, j;
   float t1, t2, t3, t4, c1, c2, d1, d2;

   ip = -(int)(log2(maxrin));

   //  q - straight  = circ1 * conjg(circ2)

   //   t - mirrored  = conjg(circ1) * conjg(circ2)

   //   premultiply  arrays ie( circ12 = circ1 * circ2) much slower

   for (i=1;i<=nring;i++) {

      numr3i = numr(3,i);
      numr2i = numr(2,i);

      t1   = circ1(numr2i) * circ2(numr2i);
      q(1) = q(1)+t1;
      t(1) = t(1)+t1;

      if (numr3i == maxrin)  {
         t1   = circ1(numr2i+1) * circ2(numr2i+1);
         q(2) = q(2)+t1;
         t(2) = t(2)+t1;
      }
      else {
	 t1          = circ1(numr2i+1) * circ2(numr2i+1);
	 q(numr3i+1) = q(numr3i+1)+t1;
      }

      for (j=3;j<=numr3i;j=j+2) {
	 jc     = j+numr2i-1;

 	 c1     = circ1(jc);
 	 c2     = circ1(jc+1);
         d1     = circ2(jc);
         d2     = circ2(jc+1);

  	 t1     = c1 * d1;
 	 t3     = c1 * d2;
 	 t2     = c2 * d2;
 	 t4     = c2 * d1;

	 q(j)   = q(j)   + t1 + t2;
	 q(j+1) = q(j+1) - t3 + t4;
	 t(j)   = t(j)   + t1 - t2;
	 t(j+1) = t(j+1) - t3 - t4;
      } 
  }
  
  // straight
  fftr_d(q,ip);

  // mirrored
  fftr_d(t,ip);
}
#undef  circ1
#undef  circ2
#undef  t
#undef  q
#undef  b
#undef  t7


#undef  numr



#define old_ptr(i,j,k) old_ptr[(i+(j+(k*ny))*nx)]
#define new_ptr(iptr,jptr,kptr) new_ptr[iptr+(jptr+(kptr*new_ny)*new_nx)]
EMData* Util::decimate(EMData* img, int x_step, int y_step, int z_step)
{
	if (!img) {
		throw NullPointerException("NULL input image");
	}
	int nx=img->get_xsize(),ny=img->get_ysize(),nz=img->get_zsize();
	if (0>(x_step-1)>(nx/2) || 0>(y_step-1)>(ny/2) || 0>(z_step-1)>(nz/2))
	{
		LOGERR("The Parameters for decimation cannot exceed the center of the image.");
		throw ImageDimensionException("The Parameters for decimation cannot exceed the center of the image.");	 
	}
	int new_st_x=(nx/2)%x_step,new_st_y=(ny/2)%y_step,new_st_z=(nz/2)%z_step;
	int rx=2*(nx/(2*x_step)),ry=2*(ny/(2*y_step)),rz=2*(nz/(2*z_step));
	int r1=int(ceil((nx-(x_step*rx))/(1.f*x_step))),r2=int(ceil((ny-(y_step*ry))/(1.f*y_step)));
	int r3=int(ceil((nz-(z_step*rz))/(1.f*z_step)));
	if(r1>1){r1=1;}
	if(r2>1){r2=1;}
	if(r3>1){r3=1;}
	EMData* img2 = new EMData();
	int new_nx=rx+r1,new_ny=ry+r2,new_nz=rz+r3;
	img2->set_size(new_nx,new_ny,new_nz);
	float *new_ptr=img2->get_data();
	float *old_ptr=img->get_data();
	int iptr,jptr,kptr=0;
	for (int k=new_st_z;k<nz;k+=z_step){jptr=0;
		for (int j=new_st_y;j<ny;j+=y_step){iptr=0;
			for (int i=new_st_x;i<nx;i+=x_step){				
				new_ptr(iptr,jptr,kptr)=old_ptr(i,j,k);
			iptr++;}
		jptr++;}
	kptr++;}
	img2->update();
	return img2;
}
#undef old_ptr
#undef new_ptr

#define inp(i,j,k) inp[i+(j+(k*new_ny))*new_nx]
#define outp(i,j,k) outp[i+(j+(k*new_ny))*new_nx]
EMData* Util::window(EMData* img,int new_nx,int new_ny, int new_nz, int x_shift, int y_shift, int z_shift)
{
	if (!img) {
		throw NullPointerException("NULL input image");
	}
	int nx=img->get_xsize(),ny=img->get_ysize(),nz=img->get_zsize();
	if(new_nx+x_shift > nx || new_ny+y_shift > ny || new_nz+z_shift > nz)
	{
		throw ImageDimensionException("The size of the window image cannot exceed the input image size.");	 
	}
	EMData* wind= new EMData();
	wind->set_size(new_nx,new_ny,new_nz);
	float *outp=wind->get_data();
	float *inp=img->get_data();

	int new_st_x=int(ceil((nx-new_nx)/2.f  + x_shift)),new_st_y=int(ceil((ny-new_ny)/2.f +
	y_shift)),new_st_z=int(ceil((nz-new_nz)/2.f + z_shift));
	if (new_st_x<0 || new_st_y<0 || new_st_z<0)
		throw ImageDimensionException("The image got shifted outside the input image. Solution: Change the shifting parameters");
	for (int k=0;k<new_nz;k++)
	    for(int j=0;j<new_ny;j++)
	        for(int i=0;i<new_nx;i++)
		     outp(i,j,k)=inp(i+new_st_x,j+new_st_y,k+new_st_z);		    
	wind->update();
	return wind;
}
#undef inp
#undef outp

#define inp(i,j,k) inp[i+(j+(k*new_ny))*new_nx]
#define outp(i,j,k) outp[i+(j+(k*new_ny))*new_nx]
EMData *Util::PAD(EMData* img, int new_nx, int new_ny, int new_nz, int x_shift, int y_shift, int z_shift, int background)
{
	if (!img) {
		throw NullPointerException("NULL input image");
	}
	int nx=img->get_xsize(),ny=img->get_ysize(),nz=img->get_zsize();
	if((new_nx+x_shift)<nx || (new_ny+y_shift)<ny || (new_nz+z_shift)<nz)
	{
		throw ImageDimensionException("The size of the padded image cannot be below the input image size.");	 
	}
	EMData* pading=new EMData();
	pading->set_size(new_nx,new_ny,new_nz);
	float *inp=img->get_data();
	float *outp=pading->get_data();
	/*if (background=='Average'){
		for(int k=1;k<nx-1;k++)
			for(int j=1;j<ny-1;j++)
				for (int i=1;i<nx-1;i++)
					sum1+=inp(i,j,k);
	float Avg=sum1/(nx*ny*nz);
	float mean=img->get_attr("mean");
	backgnd = fabs(mean-Avg);
	}
	else { backgnd=background;}*/					
	for (int k=0;k<new_nz;k++)
		for(int j=0;j<new_ny;j++)
			for (int i=0;i<new_nx;i++)
				outp(i,j,k)=background;
	int new_st_x=int(ceil((new_nx-nx)/2.f  + x_shift)),new_st_y=int(ceil((new_ny-ny)/2.f +
	y_shift)),new_st_z=int(ceil((new_nz-nz)/2.f + z_shift));
	if (new_st_x<0 || new_st_y<0 || new_st_z<0)
		throw ImageDimensionException("The image got shifted outside the input image. Solution: Change the shifting parameters");
	for (int k=0;k<nz;k++)
	    for(int j=0;j<ny;j++)
	        for(int i=0;i<nx;i++)
			outp(i,j,k)=inp(i+new_st_x,j+new_st_y,k+new_st_z); 
	pading->update();
	return pading;
}
#undef inp
#undef outp
