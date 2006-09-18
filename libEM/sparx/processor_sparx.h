/**
 * $Id$
 */

/*
 * Author: Pawel A.Penczek, 09/09/2006 (Pawel.A.Penczek@uth.tmc.edu)
 * Copyright (c) 2000-2006 The University of Texas - Houston Medical School
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
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
 * GNU General Public License for more details.
 *
 * You should have received a copy of the GNU General Public License
 * along with this program; if not, write to the Free Software
 * Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307  USA
 *
 */
 
#ifndef eman_processor_sparx_h__
#define eman_processor_sparx_h__ 1

namespace EMAN
{

        
	/** mirror an image
	 * @param axis  ''x', 'y', or 'z' axis, means mirror by changing the sign of the respective axis;
	 */
	class MirrorProcessor:public Processor
	{ 
		
	  public:
		void process_inplace(EMData * image);

		string get_name() const
		{
			return "mirror";
		}

		static Processor *NEW()
		{
			return new MirrorProcessor();
		}

		TypeDict get_param_types() const
		{
			TypeDict d;
			d.put("axis", EMObject::STRING, "'x', 'y', or 'z' axis, means mirror by changing the sign of the respective axis;");
			return d;
		}

		string get_desc() const
		{
			return "mirror an image.";
		}
		
	};



	class NewFourierProcessor:public Processor
	{
	  public:
		//virtual void process_inplace(EMData * image);
		
		static string get_group_desc()
		{
			return "Fourier Filter Processors are frequency domain processors. The input image can be either real or Fourier, and the output processed image format corresponds to that of the input file. FourierFilter class is the base class of fourier space processors. The processors can be either low-pass, high-pass, band-pass, or homomorphic. The processor parameters are in absolute frequency units, valid range is ]0,0.5], where 0.5 is Nyquist freqeuncy. ";
		}
	};
	
	/**Lowpass top-hat filter processor applied in Fourier space.
	 * @param cutoff_frequency Absolute [0,0.5] cut-off frequency.
	 */
	class NewLowpassTopHatProcessor:public NewFourierProcessor
	{
	  public:
		string get_name() const
		{ return "filter.lowpass.tophat"; }
		static Processor *NEW()
		{ return new NewLowpassTopHatProcessor(); }
		string get_desc() const
		{
			return "Lowpass top-hat filter processor applied in Fourier space.";
		}
		void process_inplace(EMData* image) {
			params["filter_type"] = TOP_HAT_LOW_PASS;
			EMFourierFilterInPlace(image, params); 
		}
		TypeDict get_param_types() const
		{
			TypeDict d;
			d.put("cutoff_frequency", EMObject::FLOAT, "Absolute [0,0.5] cut-off frequency.");
			return d;
		}
		
	};
	
	/** Highpass top-hat filter applied in Fourier space.
	 * @param cutoff_frequency Absolute [0,0.5] cut-off frequency.
	 */
	class NewHighpassTopHatProcessor:public NewFourierProcessor
	{
	  public:
		string get_name() const
		{ return "filter.highpass.tophat"; }
		static Processor *NEW()
		{ return new NewHighpassTopHatProcessor(); }
		string get_desc() const
		{
			return "Highpass top-hat filter applied in Fourier space.";
		}
		void process_inplace(EMData* image) {
			params["filter_type"] = TOP_HAT_HIGH_PASS;
			EMFourierFilterInPlace(image, params); 
		}
		TypeDict get_param_types() const
		{
			TypeDict d;
			d.put("cutoff_frequency", EMObject::FLOAT, "Absolute [0,0.5] cut-off frequency.");
			return d;
		}
	};
	
	/**Bandpass top-hat filter processor applied in Fourier space.
	 *@param low_cutoff_frequency Absolute [0,0.5] low cut-off frequency.
	 *@param high_cutoff_frequency Absolute [0,0.5] high cut-off frequency.
	 */
	class NewBandpassTopHatProcessor:public NewFourierProcessor
	{
	  public:
		string get_name() const
		{ return "filter.bandpass.tophat"; }
		static Processor *NEW()
		{ return new NewBandpassTopHatProcessor(); }
		string get_desc() const
		{
			return "Bandpass top-hat filter processor applied in Fourier space.";
		}
		void process_inplace(EMData* image) {
			params["filter_type"] = TOP_HAT_BAND_PASS;
			EMFourierFilterInPlace(image, params); 
		}
		TypeDict get_param_types() const
		{
			TypeDict d;
			d.put("low_cutoff_frequency", EMObject::FLOAT, "Absolute [0,0.5] low cut-off frequency.");
			d.put("high_cutoff_frequency", EMObject::FLOAT, "Absolute [0,0.5] high cut-off frequency.");
			return d;
		}
	};
	
