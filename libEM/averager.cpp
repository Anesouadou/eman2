/**
 * $Id$
 */
#include "averager.h"
#include "emdata.h"
#include "log.h"
#include "util.h"
#include "xydata.h"
#include "ctf.h"


using namespace EMAN;

template <> Factory < Averager >::Factory()
{
	force_add(&ImageAverager::NEW);
	force_add(&IterationAverager::NEW);
	force_add(&WeightingAverager::NEW);
	force_add(&CtfCAverager::NEW);
	force_add(&CtfCWAverager::NEW);
	force_add(&CtfCWautoAverager::NEW);
}


void Averager::add_image_list(const vector<EMData*> & image_list)
{
	for (size_t i = 0; i < image_list.size(); i++) {
		add_image(image_list[i]);
	}
}

ImageAverager::ImageAverager()
	: result(0), sigma_image(0), nimg_n0(0), ignore0(0), nimg(0)
{
	
}


void ImageAverager::add_image(EMData * image)
{
	if (!image) {
		return;
	}

	if (nimg >= 1 && !EMUtil::is_same_size(image, result)) {
		LOGERR("%sAverager can only process same-size Image",
			   get_name().c_str());
		return;
	}
	
	nimg++;

	int nx = image->get_xsize();
	int ny = image->get_ysize();
	int nz = image->get_zsize();
	size_t image_size = nx * ny * nz;
	
	if (nimg == 1) {
		result = new EMData();
		result->set_size(nx, ny, nz);
		sigma_image = params.set_default("sigma", (EMData*)0);
		ignore0 = params["ignore0"];

		nimg_n0 = new int[image_size];
		for (size_t i = 0; i < image_size; i++) {
			nimg_n0[i] = 0;
		}
	}

	float *result_data = result->get_data();
	float *sigma_image_data = 0;
	if (sigma_image) {
		sigma_image->set_size(nx, ny, nz);
		sigma_image_data = sigma_image->get_data();
	}

	float * image_data = image->get_data();
	
	if (!ignore0) {
		for (size_t j = 0; j < image_size; j++) {		
			float f = image_data[j];			
			result_data[j] += f;
			if (sigma_image_data) {
				sigma_image_data[j] += f * f;
			}
		}
	}
	else {
		for (size_t j = 0; j < image_size; j++) {		
			float f = image_data[j];
			if (f) {
				result_data[j] += f;
				if (sigma_image_data) {
					sigma_image_data[j] += f * f;
				}
				nimg_n0[j]++;
			}
		}
	}
}

EMData * ImageAverager::finish()
{
	if (result && nimg > 1) {
		size_t image_size = result->get_xsize() * result->get_ysize() * result->get_zsize();
		float * result_data = result->get_data();
		
		if (!ignore0) {
			for (size_t j = 0; j < image_size; j++) {
				result_data[j] /= nimg;
			}

			if (sigma_image) {
				float * sigma_image_data = sigma_image->get_data();

				for (size_t j = 0; j < image_size; j++) {
					float f1 = sigma_image_data[j] / nimg;
					float f2 = result_data[j];
					sigma_image_data[j] = sqrt(f1 - f2 * f2);
				}

				sigma_image->done_data();
			}
		}
		else {
			for (size_t j = 0; j < image_size; j++) {
				result_data[j] /= nimg_n0[j];
			}
			if (sigma_image) {
				float * sigma_image_data = sigma_image->get_data();

				for (size_t j = 0; j < image_size; j++) {
					float f1 = sigma_image_data[j] / nimg_n0[j];
					float f2 = result_data[j];
					sigma_image_data[j] = sqrt(f1 - f2 * f2);
				}

				sigma_image->done_data();
			}
		}
		
		result->done_data();
		result->update();
	}

	delete [] nimg_n0;
	nimg_n0 = 0;
	
	return result;
}

