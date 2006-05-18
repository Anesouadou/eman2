/**
 * $Id$
 */
#include "all_imageio.h"
#include "portable_fileio.h"
#include "emcache.h"
#include "emdata.h"
#include "ctf.h"
#include "Assert.h"

#ifdef WIN32
	#include <windows.h>
	#define MAXPATHLEN (MAX_PATH*4)
#else
	#include <sys/param.h>
#endif	//WIN32

using namespace EMAN;

EMUtil::ImageType EMUtil::get_image_ext_type(const string & file_ext)
{
	ENTERFUNC;
	static bool initialized = false;
	static map < string, ImageType > imagetypes;

	if (!initialized) {
		imagetypes["mrc"] = IMAGE_MRC;
		imagetypes["MRC"] = IMAGE_MRC;
		
		imagetypes["tnf"] = IMAGE_MRC;
		imagetypes["TNF"] = IMAGE_MRC;
		
		imagetypes["dm3"] = IMAGE_DM3;
		imagetypes["DM3"] = IMAGE_DM3;
		
		imagetypes["spi"] = IMAGE_SPIDER;
		imagetypes["SPI"] = IMAGE_SPIDER;
		
		imagetypes["spider"] = IMAGE_SPIDER;
		imagetypes["SPIDER"] = IMAGE_SPIDER;
		
		imagetypes["spidersingle"] = IMAGE_SINGLE_SPIDER;
		imagetypes["SPIDERSINGLE"] = IMAGE_SINGLE_SPIDER;

		imagetypes["singlespider"] = IMAGE_SINGLE_SPIDER;
		imagetypes["SINGLESPIDER"] = IMAGE_SINGLE_SPIDER;
		
		imagetypes["img"] = IMAGE_IMAGIC;
		imagetypes["IMG"] = IMAGE_IMAGIC;
		
		imagetypes["hed"] = IMAGE_IMAGIC;
		imagetypes["HED"] = IMAGE_IMAGIC;

		imagetypes["imagic"] = IMAGE_IMAGIC;
		imagetypes["IMAGIC"] = IMAGE_IMAGIC;
		
		imagetypes["pgm"] = IMAGE_PGM;
		imagetypes["PGM"] = IMAGE_PGM;
		
		imagetypes["lst"] = IMAGE_LST;
		imagetypes["LST"] = IMAGE_LST;
		
		imagetypes["pif"] = IMAGE_PIF;
		imagetypes["PIF"] = IMAGE_PIF;
		
		imagetypes["png"] = IMAGE_PNG;
		imagetypes["PNG"] = IMAGE_PNG;
		
		imagetypes["h5"] = IMAGE_HDF;
		imagetypes["H5"] = IMAGE_HDF;
		
		imagetypes["hd5"] = IMAGE_HDF;
		imagetypes["HD5"] = IMAGE_HDF;
		
		imagetypes["hdf"] = IMAGE_HDF;
		imagetypes["HDF"] = IMAGE_HDF;
		
		imagetypes["tif"] = IMAGE_TIFF;
		imagetypes["TIF"] = IMAGE_TIFF;
		
		imagetypes["tiff"] = IMAGE_TIFF;
		imagetypes["TIFF"] = IMAGE_TIFF;
		
		imagetypes["vtk"] = IMAGE_VTK;
		imagetypes["VTK"] = IMAGE_VTK;
		
		imagetypes["hdr"] = IMAGE_SAL;
		imagetypes["HDR"] = IMAGE_SAL;
		
		imagetypes["sal"] = IMAGE_SAL;
		imagetypes["SAL"] = IMAGE_SAL;
		
		imagetypes["map"] = IMAGE_ICOS;
		imagetypes["MAP"] = IMAGE_ICOS;

		imagetypes["icos"] = IMAGE_ICOS;
		imagetypes["ICOS"] = IMAGE_ICOS;
		
		imagetypes["am"] = IMAGE_AMIRA;
		imagetypes["AM"] = IMAGE_AMIRA;
		
		imagetypes["amira"] = IMAGE_AMIRA;
		imagetypes["AMIRA"] = IMAGE_AMIRA;
		
		imagetypes["emim"] = IMAGE_EMIM;
		imagetypes["EMIM"] = IMAGE_EMIM;
		
		imagetypes["xplor"] = IMAGE_XPLOR;
		imagetypes["XPLOR"] = IMAGE_XPLOR;
		
		imagetypes["em"] = IMAGE_EM;
		imagetypes["EM"] = IMAGE_EM;
		
		imagetypes["dm2"] = IMAGE_GATAN2;
		imagetypes["DM2"] = IMAGE_GATAN2;

		imagetypes["v4l"] = IMAGE_V4L;
		imagetypes["V4L"] = IMAGE_V4L;
		
		imagetypes["jpg"] = IMAGE_JPEG;
		imagetypes["JPG"] = IMAGE_JPEG;
		imagetypes["jpeg"] = IMAGE_JPEG;
		imagetypes["JPEG"] = IMAGE_JPEG;

		initialized = true;
	}
	
	ImageType result = IMAGE_UNKNOWN;
	
	if (imagetypes.find(file_ext) != imagetypes.end()) {
		result = imagetypes[file_ext];
	}
	
	EXITFUNC;
	return result;
}