	/**Homomorphic top-hat filter processor applied in Fourier space.
	 *@param low_cutoff_frequency Absolute [0,0.5] low cut-off frequency.
	 *@param high_cutoff_frequency Absolute [0,0.5] high cut-off frequency.
	 *@param value_at_zero_frequency Value at zero frequency.
	 */
	class NewHomomorphicTopHatProcessor:public NewFourierProcessor
	{
	  public:
		string get_name() const
		{ return "filter.homomorphic.tophat"; }
		static Processor *NEW()
		{ return new NewHomomorphicTopHatProcessor(); }
		string get_desc() const
		{
			return "Homomorphic top-hat filter processor applied in Fourier space.";
		}
		void process_inplace(EMData* image) {
			params["filter_type"] = TOP_HOMOMORPHIC;
			EMFourierFilterInPlace(image, params); 
		}
		TypeDict get_param_types() const
		{
			TypeDict d;
			d.put("low_cutoff_frequency", EMObject::FLOAT, "Absolute [0,0.5] low cut-off frequency.");
			d.put("high_cutoff_frequency", EMObject::FLOAT, "Absolute [0,0.5] high cut-off frequency.");
			d.put("value_at_zero_frequency", EMObject::FLOAT, "Value at zero frequency.");
			return d;
		}
	};
	
	/**Lowpass Gauss filter processor applied in Fourier space.
	 * @param sigma Gaussian sigma.
	 */
	class NewLowpassGaussProcessor:public NewFourierProcessor
	{
	  public:
		string get_name() const
		{ return "filter.lowpass.gauss"; }
		static Processor *NEW()
		{ return new NewLowpassGaussProcessor(); }
		string get_desc() const
		{
			return "Lowpass Gauss filter processor applied in Fourier space.";
		}
		void process_inplace(EMData* image) {
			params["filter_type"] = GAUSS_LOW_PASS;
			EMFourierFilterInPlace(image, params); 
		}
		TypeDict get_param_types() const
		{
			TypeDict d;
			d.put("sigma", EMObject::FLOAT, "Gaussian sigma.");
			return d;
		}
	};
	
	/**Highpass Gauss filter processor applied in Fourier space.
	 * @param sigma Gaussian sigma.	
	 */
	class NewHighpassGaussProcessor:public NewFourierProcessor
	{
	  public:
		string get_name() const
		{ return "filter.highpass.gauss"; }
		static Processor *NEW()
		{ return new NewHighpassGaussProcessor(); }
		string get_desc() const
		{
			return "Highpass Gauss filter processor applied in Fourier space.";
		}
		void process_inplace(EMData* image) {
			params["filter_type"] = GAUSS_HIGH_PASS;
			EMFourierFilterInPlace(image, params); 
		}
		TypeDict get_param_types() const
		{
			TypeDict d;
			d.put("sigma", EMObject::FLOAT, "Gaussian sigma.");
			return d;
		}
	};
	
	/**Bandpass Gauss filter processor applied in Fourier space.
	 * @param sigma Gaussian sigma.
	 * @param center Gaussian center.
	 */
	class NewBandpassGaussProcessor:public NewFourierProcessor
	{
	  public:
		string get_name() const
		{ return "filter.bandpass.gauss"; }
		static Processor *NEW()
		{ return new NewBandpassGaussProcessor(); }
		string get_desc() const
		{
			return "Bandpass Gauss filter processor applied in Fourier space.";
		}
		void process_inplace(EMData* image) {
			params["filter_type"] = GAUSS_BAND_PASS;
			EMFourierFilterInPlace(image, params); 
		}
		TypeDict get_param_types() const
		{
			TypeDict d;
			d.put("sigma", EMObject::FLOAT, "Gaussian sigma.");
			d.put("center", EMObject::FLOAT, "Gaussian center.");
			return d;
		}
	};
	
	/**Homomorphic Gauss filter processor applied in Fourier space.
	 * @param sigma Gaussian sigma.
	 * @param value_at_zero_frequency Value at zero frequency.
	 */
	class NewHomomorphicGaussProcessor:public NewFourierProcessor
	{
	  public:
		string get_name() const
		{ return "filter.homomorphic.gauss"; }
		static Processor *NEW()
		{ return new NewHomomorphicGaussProcessor(); }
		string get_desc() const
		{
			return "Homomorphic Gauss filter processor applied in Fourier space.";
		}
		void process_inplace(EMData* image) {
			params["filter_type"] = GAUSS_HOMOMORPHIC;
			EMFourierFilterInPlace(image, params); 
		}
		TypeDict get_param_types() const
		{
			TypeDict d;
			d.put("sigma", EMObject::FLOAT, "Gaussian sigma.");
			d.put("value_at_zero_frequency", EMObject::FLOAT, "Value at zero frequency.");
			return d;
		}
	};
	
