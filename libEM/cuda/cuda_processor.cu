

#include "cuda_util.h"
#include <stdio.h>

// Global texture
extern texture<float, 3, cudaReadModeElementType> tex;
extern texture<float, 2, cudaReadModeElementType> tex2d;

typedef unsigned int uint;

#ifdef WIN32
	#define M_PI 3.14159265358979323846f
#endif	//WIN32

__global__ void mult_kernel(float *data,const float scale,const int num_threads)
{

	const uint x=threadIdx.x;
	const uint y=blockIdx.x;

	data[x+y*num_threads] *= scale;
}

void emdata_processor_mult( EMDataForCuda* cuda_data, const float& mult) {
	
	int max_threads = 512;

	int num_calcs = cuda_data->nx*cuda_data->ny*cuda_data->nz;
	
	int grid_y = num_calcs/max_threads;
	int res_y = num_calcs - (grid_y*max_threads);
	
	if ( grid_y > 0 ) {
		const dim3 blockSize(max_threads,1, 1);
		const dim3 gridSize(grid_y,1,1);
		mult_kernel<<<gridSize,blockSize>>>(cuda_data->data,mult,max_threads);
	}
	
	if ( res_y > 0 ) {
		const dim3 blockSize(res_y,1, 1);
		const dim3 gridSize(1,1,1);
		mult_kernel<<<gridSize,blockSize>>>(cuda_data->data+grid_y*max_threads,mult,0);
	}

	cudaThreadSynchronize();	
}

__global__ void add_kernel(float *data,const float add,const int num_threads)
{

	const uint x=threadIdx.x;
	const uint y=blockIdx.x;

	data[x+y*num_threads] += add;
}

void emdata_processor_add( EMDataForCuda* cuda_data, const float& add) {
	
	int max_threads = 512;

	int num_calcs = cuda_data->nx*cuda_data->ny*cuda_data->nz;
	
	int grid_y = num_calcs/max_threads;
	int res_y = num_calcs - (grid_y*max_threads);
	
	if ( grid_y > 0 ) {
		const dim3 blockSize(max_threads,1, 1);
		const dim3 gridSize(grid_y,1,1);
		add_kernel<<<gridSize,blockSize>>>(cuda_data->data,add,max_threads);
	}
	
	if ( res_y > 0 ) {
		const dim3 blockSize(res_y,1, 1);
		const dim3 gridSize(1,1,1);
		add_kernel<<<gridSize,blockSize>>>(cuda_data->data+grid_y*max_threads,add,0);
	}

	cudaThreadSynchronize();	
}

__global__ void assignment_kernel(float *data,const float value,const int num_threads)
{

	const uint x=threadIdx.x;
	const uint y=blockIdx.x;

	data[x+y*num_threads] = value;
}

void emdata_processor_to_value( EMDataForCuda* cuda_data, const float& value) {
	
	int max_threads = 512;

	int num_calcs = cuda_data->nx*cuda_data->ny*cuda_data->nz;
	
	int grid_y = num_calcs/max_threads;
	int res_y = num_calcs - (grid_y*max_threads);
	
	if ( grid_y > 0 ) {
		const dim3 blockSize(max_threads,1, 1);
		const dim3 gridSize(grid_y,1,1);
		assignment_kernel<<<gridSize,blockSize>>>(cuda_data->data,value,max_threads);
	}
	
	if ( res_y > 0 ) {
		const dim3 blockSize(res_y,1, 1);
		const dim3 gridSize(1,1,1);
		assignment_kernel<<<gridSize,blockSize>>>(cuda_data->data+grid_y*max_threads,value,0);
	}

	cudaThreadSynchronize();	
}