EMUtil::ImageType EMUtil::fast_get_image_type(const string & filename,
											  const void *first_block,
											  off_t file_size)
{
	ENTERFUNC;
	Assert(filename != "");
	Assert(first_block != 0);
	Assert(file_size > 0);
	
#ifdef ENABLE_V4L2
	if (filename.compare(0,5,"/dev/")==0) return IMAGE_V4L;
#endif

	string ext = Util::get_filename_ext(filename);
	if (ext == "") {
		return IMAGE_UNKNOWN;
	}
	ImageType image_type = get_image_ext_type(ext);

	switch (image_type) {
	case IMAGE_MRC:
		if (MrcIO::is_valid(first_block, file_size)) {
			return IMAGE_MRC;
		}
		break;
	case IMAGE_IMAGIC:
		if (ImagicIO::is_valid(first_block)) {
			return IMAGE_IMAGIC;
		}
		break;
	case IMAGE_DM3:
		if (DM3IO::is_valid(first_block)) {
			return IMAGE_DM3;
		}
		break;
#ifdef EM_HDF5
	case IMAGE_HDF:
		if (HdfIO::is_valid(first_block)) {
			return IMAGE_HDF;
		}
		break;
#endif
	case IMAGE_LST:
		if (LstIO::is_valid(first_block)) {
			return IMAGE_LST;
		}
		break;
#ifdef EM_TIFF
	case IMAGE_TIFF:
		if (TiffIO::is_valid(first_block)) {
			return IMAGE_TIFF;
		}
		break;
#endif
	case IMAGE_SPIDER:
		if (SpiderIO::is_valid(first_block)) {
			return IMAGE_SPIDER;
		}
		break;
	case IMAGE_SINGLE_SPIDER:
		if (SingleSpiderIO::is_valid(first_block)) {
			return IMAGE_SINGLE_SPIDER;
		}
		break;
	case IMAGE_PIF:
		if (PifIO::is_valid(first_block)) {
			return IMAGE_PIF;
		}
		break;
#ifdef EM_PNG
	case IMAGE_PNG:
		if (PngIO::is_valid(first_block)) {
			return IMAGE_PNG;
		}
		break;
#endif
	case IMAGE_VTK:
		if (VtkIO::is_valid(first_block)) {
			return IMAGE_VTK;
		}
		break;
	case IMAGE_PGM:
		if (PgmIO::is_valid(first_block)) {
			return IMAGE_PGM;
		}
		break;
	case IMAGE_EMIM:
		if (EmimIO::is_valid(first_block)) {
			return IMAGE_EMIM;
		}
		break;
	case IMAGE_ICOS:
		if (IcosIO::is_valid(first_block)) {
			return IMAGE_ICOS;
		}
		break;
	case IMAGE_SAL:
		if (SalIO::is_valid(first_block)) {
			return IMAGE_SAL;
		}
		break;
	case IMAGE_AMIRA:
		if (AmiraIO::is_valid(first_block)) {
			return IMAGE_AMIRA;
		}
		break;
	case IMAGE_XPLOR:
		if (XplorIO::is_valid(first_block)) {
			return IMAGE_XPLOR;
		}
		break;
	case IMAGE_GATAN2:
		if (Gatan2IO::is_valid(first_block)) {
			return IMAGE_GATAN2;
		}
		break;
	case IMAGE_EM:
		if (EmIO::is_valid(first_block, file_size)) {
			return IMAGE_EM;
		}
		break;
	default:
		return IMAGE_UNKNOWN;
	}
	EXITFUNC;
	return IMAGE_UNKNOWN;
}