#if 0
EMData *ImageAverager::average(const vector < EMData * >&image_list) const
{	
	if (image_list.size() == 0) {
		return 0;
	}

	EMData *sigma_image = params["sigma"];
	int ignore0 = params["ignore0"];

	EMData *image0 = image_list[0];

	int nx = image0->get_xsize();
	int ny = image0->get_ysize();
	int nz = image0->get_zsize();
	size_t image_size = nx * ny * nz;

	EMData *result = new EMData();
	result->set_size(nx, ny, nz);

	float *result_data = result->get_data();
	float *sigma_image_data = 0;

	if (sigma_image) {
		sigma_image->set_size(nx, ny, nz);
		sigma_image_data = sigma_image->get_data();
	}

	int c = 1;
	if (ignore0) {
		for (size_t j = 0; j < image_size; j++) {
			int g = 0;
			for (size_t i = 0; i < image_list.size(); i++) {
				float f = image_list[i]->get_value_at(j);
				if (f) {
					g++;
					result_data[j] += f;
					if (sigma_image_data) {
						sigma_image_data[j] += f * f;
					}
				}
			}
			if (g) {
				result_data[j] /= g;
			}
		}
	}
	else {
		float *image0_data = image0->get_data();
		if (sigma_image_data) {
			memcpy(sigma_image_data, image0_data, image_size * sizeof(float));

			for (size_t j = 0; j < image_size; j++) {
				sigma_image_data[j] *= sigma_image_data[j];
			}
		}

		image0->done_data();
		memcpy(result_data, image0_data, image_size * sizeof(float));

		for (size_t i = 1; i < image_list.size(); i++) {
			EMData *image = image_list[i];

			if (EMUtil::is_same_size(image, result)) {
				float *image_data = image->get_data();

				for (size_t j = 0; j < image_size; j++) {
					result_data[j] += image_data[j];
				}

				if (sigma_image_data) {
					for (size_t j = 0; j < image_size; j++) {
						sigma_image_data[j] += image_data[j] * image_data[j];
					}
				}

				image->done_data();
				c++;
			}
		}

		for (size_t j = 0; j < image_size; j++) {
			result_data[j] /= static_cast < float >(c);
		}
	}

	if (sigma_image_data) {
		for (size_t j = 0; j < image_size; j++) {
			float f1 = sigma_image_data[j] / c;
			float f2 = result_data[j];
			sigma_image_data[j] = sqrt(f1 - f2 * f2);
		}
	}

	result->done_data();

	if (sigma_image_data) {
		sigma_image->done_data();
	}

	result->update();
	return result;
}
#endif

IterationAverager::IterationAverager() : result(0), nimg(0)
{

}

void IterationAverager::add_image( EMData * image)
{
	if (!image) {
		return;
	}

	if (nimg >= 1 && !EMUtil::is_same_size(image, result)) {
		LOGERR("%sAverager can only process same-size Image",
							 get_name().c_str());
		return;
	}

	nimg++;
	
	int nx = image->get_xsize();
	int ny = image->get_ysize();
	int nz = image->get_zsize();
	size_t image_size = nx * ny * nz;

	if (nimg == 1) {
		result = new EMData();
		result->set_size(nx, ny, nz);
		sigma_image = new EMData();
		sigma_image->set_size(nx, ny, nz);
	}

	float *image_data = image->get_data();
	float *result_data = result->get_data();
	float *sigma_image_data = sigma_image->get_data();
	
	for (size_t j = 0; j < image_size; j++) {
		float f = image_data[j];
		result_data[j] += f;
		sigma_image_data[j] += f * f;
	}
	
	
}