__global__ void phaseorigin_to_center_fourier(float* data, const int num_threads, const int nx, const int ny, const int nz, const int offset)
{
	const uint x=threadIdx.x;
	const uint y=blockIdx.x;
	
	uint idx = x+y*num_threads+offset;
	const uint nxy = (nx/4)*ny;
	uint zz = idx/(nxy);
	uint yy = (idx-zz*nxy)/(nx/4);

	const uint xx = 4*(idx%(nx/4));
	
	const uint rnxy = nx*ny;
	const uint xoff = ((yy+zz)%2==0?2:0);
	const uint didx = zz*rnxy+yy*nx+xx+xoff;
	data[didx] *= -1;
	data[didx+1] *= -1;
}

void emdata_phaseorigin_to_center_fourier(const EMDataForCuda* cuda_data) {
	int nx = cuda_data->nx;
	int ny = cuda_data->ny;
	int nz = cuda_data->nz;
	float* data = cuda_data->data;
	
	if ( nx%2==0 && (ny%2==0 || ny==1 ) && (nz%2==0 || nz==1 ) ) {
		int max_threads = 512;
		
		int num_calcs = nz*ny*(nx/4);
			
		int grid_y = num_calcs/(max_threads);
		int res_y = num_calcs - grid_y*max_threads;

		//int odd_offset=0;
		//if (((ny/2)%2)+((nz/2)%2)==1) odd_offset=1;
		if (grid_y > 0) {
			const dim3 blockSize(max_threads,1, 1);
			const dim3 gridSize(grid_y,1,1);
			phaseorigin_to_center_fourier<<<gridSize,blockSize>>>(data,max_threads,nx,ny,nz,0);
		}
		
		if (res_y > 0) {
			const dim3 blockSize(res_y,1, 1);
			const dim3 gridSize(1,1,1);
			phaseorigin_to_center_fourier<<<gridSize,blockSize>>>(data,max_threads,nx,ny,nz,grid_y*max_threads);
		}
		cudaThreadSynchronize();
	} else {
		throw;
	}
}

__global__ void correlation_kernel(float *ldata, float* rdata,const int num_threads)
{

	const uint x=threadIdx.x;
	const uint y=blockIdx.x;

	const uint idx = 2*x + y*num_threads;
	const uint idxp1 = idx+1;
	
	const float v1 = ldata[idx];
	const float v2 = ldata[idxp1];
	const float u1 = rdata[idx];
	const float u2 = rdata[idxp1];
	
	ldata[idx] = v1*u1 + v2*u2;
	ldata[idxp1] = v1*u2 - v2*u1;
}

__global__ void auto_correlation_kernel(float *ldata, float* rdata,const int num_threads)
{

	const uint x=threadIdx.x;
	const uint y=blockIdx.x;

	const uint idx = 2*x + y*num_threads;
	const uint idxp1 = idx+1;
	
	const float v1 = ldata[idx];
	const float v2 = ldata[idxp1];
	const float u1 = rdata[idx];
	const float u2 = rdata[idxp1];
	
	ldata[idx] = v1*u1 + v2*u2;
	ldata[idxp1] = 0;
}


__global__ void correlation_kernel_texture_2D(float *ldata,const int num_threads,const int xsize,const int offset)
{

	const uint x=threadIdx.x;
	const uint y=blockIdx.x;

	const uint idx = 2*x + y*num_threads+offset;
	const uint idxp1 = idx+1;
	
	const uint tx = idx % xsize;
	const uint ty = idx / xsize;
	
	const float v1 = ldata[idx];
	const float v2 = ldata[idxp1];
	const float u1 = tex2D(tex2d,tx,ty);
	const float u2 =  tex2D(tex2d,tx+1,ty);
	
	ldata[idx] = v1*u1 + v2*u2;
	ldata[idxp1] = v1*u2 - v2*u1;
}