EMUtil::ImageType EMUtil::get_image_type(const string & in_filename)
{
	ENTERFUNC;
	Assert(in_filename != "");
	
#ifdef ENABLE_V4L2
	if (in_filename.compare(0,5,"/dev/")==0) return IMAGE_V4L;
#endif
	
	string filename = in_filename;

	string old_ext = Util::get_filename_ext(filename);
	if (old_ext == ImagicIO::IMG_EXT) {
		filename = Util::change_filename_ext(filename, ImagicIO::HED_EXT);
	}
	
	FILE *in = fopen(filename.c_str(), "rb");
	if (!in) {
		throw FileAccessException(filename);
	}

	char first_block[1024];
	size_t n = fread(first_block, sizeof(char), sizeof(first_block), in);
	portable_fseek(in, 0, SEEK_END);
	off_t file_size = portable_ftell(in);

	if (n == 0) {
		LOGERR("file '%s' is an empty file", filename.c_str());
		fclose(in);
		return IMAGE_UNKNOWN;
	}
	fclose(in);

	ImageType image_type = fast_get_image_type(filename, first_block, file_size);
	if (image_type != IMAGE_UNKNOWN) {
		return image_type;
	}

	if (MrcIO::is_valid(first_block, file_size)) {
		image_type = IMAGE_MRC;
	}
	else if (DM3IO::is_valid(first_block)) {
		image_type = IMAGE_DM3;
	}
#ifdef EM_HDF5
	else if (HdfIO::is_valid(first_block)) {
		image_type = IMAGE_HDF;
	}
#endif
	else if (LstIO::is_valid(first_block)) {
		image_type = IMAGE_LST;
	}
#ifdef EM_TIFF
	else if (TiffIO::is_valid(first_block)) {
		image_type = IMAGE_TIFF;
	}
#endif
	else if (SpiderIO::is_valid(first_block)) {
		image_type = IMAGE_SPIDER;
	}
	else if (SingleSpiderIO::is_valid(first_block)) {
		image_type = IMAGE_SINGLE_SPIDER;
	}
	else if (PifIO::is_valid(first_block)) {
		image_type = IMAGE_PIF;
	}
#ifdef EM_PNG
	else if (PngIO::is_valid(first_block)) {
		image_type = IMAGE_PNG;
	}
#endif
	else if (VtkIO::is_valid(first_block)) {
		image_type = IMAGE_VTK;
	}
	else if (PgmIO::is_valid(first_block)) {
		image_type = IMAGE_PGM;
	}
	else if (EmimIO::is_valid(first_block)) {
		image_type = IMAGE_EMIM;
	}
	else if (IcosIO::is_valid(first_block)) {
		image_type = IMAGE_ICOS;
	}
	else if (SalIO::is_valid(first_block)) {
		image_type = IMAGE_SAL;
	}
	else if (AmiraIO::is_valid(first_block)) {
		image_type = IMAGE_AMIRA;
	}
	else if (XplorIO::is_valid(first_block)) {
		image_type = IMAGE_XPLOR;
	}
	else if (Gatan2IO::is_valid(first_block)) {
		image_type = IMAGE_GATAN2;
	}
	else if (EmIO::is_valid(first_block, file_size)) {
		image_type = IMAGE_EM;
	}
	else if (ImagicIO::is_valid(first_block)) {
		image_type = IMAGE_IMAGIC;
	}
	else {
		//LOGERR("I don't know this image's type: '%s'", filename.c_str());
		throw ImageFormatException("invalid image type");
	}

	EXITFUNC;
	return image_type;
}


int EMUtil::get_image_count(const string & filename)
{
	ENTERFUNC;
	Assert(filename != "");
	
	int nimg = 0;
	ImageIO *imageio = get_imageio(filename, ImageIO::READ_ONLY);

	if (imageio) {
		nimg = imageio->get_nimg();
	}
#ifndef IMAGEIO_CACHE
	if( imageio )
	{
		delete imageio;
		imageio = 0;
	}
#endif
	EXITFUNC;
	return nimg;
}