EMData * IterationAverager::finish()
{
	if (nimg < 1) {
		return result;
	}
	
	int nx = result->get_xsize();
	int ny = result->get_ysize();
	int nz = result->get_zsize();
	size_t image_size = nx * ny * nz;
	
	float *result_data = result->get_data();
	float *sigma_image_data = sigma_image->get_data();
		
	for (size_t j = 0; j < image_size; j++) {
		result_data[j] /= nimg;
		float f1 = sigma_image_data[j] / nimg;
		float f2 = result_data[j];
		sigma_image_data[j] = sqrt(f1 - f2 * f2) / sqrt((float)nimg);
	}
		
	result->done_data();
	sigma_image->done_data();

	result->update();
	sigma_image->update();

	result->append_image("iter.hed");
	float sigma = sigma_image->get_attr("sigma");
	float *sigma_image_data2 = sigma_image->get_data();
	float *result_data2 = result->get_data();
	float *d2 = new float[nx * ny];
	size_t sec_size = nx * ny * sizeof(float);

	memcpy(d2, result_data2, sec_size);
	memcpy(sigma_image_data2, result_data2, sec_size);

	printf("Iter sigma=%f\n", sigma);

	for (int k = 0; k < 1000; k++) {
		for (int i = 1; i < nx - 1; i++) {
			for (int j = 1; j < ny - 1; j++) {
				int l = i + j * nx;
				float c1 = (d2[l - 1] + d2[l + 1] + d2[l - nx] + d2[l + nx]) / 4.0f - d2[l];
				float c2 = fabs(result_data2[l] - sigma_image_data2[l]) / sigma;
				result_data2[l] += c1 * Util::eman_erfc(c2) / 100.0f;
			}
		}

		memcpy(d2, result_data2, sec_size);
	}

	delete[]d2;
	d2 = 0;

	result->done_data();
	sigma_image->done_data();

	delete sigma_image;
	sigma_image = 0;

	result->update();
	result->append_image("iter.hed");

	
	return result;
}

#if 0
EMData *IterationAverager::average(const vector < EMData * >&image_list) const
{
	if (image_list.size() == 0) {
		return 0;
	}

	EMData *image0 = image_list[0];

	int nx = image0->get_xsize();
	int ny = image0->get_ysize();
	int nz = image0->get_zsize();
	int image_size = nx * ny * nz;

	EMData *result = new EMData();
	result->set_size(nx, ny, nz);

	EMData *sigma_image = new EMData();
	sigma_image->set_size(nx, ny, nz);

	float *image0_data = image0->get_data();
	float *result_data = result->get_data();
	float *sigma_image_data = sigma_image->get_data();

	memcpy(result_data, image0_data, image_size * sizeof(float));
	memcpy(sigma_image_data, image0_data, image_size * sizeof(float));

	for (int j = 0; j < image_size; j++) {
		sigma_image_data[j] *= sigma_image_data[j];
	}

	image0->done_data();

	int nc = 1;
	for (size_t i = 1; i < image_list.size(); i++) {
		EMData *image = image_list[i];

		if (EMUtil::is_same_size(image, result)) {
			float *image_data = image->get_data();

			for (int j = 0; j < image_size; j++) {
				result_data[j] += image_data[j];
				sigma_image_data[j] += image_data[j] * image_data[j];
			}

			image->done_data();
			nc++;
		}
	}

	float c = static_cast < float >(nc);
	for (int j = 0; j < image_size; j++) {
		float f1 = sigma_image_data[j] / c;
		float f2 = result_data[j] / c;
		sigma_image_data[j] = sqrt(f1 - f2 * f2) / sqrt(c);
	}


	for (int j = 0; j < image_size; j++) {
		result_data[j] /= c;
	}

	result->done_data();
	sigma_image->done_data();

	result->update();
	sigma_image->update();

	result->append_image("iter.hed");

	float sigma = sigma_image->get_attr("sigma");
	float *sigma_image_data2 = sigma_image->get_data();
	float *result_data2 = result->get_data();
	float *d2 = new float[nx * ny];
	size_t sec_size = nx * ny * sizeof(float);

	memcpy(d2, result_data2, sec_size);
	memcpy(sigma_image_data2, result_data2, sec_size);

	printf("Iter sigma=%f\n", sigma);

	for (int k = 0; k < 1000; k++) {
		for (int i = 1; i < nx - 1; i++) {
			for (int j = 1; j < ny - 1; j++) {
				int l = i + j * nx;
				float c1 = (d2[l - 1] + d2[l + 1] + d2[l - nx] + d2[l + nx]) / 4.0f - d2[l];
				float c2 = fabs(result_data2[l] - sigma_image_data2[l]) / sigma;
				result_data2[l] += c1 * Util::eman_erfc(c2) / 100.0f;
			}
		}

		memcpy(d2, result_data2, sec_size);
	}

	delete[]d2;
	d2 = 0;

	result->done_data();
	sigma_image->done_data();

	delete sigma_image;
	sigma_image = 0;

	result->update();
	result->append_image("iter.hed");

	return result;
}
#endif