__global__ void correlation_kernel_texture_3D(float *ldata,const int num_threads, const int xsize, const int xysize, const int offset)
{

	const uint x=threadIdx.x;
	const uint y=blockIdx.x;

	const uint idx = 2*x + y*num_threads + offset;
	const uint idxp1 = idx+1;
	
	const uint tx = idx % xsize;
	const uint tz = idx / xysize;
	const uint ty = (idx - tz*xysize)/xsize;
	
	const float v1 = ldata[idx];
	const float v2 = ldata[idxp1];
	const float u1 = tex3D(tex,tx,ty,tz);
	const float u2 = tex3D(tex,tx+1,ty,tz);
	
	ldata[idx] = v1*u1 + v2*u2;
	ldata[idxp1] = v1*u2 - v2*u1;
}

void emdata_processor_correlation_texture( const EMDataForCuda* cuda_data, const int center ) {
	int max_threads = 512; // I halve the threads because each kernel access memory in two locations

	int num_calcs = cuda_data->nx*cuda_data->ny*cuda_data->nz;
	
	int grid_y = num_calcs/(2*max_threads);
	int res_y = (num_calcs - (2*grid_y*max_threads))/2;
	
// 	printf("Grid %d, Res %d, dims %d %d %d\n",grid_y,res_y,cuda_data->nx,cuda_data->ny,cuda_data->nz);
	
	if ( grid_y > 0 ) {
		const dim3 blockSize(max_threads,1, 1);
		const dim3 gridSize(grid_y,1,1);
		if (cuda_data->nz == 1) {
			correlation_kernel_texture_2D<<<gridSize,blockSize>>>(cuda_data->data,2*max_threads,cuda_data->nx,0);
		} else {
			correlation_kernel_texture_3D<<<gridSize,blockSize>>>(cuda_data->data,2*max_threads,cuda_data->nx,cuda_data->nx*cuda_data->ny,0);
		}
	}
// 	res_y = 0;
	if ( res_y > 0 ) {
		const dim3 blockSize(res_y,1,1);
		const dim3 gridSize(1,1,1);
		int inc = 2*grid_y*max_threads;
// 		printf("Res %d, inc %d\n",res_y,inc);
		if (cuda_data->nz == 1) {
			correlation_kernel_texture_2D<<<gridSize,blockSize>>>(cuda_data->data,0,cuda_data->nx,inc);
		} else {
			correlation_kernel_texture_3D<<<gridSize,blockSize>>>(cuda_data->data,0,cuda_data->nx,cuda_data->nx*cuda_data->ny,inc);
		}
	}
	
	cudaThreadSynchronize();
	if (center) {
		emdata_phaseorigin_to_center_fourier(cuda_data);
	}
}


void emdata_processor_correlation( const EMDataForCuda* left, const EMDataForCuda* right, const int center) {
	int max_threads = 512;

	int num_calcs = left->nx*left->ny*left->nz;
	
	int grid_y = num_calcs/(2*max_threads);
	int res_y = (num_calcs - (2*grid_y*max_threads))/2;
	
	//printf("Grid y %d, res %d, dims %d %d %d\n", grid_y,res_y,left->nx,left->ny,left->nz);
	
	if ( grid_y > 0 ) {
		const dim3 blockSize(max_threads,1, 1);
		const dim3 gridSize(grid_y,1,1);
		if (left->data != right->data) {
			correlation_kernel<<<gridSize,blockSize>>>(left->data,right->data,2*max_threads);
		} else {
			auto_correlation_kernel<<<gridSize,blockSize>>>(left->data,right->data,2*max_threads);
		}
	}
	
	if ( res_y > 0 ) {
		const dim3 blockSize(res_y,1, 1);
		const dim3 gridSize(1,1,1);
		int inc = 2*grid_y*max_threads;
		if (left->data != right->data) {
			correlation_kernel<<<gridSize,blockSize>>>(left->data+inc,right->data+inc,0);
		} else {
			auto_correlation_kernel<<<gridSize,blockSize>>>(left->data+inc,right->data+inc,0);
		}
	}
	cudaThreadSynchronize();
	
	if (center) {
		emdata_phaseorigin_to_center_fourier(left);
	}
}