ImageIO *EMUtil::get_imageio(const string & filename, int rw,
							 ImageType image_type)
{
	ENTERFUNC;
	Assert(filename != "");
	Assert(rw == ImageIO::READ_ONLY ||
		   rw == ImageIO::READ_WRITE ||
		   rw == ImageIO::WRITE_ONLY);
	
	ImageIO *imageio = 0;
#ifdef IMAGEIO_CACHE
	imageio = GlobalCache::instance()->get_imageio(filename, rw);
	if (imageio) {
		return imageio;
	}
#endif
	
	ImageIO::IOMode rw_mode = static_cast < ImageIO::IOMode > (rw);
	
	if (image_type == IMAGE_UNKNOWN) {
		if(rw == ImageIO::WRITE_ONLY || rw == ImageIO::READ_WRITE) {
			throw ImageFormatException("writing to this image format not supported.");
		}
		
		image_type = get_image_type(filename);
	}

	switch (image_type) {
#ifdef ENABLE_V4L2
	case IMAGE_V4L:
		imageio = new V4L2IO(filename, rw_mode);
		break;
#endif
	case IMAGE_MRC:
		imageio = new MrcIO(filename, rw_mode);
		break;
	case IMAGE_IMAGIC:
		imageio = new ImagicIO(filename, rw_mode);
		break;
	case IMAGE_DM3:
		imageio = new DM3IO(filename, rw_mode);
		break;
#ifdef EM_TIFF
	case IMAGE_TIFF:
		imageio = new TiffIO(filename, rw_mode);
		break;
#endif
#ifdef EM_HDF5
	case IMAGE_HDF:
		imageio = new HdfIO(filename, rw_mode);
		break;
#endif
	case IMAGE_LST:
		imageio = new LstIO(filename, rw_mode);
		break;
	case IMAGE_PIF:
		imageio = new PifIO(filename, rw_mode);
		break;
	case IMAGE_VTK:
		imageio = new VtkIO(filename, rw_mode);
		break;
	case IMAGE_SPIDER:
		imageio = new SpiderIO(filename, rw_mode);
		break;
	case IMAGE_SINGLE_SPIDER:
		imageio = new SingleSpiderIO(filename, rw_mode);
		break;
	case IMAGE_PGM:
		imageio = new PgmIO(filename, rw_mode);
		break;
	case IMAGE_EMIM:
		imageio = new EmimIO(filename, rw_mode);
		break;
	case IMAGE_ICOS:
		imageio = new IcosIO(filename, rw_mode);
		break;
#ifdef EM_PNG
	case IMAGE_PNG:
		imageio = new PngIO(filename, rw_mode);
		break;
#endif
	case IMAGE_SAL:
		imageio = new SalIO(filename, rw_mode);
		break;
	case IMAGE_AMIRA:
		imageio = new AmiraIO(filename, rw_mode);
		break;
	case IMAGE_GATAN2:
		imageio = new Gatan2IO(filename, rw_mode);
		break;
	case IMAGE_EM:
		imageio = new EmIO(filename, rw_mode);
		break;
	case IMAGE_XPLOR:
		imageio = new XplorIO(filename, rw_mode);
		break;
	default:
		break;
	}
#ifdef IMAGEIO_CACHE
	GlobalCache::instance()->add_imageio(filename, rw, imageio);
#endif
	EXITFUNC;
	return imageio;
}



const char *EMUtil::get_imagetype_name(ImageType t)
{
	switch (t) {
	case IMAGE_V4L:
		return "V4L2";
	case IMAGE_MRC:
		return "MRC";
	case IMAGE_SPIDER:
		return "SPIDER";
	case IMAGE_SINGLE_SPIDER:
		return "Single-SPIDER";
	case IMAGE_IMAGIC:
		return "IMAGIC";
	case IMAGE_PGM:
		return "PGM";
	case IMAGE_LST:
		return "LST";
	case IMAGE_PIF:
		return "PIF";
	case IMAGE_PNG:
		return "PNG";
	case IMAGE_HDF:
		return "HDF5";
	case IMAGE_DM3:
		return "GatanDM3";
	case IMAGE_TIFF:
		return "TIFF";
	case IMAGE_VTK:
		return "VTK";
	case IMAGE_SAL:
		return "HDR";
	case IMAGE_ICOS:
		return "ICOS_MAP";
	case IMAGE_EMIM:
		return "EMIM";
	case IMAGE_GATAN2:
		return "GatanDM2";
	case IMAGE_AMIRA:
		return "AmiraMesh";
	case IMAGE_XPLOR:
		return "XPLOR";
	case IMAGE_EM:
		return "EM";
	case IMAGE_UNKNOWN:
		return "unknown";
	}
	return "unknown";
}

const char *EMUtil::get_datatype_string(EMDataType type)
{
	switch (type) {
	case EM_CHAR:
		return "CHAR";
	case EM_UCHAR:
		return "UNSIGNED CHAR";
	case EM_SHORT:
		return "SHORT";
	case EM_USHORT:
		return "UNSIGNED SHORT";
	case EM_INT:
		return "INT";
	case EM_UINT:
		return "UNSIGNED INT";
	case EM_FLOAT:
		return "FLOAT";
	case EM_DOUBLE:
		return "DOUBLE";
	case EM_SHORT_COMPLEX:
		return "SHORT_COMPLEX";
	case EM_USHORT_COMPLEX:
		return "USHORT_COMPLEX";
	case EM_FLOAT_COMPLEX:
		return "FLOAT_COMPLEX";
	case EM_UNKNOWN:
		return "UNKNOWN";
	}
	return "UNKNOWN";
}

void EMUtil::get_region_dims(const Region * area, int nx, int *area_x,
							 int ny, int *area_y, int nz, int *area_z)
{
	Assert(area_x);
	Assert(area_y);
	
	if (!area) {
		*area_x = nx;
		*area_y = ny;
		if (area_z) {
			*area_z = nz;
		}
	}
	else {
		*area_x = (int)area->size[0];
		*area_y = (int)area->size[1];

		if (area_z) {
			if (area->get_ndim() > 2 && nz > 1) {
				*area_z = (int)area->size[2];
			}
			else {
				*area_z = 1;
			}
		}
	}
}