CtfAverager::CtfAverager() :
	sf(0), curves(0), need_snr(false), outfile(0),
	result(0), image0_fft(0), image0_copy(0), snri(0), snrn(0),
	tdr(0), tdi(0), tn(0),
	filter(0), nimg(0), nx(0), ny(0), nz(0)
{

}

void CtfAverager::add_image(EMData * image)
{
	if (!image) {
		return;
	}

	if (nimg >= 1 && !EMUtil::is_same_size(image, result)) {
		LOGERR("%sAverager can only process same-size Image",
							 get_name().c_str());
		return;
	}

	if (image->get_zsize() != 1) {
		LOGERR("%sAverager: Only 2D images are currently supported",
							 get_name().c_str());
	}

	string alg_name = get_name();

	if (alg_name == "CtfCW" || alg_name == "CtfCWauto") {
		if (image->get_ctf() != 0 && !image->has_ctff()) {
			LOGERR("%sAverager: Attempted CTF Correction with no ctf parameters",
								 get_name().c_str());
		}
	}
	else {
		if (image->get_ctf() != 0) {
			LOGERR("%sAverager: Attempted CTF Correction with no ctf parameters",
								 get_name().c_str());
		}
	}
	
	nimg++;

		
	if (nimg == 1) {
		image0_fft = image->do_fft();
		
		nx = image0_fft->get_xsize();
		ny = image0_fft->get_ysize();
		nz = image0_fft->get_zsize();
		
		result = new EMData();
		result->set_size(nx - 2, ny, nz);

	
		if (alg_name == "Weighting" && curves) {
			if (!sf) {
				LOGWARN("CTF curve in file will contain relative, not absolute SNR!");
			}
			curves->set_size(Ctf::CTFOS * ny / 2, 3, 1);
			curves->to_zero();
		}


		if (alg_name == "CtfC") {
			filter = params["filter"];
			if (filter == 0) {
				filter = 22.0f;
			}
			float apix_y = image->get_attr_dict().get("apix_y");
			float ds = 1.0f / (apix_y * ny * Ctf::CTFOS);
			filter = 1.0f / (filter * ds);
		}
		
		if (alg_name == "CtfCWauto") {
			int nxy2 = nx * ny/2;
			
			snri = new float[ny / 2];
			snrn = new float[ny / 2];
			tdr = new float[nxy2];
			tdi = new float[nxy2];
			tn = new float[nxy2];
			
			for (int i = 0; i < ny / 2; i++) {
				snri[i] = 0;
				snrn[i] = 0;
			}

			for (int i = 0; i < nxy2; i++) {
				tdr[i] = 1;
				tdi[i] = 1;
				tn[i] = 1;
			}
		}

		image0_copy = image0_fft->copy_head();
		image0_copy->ap2ri();
		image0_copy->to_zero();
	}
	
	Ctf::CtfType curve_type = Ctf::CTF_ABS_AMP_S;
	if (alg_name == "CtfCWauto") {
		curve_type = Ctf::CTF_AMP_S;
	}
	
	float *src = image->get_data();
	image->ap2ri();
	Ctf *image_ctf = image->get_ctf();
	int ny2 = image->get_ysize();

	vector<float> ctf1 = image_ctf->compute_1d(ny2, curve_type);
		
	if (ctf1.size() == 0) {
		LOGERR("Unexpected CTF correction problem");
	}

	ctf.push_back(ctf1);

	vector<float> ctfn1;
	if (sf) {
		ctfn1 = image_ctf->compute_1d(ny2, Ctf::CTF_ABS_SNR, sf);
	}
	else {
		ctfn1 = image_ctf->compute_1d(ny2, Ctf::CTF_RELATIVE_SNR);
	}

	ctfn.push_back(ctfn1);

	if (alg_name == "CtfCWauto") {
		int j = 0;
		for (int y = 0; y < ny; y++) {
			for (int x = 0; x < nx / 2; x++, j += 2) {
				float r = hypot(x, y - ny / 2.0f);
				int l = static_cast < int >(Util::fast_floor(r));

				if (l >= 0 && l < ny / 2) {
					int k = y*nx/2 + x;
					tdr[k] *= src[j];
					tdi[k] *= src[j + 1];
					tn[k] *= (float)hypot(src[j], src[j + 1]);
				}
			}
		}
	}


	float *tmp_data = image0_copy->get_data();

	int j = 0;
	for (int y = 0; y < ny; y++) {
		for (int x = 0; x < nx / 2; x++, j += 2) {
			float r = Ctf::CTFOS * sqrt(x * x + (y - ny / 2.0f) * (y - ny / 2.0f));
			int l = static_cast < int >(Util::fast_floor(r));
			r -= l;

			float f = 0;
			if (l <= Ctf::CTFOS * ny / 2 - 2) {
				f = (ctf1[l] * (1 - r) + ctf1[l + 1] * r);
			}
			tmp_data[j] += src[j] * f;
			tmp_data[j + 1] += src[j + 1] * f;
		}
	}
	
	EMData *image_fft = image->do_fft();
	image_fft->done_data();

}