__global__ void unwrap_kernel(float* dptr, const int num_threads, const int r1, const float p, const int nx, const int ny, const int nxp, const int dx,const int dy,const int weight_radial,const int offset) {
	const uint x=threadIdx.x;
	const uint y=blockIdx.x;
	
	const uint idx = x + y*num_threads+offset;
	
	const uint tx = idx % nxp;
	const uint ty = idx / nxp;
	
	float ang = tx * M_PI * p;
	float si = sinf(ang);
	float co = cosf(ang);

	float ypr1 = ty + r1;
	float xx = ypr1 * co + nx / 2 + dx;
	float yy = ypr1 * si + ny / 2 + dy;
	if ( weight_radial ) dptr[idx] = tex2D(tex2d,xx+0.5,yy+0.5)*ypr1;
	else dptr[idx] = tex2D(tex2d,xx+0.5,yy+0.5);
}

	
EMDataForCuda* emdata_unwrap(int r1, int r2, int xs, int num_pi, int dx, int dy, int weight_radial, int nx, int ny) {	
	
	float* dptr;
	int n = xs*(r2-r1);
	cudaError_t error = cudaMalloc((void**)&dptr,n*sizeof(float));
	if ( error != cudaSuccess ) {
		const char* s = cudaGetErrorString(error);
		printf("Cuda malloc failed in emdata_unwrap: %s\n",s);
		throw;
	}
	
	int max_threads = 512;
	int num_calcs = n;
	
	int grid_y = num_calcs/(max_threads);
	int res_y = num_calcs - grid_y*max_threads;
	
	//printf("Grid %d, res %d, n %d, p %f \n",grid_y,res_y,n, p/xs);
	
	if ( grid_y > 0 ) {
		const dim3 blockSize(max_threads,1, 1);
		const dim3 gridSize(grid_y,1,1);
		unwrap_kernel<<<gridSize,blockSize>>>(dptr,max_threads,r1,(float) num_pi/ (float)xs, nx,ny,xs,dx,dy,weight_radial,0);	
	}
	
	if ( res_y > 0 ) {
		const dim3 blockSize(res_y,1, 1);
		const dim3 gridSize(1,1,1);
		unwrap_kernel<<<gridSize,blockSize>>>(dptr,max_threads,r1, (float) num_pi/ (float)xs, nx,ny,xs,dx,dy,weight_radial,grid_y*max_threads);	
	}
	
	EMDataForCuda* tmp = (EMDataForCuda*) malloc( sizeof(EMDataForCuda) );
	tmp->data = dptr;
	tmp->nx = xs;
	tmp->ny = r2-r1;
	tmp->nz = 1;
	return tmp;
}



__global__ void swap_bot_left_top_right(float* data, const int num_threads, const int nx, const int ny, const int xodd, const int yodd, const int offset) {
	const uint x=threadIdx.x;
	const uint y=blockIdx.x;
	
	const uint gpu_idx = x+y*num_threads+offset; 
	const uint c = gpu_idx % (nx/2);
	const uint r = gpu_idx / (nx/2);
	
	const uint idx1 = r*nx + c;
	const uint idx2 = (r+ny/2+yodd)*nx + c + nx/2+xodd;
	float tmp = data[idx1];
	data[idx1] = data[idx2];
	data[idx2] = tmp;
}

__global__ void swap_top_left_bot_right(float* data, const int num_threads, const int nx, const int ny, const int xodd, const int yodd, const int offset) {
	const uint x=threadIdx.x;
	const uint y=blockIdx.x;
	
	const uint gpu_idx = x+y*num_threads+offset;
	const uint c = gpu_idx % (nx/2);
	const uint r = gpu_idx / (nx/2) + ny/2+yodd;
	
	const uint idx1 = r*nx + c;
	const uint idx2 = (r-ny/2-yodd)*nx + c + nx/2+xodd;
	float tmp = data[idx1];
	data[idx1] = data[idx2];
	data[idx2] = tmp;
}