void EMUtil::get_region_origins(const Region * area, int *p_x0, int *p_y0, int *p_z0,
								int nz, int image_index)
{
	Assert(p_x0);
	Assert(p_y0);
	
	if (area) {
		*p_x0 = static_cast < int >(area->origin[0]);
		*p_y0 = static_cast < int >(area->origin[1]);

		if (p_z0 && nz > 1 && area->get_ndim() > 2) {
			*p_z0 = static_cast < int >(area->origin[2]);
		}
	}
	else {
		*p_x0 = 0;
		*p_y0 = 0;
		if (p_z0) {
			*p_z0 = nz > 1 ? 0 : image_index;
		}
	}
}


void EMUtil::process_region_io(void *vdata, FILE * file,
							   int rw_mode, int image_index,
							   size_t mode_size, int nx, int ny, int nz,
							   const Region * area, bool need_flip, 
							   ImageType imgtype, int pre_row, int post_row)
{
	Assert(vdata != 0);
	Assert(file != 0);
	Assert(rw_mode == ImageIO::READ_ONLY ||
		   rw_mode == ImageIO::READ_WRITE ||
		   rw_mode == ImageIO::WRITE_ONLY);
	
	unsigned char * cdata = (unsigned char *)vdata;
	
	int x0 = 0;
	int y0 = 0;
	int z0 = nz > 1 ? 0 : image_index;

	int xlen = 0;
	int ylen = 0;
	int zlen = 0;
	get_region_dims(area, nx, &xlen, ny, &ylen, nz, &zlen);

	if (area) {
		x0 = static_cast < int >(area->origin[0]);
		y0 = static_cast < int >(area->origin[1]);
		if (nz > 1 && area->get_ndim() > 2) {
			z0 = static_cast < int >(area->origin[2]);
		}
	}

	size_t area_sec_size = xlen * ylen * mode_size;
	size_t img_row_size = nx * mode_size + pre_row + post_row;
	size_t area_row_size = xlen * mode_size;

	size_t x_pre_gap = x0 * mode_size;
	size_t x_post_gap = (nx - x0 - xlen) * mode_size;

	size_t y_pre_gap = y0 * img_row_size;
	size_t y_post_gap = (ny - y0 - ylen) * img_row_size;

	portable_fseek(file, img_row_size * ny * z0, SEEK_CUR);

	float nxlendata[1];
	int floatsize = (int) sizeof(float);
	nxlendata[0] = (float)(nx * floatsize);
	
	for (int k = 0; k < zlen; k++) {
		if (y_pre_gap > 0) {
			portable_fseek(file, y_pre_gap, SEEK_CUR);
		}
		int k2 = k * (int)area_sec_size;
		
		for (int j = 0; j < ylen; j++) {
			if (pre_row > 0) {
				if (imgtype == IMAGE_ICOS && rw_mode != ImageIO::READ_ONLY && !area) {
					fwrite(nxlendata, floatsize, 1, file);
				}
				else {
					portable_fseek(file, pre_row, SEEK_CUR);
				}
			}

			if (x_pre_gap > 0) {
				portable_fseek(file, x_pre_gap, SEEK_CUR);
			}

			int jj = j;
			if (need_flip) {
				jj = ylen - 1 - j;
			}

			if (rw_mode == ImageIO::READ_ONLY) {
				if (fread(&cdata[k2 + jj * area_row_size],
						  area_row_size, 1, file) != 1) {
                    int a = 1;
                    a = 1;
					throw ImageReadException("", "incomplete data read");
				}
			}
			else {
				if (fwrite(&cdata[k2 + jj * area_row_size],
						   area_row_size, 1, file) != 1) {
					throw ImageWriteException("", "incomplete data write");
				}
			}
				
			if (x_post_gap > 0) {                
				portable_fseek(file, x_post_gap, SEEK_CUR);
			}

			if (post_row > 0) {
				if (imgtype == IMAGE_ICOS && rw_mode != ImageIO::READ_ONLY && !area) {
					fwrite(nxlendata, floatsize, 1, file);
				}
				else {
					portable_fseek(file, post_row, SEEK_CUR);
				}
			}
		}

		if (y_post_gap > 0) {
			portable_fseek(file, y_post_gap, SEEK_CUR);
		}
	}
}


void EMUtil::dump_dict(const Dict & dict)
{
	vector < string > keys = dict.keys();
	vector < EMObject > values = dict.values();

	for (unsigned int i = 0; i < keys.size(); i++) {
		EMObject obj = values[i];
		if( !obj.is_null() ) {
			string val = obj.to_str();
	
			if (keys[i] == "datatype") {
				val = get_datatype_string((EMDataType) (int) obj);
			}
	
			fprintf(stdout, "%25s\t%s\n", keys[i].c_str(), val.c_str());
		}
	}
}