EMData * CtfAverager::finish()
{
	int j = 0;
	for (int y = 0; y < ny; y++) {
		for (int x = 0; x < nx / 2; x++, j += 2) {
			float r = (float) hypot(x, y - ny / 2.0f);
			int l = static_cast < int >(Util::fast_floor(r));
			if (l >= 0 && l < ny / 2) {
				int k = y*nx/2 + x;
				snri[l] += (tdr[k] + tdi[k]/tn[k]);
				snrn[l] += 1;
			}
		}
	}
	
	for (int i = 0; i < ny / 2; i++) {
		snri[i] *= nimg / snrn[i];
	}

	if (outfile != "") {
		Util::save_data(0, 1, snri, ny / 2, outfile);
	}
	

	float *cd = 0;
	if (curves) {
		cd = curves->get_data();
	}
	
	for (int i = 0; i < Ctf::CTFOS * ny / 2; i++) {
		float ctf0 = 0;
		for (int j = 0; j < nimg; j++) {
			ctf0 += ctfn[j][i];
			if (ctf[j][i] == 0) {
				ctf[j][i] = 1.0e-12f;
			}

			if (curves) {
				cd[i] += ctf[j][i] * ctfn[j][i];
				cd[i + Ctf::CTFOS * ny / 2] += ctfn[j][i];
				cd[i + 2 * Ctf::CTFOS * ny / 2] += ctfn[j][i];
			}
		}
		
		string alg_name = get_name();

		if (alg_name == "CtfCW" && need_snr) {
			snr[i] = ctf0;
		}

		float ctf1 = ctf0;
		if (alg_name == "CtfCWauto") {
			ctf1 = snri[i / Ctf::CTFOS];
		}

		if (ctf1 <= 0.0001f) {
			ctf1 = 0.1f;
		}

		if (alg_name == "CtfC") {
			for (int j = 0; j < nimg; j++) {
				ctf[j][i] = exp(-i * i / (filter * filter)) * ctfn[j][i] / (fabs(ctf[j][i]) * ctf1);
			}
		}
		else if (alg_name == "Weighting") {
			for (int j = 0; j < nimg; j++) {
				ctf[j][i] = ctfn[j][i] / ctf1;
			}
		}
		else if (alg_name == "CtfCW") {
			for (int j = 0; j < nimg; j++) {
				ctf[j][i] = (ctf1 / (ctf1 + 1)) * ctfn[j][i] / (ctf[j][i] * ctf1);
			}
		}
		else if (alg_name == "CtfCWauto") {
			for (int j = 0; j < nimg; j++) {
				ctf[j][i] = ctf1 * ctfn[j][i] / (fabs(ctf[j][i]) * ctf0);
			}
		}
	}


	if (curves) {
		for (int i = 0; i < Ctf::CTFOS * ny / 2; i++) {
			cd[i] /= cd[i + Ctf::CTFOS * ny / 2];
		}
		curves->done_data();
	}

	image0_copy->done_data();
	
	float *result_data = result->get_data();
	EMData *tmp_ift = image0_copy->do_ift();
	float *tmp_ift_data = tmp_ift->get_data();
	memcpy(result_data, tmp_ift_data, (nx - 2) * ny * sizeof(float));
	result->done_data();
	tmp_ift->done_data();

	delete image0_copy;
	image0_copy = 0;

	if (snri) {
		delete[]snri;
		snri = 0;
	}

	if (snrn) {
		delete[]snrn;
		snrn = 0;
	}

	result->update();

	delete [] snri;
	snri = 0;
	delete [] snrn;
	snrn = 0;
	delete [] tdr;
	tdr = 0;
	delete [] tdi;
	tdi = 0;
	delete [] tn;
	tn = 0;
	
	return result;
}