	/**Divide by a Gaussian in Fourier space.
	 * @param sigma Gaussian sigma.
	 */
	class NewInverseGaussProcessor:public NewFourierProcessor
	{
	  public:
		string get_name() const
		{ return "filter.gaussinverse"; }
		static Processor *NEW()
		{ return new NewInverseGaussProcessor(); }
		string get_desc() const
		{
			return "Divide by a Gaussian in Fourier space.";
		}
		void process_inplace(EMData* image) {
			params["filter_type"] = GAUSS_INVERSE;
			EMFourierFilterInPlace(image, params); 
		}
		TypeDict get_param_types() const
		{
			TypeDict d;
			d.put("sigma", EMObject::FLOAT, "Gaussian sigma.");
			return d;
		}
	};
	
	/**Shift by phase multiplication in Fourier space.
	 */
	class SHIFTProcessor:public NewFourierProcessor
	{
	  public:
		string get_name() const
		{ return "filter.shift"; }
		static Processor *NEW()
		{ return new SHIFTProcessor(); }
		string get_desc() const
		{
			return "Shift by phase multiplication in Fourier space.";
		}
		void process_inplace(EMData* image) {
			params["filter_type"] = SHIFT;
			EMFourierFilterInPlace(image, params); 
		}
		TypeDict get_param_types() const
		{
			TypeDict d;
			d.put("x_shift", EMObject::FLOAT, "Shift x");
			d.put("y_shift", EMObject::FLOAT, "Shift y");
			d.put("z_shift", EMObject::FLOAT, "Shift z");
			return d;
		}
	};
	
	/**Divide by a Kaiser-Bessel I0 func in Fourier space.
	 */
	class InverseKaiserI0Processor:public NewFourierProcessor
	{
	  public:
		string get_name() const
		{ return "filter.kaiser_io_inverse"; }
		static Processor *NEW()
		{ return new InverseKaiserI0Processor(); }
		string get_desc() const
		{
			return "Divide by a Kaiser-Bessel I0 func in Fourier space.";
		}
		void process_inplace(EMData* image) {
			params["filter_type"] = KAISER_I0_INVERSE;
			EMFourierFilterInPlace(image, params); 
		}
	};
	
	/**Divide by a Kaiser-Bessel Sinh func in Fourier space.
	 */
	class InverseKaiserSinhProcessor:public NewFourierProcessor
	{
	  public:
		string get_name() const
		{ return "filter.kaisersinhinverse"; }
		static Processor *NEW()
		{ return new InverseKaiserSinhProcessor(); }
		string get_desc() const
		{
			return "Divide by a Kaiser-Bessel Sinh func in Fourier space.";
		}
		void process_inplace(EMData* image) {
			params["filter_type"] = KAISER_SINH_INVERSE;
			EMFourierFilterInPlace(image, params); 
		}
	};
	
	/**Filter with tabulated data in Fourier space.
	 *@param table Tabulated filter data.
	 */
	class NewRadialTableProcessor:public NewFourierProcessor
	{
	  public:
		string get_name() const
		{ return "filter.radialtable"; }
		static Processor *NEW()
		{ return new NewRadialTableProcessor(); }
		string get_desc() const
		{
			return "Filter with tabulated data in Fourier space.";
		}
		void process_inplace(EMData* image) {
			params["filter_type"] = RADIAL_TABLE;
			EMFourierFilterInPlace(image, params); 
		}
		TypeDict get_param_types() const
		{
			TypeDict d;
			d.put("table", EMObject::FLOATARRAY, "Tabulated filter data.");
			return d;
		}
	};
	