bool EMUtil::is_same_size(const EMData * const em1, const EMData * const em2)
{
	if (em1->get_xsize() == em2->get_xsize() &&
		em1->get_ysize() == em2->get_ysize() &&
		em1->get_zsize() == em2->get_zsize()) {
		return true;
	}
	return false;
}

bool EMUtil::is_complex_type(EMDataType datatype)
{
	if (datatype == EM_SHORT_COMPLEX ||
		datatype == EM_USHORT_COMPLEX ||
		datatype == EM_FLOAT_COMPLEX) {
		return true;
	}
	return false;
}


EMData *EMUtil::vertical_acf(const EMData * image, int maxdy)
{
	if (!image) {
		throw NullPointerException("NULL Image");
	}
	
	EMData *ret = new EMData();
	int nx = image->get_xsize();
	int ny = image->get_ysize();

	if (maxdy <= 1) {
		maxdy = ny / 8;
	}

	ret->set_size(nx, maxdy, 1);

	float *data = image->get_data();
	float *ret_data = ret->get_data();

	for (int x = 0; x < nx; x++) {
		for (int y = 0; y < maxdy; y++) {
			float dot = 0;
			for (int yy = maxdy; yy < ny - maxdy; yy++) {
				dot += data[x + (yy + y) * nx] * data[x + (yy - y) * nx];
			}
			ret_data[x + y * nx] = dot;
		}
	}

	ret->done_data();

	return ret;
}



EMData *EMUtil::make_image_median(const vector < EMData * >&image_list)
{
	if (image_list.size() == 0) {
		return 0;
	}

	EMData *image0 = image_list[0];
	int image0_nx = image0->get_xsize();
	int image0_ny = image0->get_ysize();
	int image0_nz = image0->get_zsize();
	int size = image0_nx * image0_ny * image0_nz;

	EMData *result = new EMData();

	result->set_size(image0_nx, image0_ny, image0_nz);

	float *dest = result->get_data();
	int nitems = static_cast < int >(image_list.size());
	float *srt = new float[nitems];
	float **src = new float *[nitems];

	for (int i = 0; i < nitems; i++) {
		src[i] = image_list[i]->get_data();
	}

	for (int i = 0; i < size; i++) {
		for (int j = 0; j < nitems; j++) {
			srt[j] = src[j][i];
		}

		for (int j = 0; j < nitems; j++) {
			for (int k = j + 1; k < nitems; k++) {
				if (srt[j] < srt[k]) {
					float v = srt[j];
					srt[j] = srt[k];
					srt[k] = v;
				}
			}
		}

		int l = nitems / 2;
		if (nitems < 3) {
			dest[i] = srt[l];
		}
		else {
			dest[i] = (srt[l] + srt[l + 1] + srt[l - 1]) / 3.0f;
		}
	}

	result->done_data();
	if( srt )
	{
		delete[]srt;
		srt = 0;
	}
	if( src )
	{
		delete[]src;
		src = 0;
	}

	result->update();

	return result;
}

bool EMUtil::is_same_ctf(const EMData * image1, const EMData * image2)
{
	if (!image1) {
		throw NullPointerException("image1 is NULL");
	}
	if (!image2) {
		throw NullPointerException("image2 is NULL");
	}
	
	Ctf *ctf1 = image1->get_ctf();
	Ctf *ctf2 = image2->get_ctf();

	if ((!ctf1 && !ctf2) && (image1->has_ctff() == false && image2->has_ctff() == false)) {
		return true;
	}

	if (ctf1 && ctf2) {
		return ctf1->equal(ctf2);
	}
	return false;
}

static int imgscore_cmp(const void *imgscore1, const void *imgscore2)
{
	Assert(imgscore1 != 0);
	Assert(imgscore2 != 0);
	
	float c = ((ImageScore *)imgscore1)->score - ((ImageScore *)imgscore2)->score;
	if (c<0) {
		return 1;
	}
	else if (c>0) {
		return -1;
	}
	return 0;
}

ImageSort::ImageSort(int nn)
{
	Assert(nn > 0);
	n = nn;
	image_scores = new ImageScore[n];
}

ImageSort::~ImageSort()
{
	if( image_scores )
	{
		delete [] image_scores;
		image_scores = 0;
	}
}

void ImageSort::sort()
{
	qsort(image_scores, n, sizeof(ImageScore), imgscore_cmp);

}

void ImageSort::set(int i, float score)
{
	Assert(i >= 0);
	image_scores[i] = ImageScore(i, score);
}

int ImageSort::get_index(int i) const
{
	Assert(i >= 0);
	return image_scores[i].index;
}