#if 0
EMData *CtfAverager::average(const vector < EMData * >&image_list) const
{
	if (image_list.size() == 0) {
		return 0;
	}

	EMData *image0 = image_list[0];
	if (image0->get_zsize() != 1) {
		LOGERR("Only 2D images are currently supported");
		return 0;
	}

	string alg_name = get_name();

	if (alg_name == "CtfCW" || alg_name == "CtfCWauto") {
		if (image0->get_ctf() != 0 && !image0->has_ctff()) {
			LOGERR("Attempted CTF Correction with no ctf parameters");
			return 0;
		}
	}
	else {
		if (image0->get_ctf() != 0) {
			LOGERR("Attempted CTF Correction with no ctf parameters");
			return 0;
		}
	}

	size_t num_images = image_list.size();
	vector < float >*ctf = new vector < float >[num_images];
	vector < float >*ctfn = new vector < float >[num_images];
	float **src = new float *[num_images];

	Ctf::CtfType curve_type = Ctf::CTF_ABS_AMP_S;
	if (alg_name == "CtfCWauto") {
		curve_type = Ctf::CTF_AMP_S;
	}

	for (size_t i = 0; i < num_images; i++) {
		EMData *image = image_list[i]->do_fft();
		image->ap2ri();
		src[i] = image->get_data();
		Ctf *image_ctf = image->get_ctf();
		int ny = image->get_ysize();
		ctf[i] = image_ctf->compute_1d(ny, curve_type);

		if (ctf[i].size() == 0) {
			LOGERR("Unexpected CTF correction problem");
			return 0;
		}

		if (sf) {
			ctfn[i] = image_ctf->compute_1d(ny, Ctf::CTF_ABS_SNR, sf);
		}
		else {
			ctfn[i] = image_ctf->compute_1d(ny, Ctf::CTF_RELATIVE_SNR);
		}
	}

	EMData *image0_fft = image0->do_fft();

	int nx = image0_fft->get_xsize();
	int ny = image0_fft->get_ysize();
	int nz = image0_fft->get_zsize();

	EMData *result = new EMData();
	result->set_size(nx - 2, ny, nz);

	float *cd = 0;
	if (alg_name == "Weighting" && curves) {
		if (!sf) {
			LOGWARN("CTF curve in file will contain relative, not absolute SNR!");
		}
		curves->set_size(Ctf::CTFOS * ny / 2, 3, 1);
		curves->to_zero();
		cd = curves->get_data();
	}

	float filter = 0;
	if (alg_name == "CtfC") {
		filter = params["filter"];
		if (filter == 0) {
			filter = 22.0f;
		}
		float apix_y = image0->get_attr_dict().get("apix_y");
		float ds = 1.0f / (apix_y * ny * Ctf::CTFOS);
		filter = 1.0f / (filter * ds);
	}

	float *snri = 0;
	float *snrn = 0;

	if (alg_name == "CtfCWauto") {
		snri = new float[ny / 2];
		snrn = new float[ny / 2];

		for (int i = 0; i < ny / 2; i++) {
			snri[i] = 0;
			snrn[i] = 0;
		}

		int j = 0;
		for (int y = 0; y < ny; y++) {
			for (int x = 0; x < nx / 2; x++, j += 2) {
				float r = hypot(x, y - ny / 2.0f);
				int l = static_cast < int >(Util::fast_floor(r));

				if (l >= 0 && l < ny / 2) {
					float tdr = 1;
					float tdi = 1;
					float tn = 1;

					for (size_t i = 0; i < num_images; i++) {
						tdr *= src[i][j];
						tdi *= src[i][j + 1];
						tn *= hypot(src[i][j], src[i][j + 1]);
					}

					tdr += tdi / tn;
					snri[l] += tdr;
					snrn[l] += 1;
				}
			}
		}

		for (int i = 0; i < ny / 2; i++) {
			snri[i] *= num_images / snrn[i];
		}
		if (outfile != "") {
			Util::save_data(0, 1, snri, ny / 2, outfile);
		}
	}

	for (int i = 0; i < Ctf::CTFOS * ny / 2; i++) {
		float ctf0 = 0;
		for (size_t j = 0; j < num_images; j++) {
			ctf0 += ctfn[j][i];
			if (ctf[j][i] == 0) {
				ctf[j][i] = 1.0e-12;
			}

			if (curves) {
				cd[i] += ctf[j][i] * ctfn[j][i];
				cd[i + Ctf::CTFOS * ny / 2] += ctfn[j][i];
				cd[i + 2 * Ctf::CTFOS * ny / 2] += ctfn[j][i];
			}
		}

		if (alg_name == "CtfCW" && need_snr) {
			snr[i] = ctf0;
		}

		float ctf1 = ctf0;
		if (alg_name == "CtfCWauto") {
			ctf1 = snri[i / Ctf::CTFOS];
		}

		if (ctf1 <= 0.0001f) {
			ctf1 = 0.1f;
		}

		if (alg_name == "CtfC") {
			for (size_t j = 0; j < num_images; j++) {
				ctf[j][i] = exp(-i * i / (filter * filter)) * ctfn[j][i] / (fabs(ctf[j][i]) * ctf1);
			}
		}
		else if (alg_name == "Weighting") {
			for (size_t j = 0; j < num_images; j++) {
				ctf[j][i] = ctfn[j][i] / ctf1;
			}
		}
		else if (alg_name == "CtfCW") {
			for (size_t j = 0; j < num_images; j++) {
				ctf[j][i] = (ctf1 / (ctf1 + 1)) * ctfn[j][i] / (ctf[j][i] * ctf1);
			}
		}
		else if (alg_name == "CtfCWauto") {
			for (size_t j = 0; j < num_images; j++) {
				ctf[j][i] = ctf1 * ctfn[j][i] / (fabs(ctf[j][i]) * ctf0);
			}
		}
	}


	if (curves) {
		for (int i = 0; i < Ctf::CTFOS * ny / 2; i++) {
			cd[i] /= cd[i + Ctf::CTFOS * ny / 2];
		}
		curves->done_data();
	}

	EMData *image0_copy = image0_fft->copy_head();
	image0_copy->ap2ri();

	float *tmp_data = image0_copy->get_data();

	int j = 0;
	for (int y = 0; y < ny; y++) {
		for (int x = 0; x < nx / 2; x++, j += 2) {
			float r = Ctf::CTFOS * sqrt(x * x + (y - ny / 2.0f) * (y - ny / 2.0f));
			int l = static_cast < int >(Util::fast_floor(r));
			r -= l;

			tmp_data[j] = 0;
			tmp_data[j + 1] = 0;

			for (size_t i = 0; i < num_images; i++) {
				float f = 0;
				if (l <= Ctf::CTFOS * ny / 2 - 2) {
					f = (ctf[i][l] * (1 - r) + ctf[i][l + 1] * r);
				}
				tmp_data[j] += src[i][j] * f;
				tmp_data[j + 1] += src[i][j + 1] * f;
			}
		}
	}

	image0_copy->done_data();

	float *result_data = result->get_data();
	EMData *tmp_ift = image0_copy->do_ift();
	float *tmp_ift_data = tmp_ift->get_data();
	memcpy(result_data, tmp_ift_data, (nx - 2) * ny * sizeof(float));
	result->done_data();
	tmp_ift->done_data();

	delete image0_copy;
	image0_copy = 0;

	for (size_t i = 0; i < num_images; i++) {
		EMData *img = image_list[i]->do_fft();
		img->done_data();
	}

	delete[]src;
	src = 0;

	delete[]ctf;
	ctf = 0;

	delete[]ctfn;
	ctfn = 0;

	if (snri) {
		delete[]snri;
		snri = 0;
	}

	if (snrn) {
		delete[]snrn;
		snrn = 0;
	}

	result->update();
	return result;
}
#endif


void dump_averagers()
{
	dump_factory < Averager > ();
}