__global__ void swap_middle_row(float* data, const int num_threads, const int nx, const int ny, const int xodd, const int yodd, const int offset) {
	const uint x=threadIdx.x;
	const uint y=blockIdx.x;
	
	const uint c = x+y*num_threads+offset;
	int r = ny/2;
	int idx1 = r*nx + c;
	int idx2 = r*nx + c + nx/2+ xodd;
	float tmp = data[idx1];
	data[idx1] = data[idx2];
	data[idx2] = tmp;
}

// Iterate along the central column, swapping values where appropriate
__global__ void swap_middle_column(float* data, const int num_threads, const int nx, const int ny, const int xodd, const int yodd, const int offset) {
	const uint x=threadIdx.x;
	const uint y=blockIdx.x;
	
	const uint r = x+y*num_threads+offset;
	int c = nx/2;
	int idx1 = r*nx + c;
	int idx2 = (r+ny/2+yodd)*nx + c;
	float tmp = data[idx1];
	data[idx1] = data[idx2];
	data[idx2] = tmp;
}

void swap_central_slices_180(EMDataForCuda* cuda_data)
{
	int nx = cuda_data->nx;
	int ny = cuda_data->ny;
	int nz = cuda_data->nz;

	int xodd = (nx % 2) == 1;
	int yodd = (ny % 2) == 1;
	//int zodd = (nz % 2) == 1;
	
	//int nxy = nx * ny;
	float *data = cuda_data->data;

	if ( ny == 1 && nz == 1 ){
		throw;
	}
	else if ( nz == 1 ) {
		if ( yodd ) {
			// Iterate along middle row, swapping values where appropriate
			
			int max_threads = 512;
			int num_calcs = nx/2;
				
			int grid_y = num_calcs/(max_threads);
			int res_y = num_calcs - grid_y*max_threads;
			
			if (grid_y > 0) {
				const dim3 blockSize(max_threads,1, 1);
				const dim3 gridSize(grid_y,1,1);
				swap_middle_row<<<gridSize,blockSize>>>(data,max_threads,nx,ny,xodd,yodd,0);
			}
			
			if (res_y) {
				const dim3 blockSize(res_y,1, 1);
				const dim3 gridSize(1,1,1);
				swap_middle_row<<<gridSize,blockSize>>>(data,max_threads,nx,ny,xodd,yodd,grid_y*max_threads);
			}
		}

		if ( xodd )	{
			// Iterate along the central column, swapping values where appropriate
			int max_threads = 512;
			int num_calcs = ny/2;
				
			int grid_y = num_calcs/(max_threads);
			int res_y = num_calcs - grid_y*max_threads;
			
			if (grid_y > 0) {
				const dim3 blockSize(max_threads,1, 1);
				const dim3 gridSize(grid_y,1,1);
				swap_middle_column<<<gridSize,blockSize>>>(data,max_threads,nx,ny,xodd,yodd,0);
			}
			
			if (res_y) {
				const dim3 blockSize(res_y,1, 1);
				const dim3 gridSize(1,1,1);
				swap_middle_column<<<gridSize,blockSize>>>(data,max_threads,nx,ny,xodd,yodd,grid_y*max_threads);
			}
			
		}
	}
	else // nx && ny && nz are greater than 1
	{
		throw;
	}
}