float ImageSort::get_score(int i) const
{
	Assert(i >= 0);
	return image_scores[i].score;
}


int ImageSort::size() const
{
	return n;
}


void EMUtil::process_ascii_region_io(float *data, FILE * file, int rw_mode,
									 int , size_t mode_size, int nx, int ny, int nz,
									 const Region * area, bool has_index_line,
									 int nitems_per_line, const char *outformat)
{
	Assert(data != 0);
	Assert(file != 0);
	Assert(rw_mode == ImageIO::READ_ONLY ||
		   rw_mode == ImageIO::READ_WRITE ||
		   rw_mode == ImageIO::WRITE_ONLY);
	
	int xlen = 0, ylen = 0, zlen = 0;
	EMUtil::get_region_dims(area, nx, &xlen, ny, &ylen, nz, &zlen);
	
	int x0 = 0;
	int y0 = 0;
	int z0 = 0;

	if (area) {
		x0 = (int)area->origin[0];
		y0 = (int)area->origin[1];
		z0 = (int)area->origin[2];
	}
	
	int nlines_per_sec = (nx *ny) / nitems_per_line;
	int nitems_last_line = (nx * ny) % nitems_per_line;
	if (nitems_last_line != 0) {
		nlines_per_sec++;
	}
	
	if (has_index_line) {
		nlines_per_sec++;
	}
	
	if (z0 > 0) {
		jump_lines(file, z0 * nlines_per_sec);
	}


	int nlines_pre_sec = (y0 * nx + x0) / nitems_per_line;
	int gap_nitems = nx - xlen;
	int ti = 0;
	int rlines = 0;
	
	for (int k = 0; k < zlen; k++) {		
		EMUtil::jump_lines(file, nlines_pre_sec+1);
		
		int head_nitems = (y0 * nx + x0) % nitems_per_line;
		int tail_nitems = 0;
		bool is_head_read = false;
		
		for (int j = 0; j < ylen; j++) {
			
			if (head_nitems > 0 && !is_head_read) {
				EMUtil::process_numbers_io(file, rw_mode, nitems_per_line, mode_size,
										   nitems_per_line-head_nitems,
										   nitems_per_line-1, data, &ti, outformat);
				rlines++;
			}
			
			EMUtil::process_lines_io(file, rw_mode, nitems_per_line,
									 mode_size, (xlen - head_nitems),
									 data, &ti, outformat);

			rlines += ((xlen - head_nitems)/nitems_per_line);
			
			tail_nitems = (xlen - head_nitems) % nitems_per_line;
			
			if ((gap_nitems + tail_nitems) > 0) {
				head_nitems = nitems_per_line -
					(gap_nitems + tail_nitems) % nitems_per_line;
			}
			else {
				head_nitems = 0;
			}
			
			is_head_read = false;
			
			if (tail_nitems > 0) {
				if ((gap_nitems < (nitems_per_line-tail_nitems)) &&
					(j != (ylen-1))) {
					EMUtil::exclude_numbers_io(file, rw_mode, nitems_per_line,
											   mode_size, tail_nitems, 
											   tail_nitems+gap_nitems-1, data, &ti, outformat);
					is_head_read = true;
					rlines++;
				}
				else {
					EMUtil::process_numbers_io(file, rw_mode, nitems_per_line, mode_size,
											   0, tail_nitems-1, data, &ti, outformat);
					rlines++;
				}
			}

			if (gap_nitems > (nitems_per_line-tail_nitems)) {
				int gap_nlines = (gap_nitems - (nitems_per_line-tail_nitems)) /
					nitems_per_line;
				if (gap_nlines > 0 && j != (ylen-1)) {
					EMUtil::jump_lines(file, gap_nlines);
				}
			}
		}
		
		int ytail_nitems = (ny-ylen-y0) * nx + (nx-xlen-x0) - (nitems_per_line-tail_nitems);
		EMUtil::jump_lines_by_items(file, ytail_nitems, nitems_per_line);
	}
}


void EMUtil::jump_lines_by_items(FILE * file, int nitems, int nitems_per_line)
{
	Assert(file);
	Assert(nitems_per_line > 0);
	
	if (nitems <= 0) {
		return;
	}
	
	int nlines = nitems / nitems_per_line;
	if ((nitems % nitems_per_line) != 0) {
		nlines++;
	}
	if (nlines > 0) {
		jump_lines(file, nlines);
	}
}


void EMUtil::jump_lines(FILE * file, int nlines)
{
	Assert(file);
	
	if (nlines > 0) {
		char line[MAXPATHLEN];
		for (int l = 0; l < nlines; l++) {
			if (!fgets(line, sizeof(line), file)) {
				Assert("read xplor file failed");
			}
		}
	}
}