	/**Lowpass Butterworth filter processor applied in Fourier space.
	 *@param low_cutoff_frequency Absolute [0,0.5] low cut-off frequency.
	 *@param high_cutoff_frequency Absolute [0,0.5] high cut-off frequency.
	 */
	class NewLowpassButterworthProcessor:public NewFourierProcessor
	{
	  public:
		string get_name() const
		{ return "filter.lowpass.butterworth"; }
		static Processor *NEW()
		{ return new NewLowpassButterworthProcessor(); }
		string get_desc() const
		{
			return "Lowpass Butterworth filter processor applied in Fourier space.";
		}
		void process_inplace(EMData* image) {
			params["filter_type"] = BUTTERWORTH_LOW_PASS;
			EMFourierFilterInPlace(image, params); 
		}
		TypeDict get_param_types() const
		{
			TypeDict d;
			d.put("low_cutoff_frequency", EMObject::FLOAT, "Absolute [0,0.5] low cut-off frequency.");
			d.put("high_cutoff_frequency", EMObject::FLOAT, "Absolute [0,0.5] high cut-off frequency.");
			return d;
		}
	};
	
	/**Highpass Butterworth filter processor applied in Fourier space.
	 *@param low_cutoff_frequency Absolute [0,0.5] low cut-off frequency.
	 *@param high_cutoff_frequency Absolute [0,0.5] high cut-off frequency.
	 */
	class NewHighpassButterworthProcessor:public NewFourierProcessor
	{
	  public:
		string get_name() const
		{ return "filter.highpass.butterworth"; }
		static Processor *NEW()
		{ return new NewHighpassButterworthProcessor(); }
		string get_desc() const
		{
			return "Highpass Butterworth filter processor applied in Fourier space.";
		}
		void process_inplace(EMData* image) {
			params["filter_type"] = BUTTERWORTH_HIGH_PASS;
			EMFourierFilterInPlace(image, params); 
		}
		TypeDict get_param_types() const
		{
			TypeDict d;
			d.put("low_cutoff_frequency", EMObject::FLOAT, "Absolute [0,0.5] low cut-off frequency.");
			d.put("high_cutoff_frequency", EMObject::FLOAT, "Absolute [0,0.5] high cut-off frequency.");
			return d;
		}
	};
	
	/**Homomorphic Butterworth filter processor applied in Fourier space.
	 *@param low_cutoff_frequency Absolute [0,0.5] low cut-off frequency.
	 *@param high_cutoff_frequency Absolute [0,0.5] high cut-off frequency.
	 *@param value_at_zero_frequency Value at zero frequency.
	 */
	class NewHomomorphicButterworthProcessor:public NewFourierProcessor
	{
	  public:
		string get_name() const
		{ return "filter.homomorphic.butterworth"; }
		static Processor *NEW()
		{ return new NewHomomorphicButterworthProcessor(); }
		string get_desc() const
		{
			return "Homomorphic Butterworth filter processor applied in Fourier space.";
		}
		void process_inplace(EMData* image) {
			params["filter_type"] = BUTTERWORTH_HOMOMORPHIC;
			EMFourierFilterInPlace(image, params); 
		}
		TypeDict get_param_types() const
		{
			TypeDict d;
			d.put("low_cutoff_frequency", EMObject::FLOAT, "Absolute [0,0.5] low cut-off frequency.");
			d.put("high_cutoff_frequency", EMObject::FLOAT, "Absolute [0,0.5] high cut-off frequency.");
			d.put("value_at_zero_frequency", EMObject::FLOAT, "Value at zero frequency.");
			return d;
		}
	};
	
	/**Lowpass tanh filter processor applied in Fourier space.
	 *@param cutoff_frequency Absolute [0,0.5] cut-off frequency.
	 *@param fall_off Tanh decay rate.
	 */
	class NewLowpassTanhProcessor:public NewFourierProcessor
	{
	  public:
		string get_name() const
		{ return "filter.lowpass.tanh"; }
		static Processor *NEW()
		{ return new NewLowpassTanhProcessor(); }
		string get_desc() const
		{
			return "Lowpass tanh filter processor applied in Fourier space.";
		}
		void process_inplace(EMData* image) {
			params["filter_type"] = TANH_LOW_PASS;
			EMFourierFilterInPlace(image, params); 
		}
		TypeDict get_param_types() const
		{
			TypeDict d;
			d.put("cutoff_frequency", EMObject::FLOAT, "Absolute [0,0.5] cut-off frequency.");
			d.put("fall_off", EMObject::FLOAT, "Tanh decay rate.");
			return d;
		}
	};
	