void swap_corners_180(EMDataForCuda* cuda_data)
{
	int nx = cuda_data->nx;
	int ny = cuda_data->ny;
	int nz = cuda_data->nz;

	int xodd = (nx % 2) == 1;
	int yodd = (ny % 2) == 1;
	//int zodd = (nz % 2) == 1;

	//int nxy = nx * ny;

	float *data = cuda_data->data;

	if ( ny == 1 && nz == 1 ){
		throw;
	}
	else if ( nz == 1 ) {
		int max_threads = 512;
		int num_calcs = ny/2*nx/2;
			
		int grid_y = num_calcs/(max_threads);
		int res_y = num_calcs - grid_y*max_threads;
		
		//printf("Grid %d, res %d, n %d\n",grid_y,res_y,num_calcs );
		// Swap bottom left and top right
		if (grid_y > 0) {
			const dim3 blockSize(max_threads,1, 1);
			const dim3 gridSize(grid_y,1,1);
			swap_bot_left_top_right<<<gridSize,blockSize>>>(data,max_threads,nx,ny,xodd,yodd,0);
		}
		
		if (res_y) {
			const dim3 blockSize(res_y,1, 1);
			const dim3 gridSize(1,1,1);
			swap_bot_left_top_right<<<gridSize,blockSize>>>(data,max_threads,nx,ny,xodd,yodd,grid_y*max_threads);
		}
		
		num_calcs = (ny-ny/2+yodd)*nx/2;
		//printf("Grid %d, res %d, n %d\n",grid_y,res_y,num_calcs );
					
		grid_y = num_calcs/(max_threads);
		res_y = num_calcs - grid_y*max_threads;
		// Swap the top left and bottom right corners
		if (grid_y > 0) {
			const dim3 blockSize(max_threads,1, 1);
			const dim3 gridSize(grid_y,1,1);
			swap_top_left_bot_right<<<gridSize,blockSize>>>(data,max_threads,nx,ny,xodd,yodd,0);
		}
		
		if (res_y) {
			const dim3 blockSize(res_y,1, 1);
			const dim3 gridSize(1,1,1);
			swap_top_left_bot_right<<<gridSize,blockSize>>>(data,max_threads,nx,ny,xodd,yodd,grid_y*max_threads);

		}
	}
	else // nx && ny && nz are greater than 1
	{
		throw;
	}
}

__global__ void middle_to_right(float* data, const int nx, const int ny)
{
	float tmp;
	for ( int r  = 0; r < ny; ++r ) {
		float last_val = data[r*nx+nx/2];
		for ( int c = nx-1; c >=  nx/2; --c ){
			int idx = r*nx+c;
			tmp = data[idx];
			data[idx] = last_val;
			last_val = tmp;
		}
	}
}

__global__ void middle_to_top(float* data, const int nx, const int ny)
{
	float tmp;
	for ( int c = 0; c < nx; ++c ) {
		// Get the value in the top row
		float last_val = data[ny/2*nx + c];
		for ( int r = ny-1; r >= ny/2; --r ){
			int idx = r*nx+c;
			tmp = data[idx];
			data[idx] = last_val;
			last_val = tmp;
		}
	}
}


void emdata_phaseorigin_to_center(EMDataForCuda* cuda_data) {
	int xodd = (cuda_data->nx % 2) == 1;
	int yodd = (cuda_data->ny % 2) == 1;
	//int zodd = (cuda_data->nz % 2) == 1;

	//int nxy = nx * ny;
	if ( cuda_data->nz == 1 && cuda_data->ny > 1 ){
		// The order in which these operations occur literally undoes what the
		// PhaseToCornerProcessor did to the image.
		// First, the corners sections of the image are swapped appropriately
		swap_corners_180(cuda_data);
		// Second, central pixel lines are swapped
		swap_central_slices_180(cuda_data);

		// Third, appropriate sections of the image are cyclically shifted by one pixel
		if (xodd) {
			// Transfer the middle column to the far right
			// Shift all from the far right to (but not including the) middle one to the left
			middle_to_right<<<1,1>>>(cuda_data->data,cuda_data->nx,cuda_data->ny);
		}
		if (yodd) {
			// Tranfer the middle row to the top,
			// shifting all pixels from the top row down one, until  but not including the) middle
			middle_to_top<<<1,1>>>(cuda_data->data,cuda_data->nx,cuda_data->ny);
		}
		cudaThreadSynchronize();
	} else {
		throw;
	}
}