void EMUtil::process_numbers_io(FILE * file, int rw_mode,
								int nitems_per_line, size_t mode_size, int start,
								int end, float *data, int *p_i, const char * outformat)
{
	Assert(file);
	Assert(start >= 0);
	Assert(start <= end);
	Assert(end <= nitems_per_line);
	Assert(data);
	Assert(p_i);
	Assert(outformat);
	
	char line[MAXPATHLEN];
	
	if (rw_mode == ImageIO::READ_ONLY) {
		if (!fgets(line, sizeof(line), file)) {
			Assert("read xplor file failed");
		}
		
		int nitems_in_line = (int) (strlen(line) / mode_size);
		Assert(end <= nitems_in_line);
		vector<float> d(nitems_in_line);
		char * pline = line;
		
		for (int i = 0; i < nitems_in_line; i++) {
			sscanf(pline, "%f", &d[i]);
			pline += (int)mode_size;
		}
		
		
		for (int i = start; i <= end; i++) {
			data[*p_i] = d[i];
			(*p_i)++;
		}
	}
	else {
		portable_fseek(file, mode_size * start, SEEK_CUR);
		for (int i = start; i <= end; i++) {
			fprintf(file, outformat, data[*p_i]);
			(*p_i)++;
		}
		
		portable_fseek(file, mode_size * (nitems_per_line - end-1)+1, SEEK_CUR);		
	}
}


void EMUtil::exclude_numbers_io(FILE * file, int rw_mode,
								int nitems_per_line, size_t mode_size, int start,
								int end, float * data, int *p_i, const char * outformat)
{
	Assert(file);
	Assert(mode_size > 0);
	Assert(start >= 0);
	Assert(end <= nitems_per_line);
	Assert(data);
	Assert(p_i);
	Assert(outformat);
	
	char line[MAXPATHLEN];
	
	if (rw_mode == ImageIO::READ_ONLY) {
		
		if (!fgets(line, sizeof(line), file)) {
			Assert("read xplor file failed");
		}

		int nitems_in_line =  (int) (strlen(line) / mode_size);
		Assert(end <= nitems_in_line);
		
		vector<float> d(nitems_in_line);
		char *pline = line;
		
		for (int i = 0; i < nitems_in_line; i++) {
			sscanf(pline, "%f", &d[i]);
			pline = pline + (int)mode_size;
		}
		
	
		for (int i = 0; i < start; i++) {
			data[*p_i] = d[i];
			(*p_i)++;
		}
		
		for (int i = end+1; i < nitems_in_line; i++) {
			data[*p_i] = d[i];
			(*p_i)++;
		}
	}
	else {
		for (int i = 0; i < start; i++) {
			fprintf(file, outformat, data[*p_i]);
			(*p_i)++;
		}

		portable_fseek(file, (end-start+1) * mode_size, SEEK_CUR);

		for (int i = end+1; i < nitems_per_line; i++) {
			fprintf(file, outformat, data[*p_i]);
			(*p_i)++;
		}
		portable_fseek(file, 1, SEEK_CUR);
	}
}

void EMUtil::process_lines_io(FILE * file, int rw_mode,
							  int nitems_per_line, size_t mode_size,
							  int nitems, float *data, int *p_i,
							  const char * outformat)
{
	Assert(file);
	Assert(data);
	Assert(p_i);

	if (nitems > 0) {
		int nlines = nitems / nitems_per_line;
		for (int i = 0; i < nlines; i++) {
			EMUtil::process_numbers_io(file, rw_mode, nitems_per_line, mode_size, 0, 
									   nitems_per_line-1, data, p_i, outformat);
		}
	}
}

vector<string> EMUtil::get_euler_names(const string & euler_type)
{
    vector<string> v;
    string b = "euler_";
    
    if (euler_type == "EMAN") {
        v.push_back(b + "alt");
        v.push_back(b + "az");
        v.push_back(b + "phi");
    }
    else if (euler_type == "MRC") {
        v.push_back(b + "theta");
        v.push_back(b + "phi");
        v.push_back(b + "omega");
    }
    else if (euler_type == "IMAGIC") {
        v.push_back(b + "alpha");
        v.push_back(b + "beta");
        v.push_back(b + "gamma");
    }
    else if (euler_type == "SPIDER") {
        v.push_back(b + "phi");
        v.push_back(b + "theta");
        v.push_back(b + "gamma");
    }
    else if (euler_type == "SPIN" ||
             euler_type == "SGIROT") {
        v.push_back(b + "q");
        v.push_back(b + "n1");
        v.push_back(b + "n2");
        v.push_back(b + "n3");
    }

    else if (euler_type == "QUATERNION") {
        v.push_back(b + "e0");
        v.push_back(b + "e1");
        v.push_back(b + "e2");
        v.push_back(b + "e3");
    }

    return v;
}