	/**Highpass tanh filter processor applied in Fourier space.
	 *@param cutoff_frequency Absolute [0,0.5] cut-off frequency.
	 *@param fall_off Tanh decay rate.
	 */
	class NewHighpassTanhProcessor:public NewFourierProcessor
	{
	  public:
		string get_name() const
		{ return "filter.highpass.tanh"; }
		static Processor *NEW()
		{ return new NewHighpassTanhProcessor(); }
		string get_desc() const
		{
			return "Highpass tanh filter processor applied in Fourier space.";
		}
		void process_inplace(EMData* image) {
			params["filter_type"] = TANH_HIGH_PASS;
			EMFourierFilterInPlace(image, params); 
		}
		TypeDict get_param_types() const
		{
			TypeDict d;
			d.put("cutoff_frequency", EMObject::FLOAT, "Absolute [0,0.5] cut-off frequency.");
			d.put("fall_off", EMObject::FLOAT, "Tanh decay rate.");
			return d;
		}
	};
	
	/**Homomorphic Tanh processor applied in Fourier space
	 *@param cutoff_frequency Absolute [0,0.5] cut-off frequency.
	 *@param fall_off Tanh decay rate.
	 *@param value_at_zero_frequency Value at zero frequency.
	 */
	class NewHomomorphicTanhProcessor:public NewFourierProcessor
	{
	  public:
		string get_name() const
		{ return "filter.homomorphic.tanh"; }
		static Processor *NEW()
		{ return new NewHomomorphicTanhProcessor(); }
		string get_desc() const
		{
			return "Homomorphic Tanh processor applied in Fourier space";
		}
		void process_inplace(EMData* image) {
			params["filter_type"] = TANH_HOMOMORPHIC;
			EMFourierFilterInPlace(image, params); 
		}
		TypeDict get_param_types() const
		{
			TypeDict d;
			d.put("cutoff_frequency", EMObject::FLOAT, "Absolute [0,0.5] cut-off frequency.");
			d.put("fall_off", EMObject::FLOAT, "Tanh decay rate.");
			d.put("value_at_zero_frequency", EMObject::FLOAT, "Value at zero frequency.");
			return d;
		}
	};
	
	/**Bandpass tanh processor applied in Fourier space.
	 *@param low_cutoff_frequency Absolute [0,0.5] low cut-off frequency.
	 *@param Low_fall_off Tanh low decay rate.	 
	 *@param high_cutoff_frequency Absolute [0,0.5] high cut-off frequency.
	 *@param high_fall_off Tanh high decay rate.
	 *@param fall_off Tanh decay rate.
	 */
	class NewBandpassTanhProcessor:public NewFourierProcessor
	{
	  public:
		string get_name() const
		{ return "filter.bandpass.tanh"; }
		static Processor *NEW()
		{ return new NewBandpassTanhProcessor(); }
		string get_desc() const
		{
			return "Bandpass tanh processor applied in Fourier space.";
		}
		void process_inplace(EMData* image) {
			params["filter_type"] = TANH_BAND_PASS;
			EMFourierFilterInPlace(image, params); 
		}
		TypeDict get_param_types() const
		{
			TypeDict d;
			d.put("low_cutoff_frequency", EMObject::FLOAT, "Absolute [0,0.5] low cut-off frequency.");
			d.put("Low_fall_off", EMObject::FLOAT, "Tanh low decay rate.");
			d.put("high_cutoff_frequency", EMObject::FLOAT, "Absolute [0,0.5] high cut-off frequency.");
			d.put("high_fall_off", EMObject::FLOAT, "Tanh high decay rate.");
			d.put("fall_off", EMObject::FLOAT, "Tanh decay rate.");
			return d;
		}
	};

	class CTF_Processor:public NewFourierProcessor
	{
	  public:
		string get_name() const
		{ return "filter.CTF_"; }
		static Processor *NEW()
		{ return new CTF_Processor(); }
		string get_desc() const
		{
			return "CTF_ is applied in Fourier image.";
		}
		void process_inplace(EMData* image) {
			params["filter_type"] = CTF_;
			EMFourierFilterInPlace(image, params); 
		}
		TypeDict get_param_types() const
		{
			TypeDict d;
			d.put("defocus", EMObject::FLOAT, "defocus value in Angstrom.");
			d.put("cs", EMObject::FLOAT, "cs in CM.");
			d.put("voltage", EMObject::FLOAT, "voltage in Kv.");
			d.put("ps", EMObject::FLOAT, "pixel size.");
			d.put("b_factor", EMObject::FLOAT, "Gaussian like evelope function (b_factor).");
			d.put("wgh", EMObject::FLOAT, "Amplitude contrast ratio.");
			d.put("sign", EMObject::FLOAT, "Sign of Contrast transfer function,and use -1 to compensate.");
			d.put("npow", EMObject::FLOAT, "power of transfer function.");
			return d;
		}
	};
}

#endif	//eman_processor_sparx_h__
