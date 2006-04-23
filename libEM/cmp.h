/**
 * $Id$
 */
#ifndef eman_cmp__h__
#define eman_cmp__h__ 1


#include "emobject.h"

namespace EMAN
{

	class EMData;
	class Transform3D;

	/** Cmp class defines image comparison method. Using default
	 * arguments, smaller values indicate more similar images.
	 *
	 * Cmp class is the base comparison class. Each specific
     * comparison class is a subclass of Cmp, and must have a unique
     * name. The name is used to  create a new Cmp instance or call a Cmp.
	 *
	 * All Cmp classes in EMAN are managed by a Factory pattern. So 
	 * each Cmp class must define:
	 *   - a unique name to idenfity itself in the factory.
	 *   - a static method to register itself in the factory.
	 *
	 *
     * Typical usage of Cmp:
     *
     *  - How to get all Cmp names
     @code
     *      vector<string> all_cmps = Factory<Cmp>::get_list();
     @endcode
	 *
     *  - How to use a Cmp
     @code
     *      EMData *image1 = ...;
     *      EMData *image2 = ...;
	 *      Dict params = ...;
     *      float result = image1->cmp("CMP_NAME", image2, params);
     @endcode
	 *
     *  - How to define a new Cmp class \n
     *    A new XYZCmp class should implement the following functions:
	 *    (Please replace 'XYZ' with your own class name).
	 @code
     *        float cmp(EMData * image, EMData * with) const;
     *        TypeDict get_param_types() const;
     *        string get_name() const { return "XYZ"; }
     *        static Cmp *NEW() { return XYZCmp(); }
	 @endcode
     */

	class Cmp
	{
	  public:
		virtual ~ Cmp()
		{
		}
		
		/** To compare 'image' with another image passed in through
		 * its parameters. An optional transformation may be used
		 * to transform the 2 images.
		 *
		 * @param image The first image to be compared.
		 * @param with The second image to be comppared.
		 * @return The comparison result. Smaller better by default
		 */			
		virtual float cmp(EMData * image, EMData * with) const = 0;
		
		/** Get the Cmp's name. Each Cmp is identified by a unique name.
		 * @return The Cmp's name.
		 */
		virtual string get_name() const = 0;

		virtual string get_desc() const = 0;

		/** Get the Cmp parameters in a key/value dictionary.
		 * @return A key/value pair dictionary containing the parameters.
		 */
		virtual Dict get_params() const
		{
			return params;
		}

		/** Set the Cmp parameters using a key/value dictionary.
		 * @param new_params A dictionary containing the new parameters.
		 */
		virtual void set_params(const Dict & new_params)
		{
			params = new_params;
		}

		/** Get Cmp parameter information in a dictionary. Each
		 * parameter has one record in the dictionary. Each record
		 * contains its name, data-type, and description.
		 *
		 * @return A dictionary containing the parameter info.
		 */	 
		virtual TypeDict get_param_types() const = 0;
		
	protected:
		void validate_input_args(const EMData * image, const EMData *with) const;
		
		mutable Dict params;
	};

	/** Compute the cross-correlation coefficient between two images.
	 *
	 * The cross-correlation coefficient is defined as:
	 *       <AB> - <A><B>
	 * CCC = -------------
	 *       sig(A)sig(B)
	 *
	 * where the angle brackets denote averages and "sig" is the 
	 * standard deviation.  In the case of a mask, only pixels under 
	 * the mask are included in the calculation of averages.
	 *
	 * For complex images, this routine currently bails.
	 * @author Grant Goodyear (grant.goodyear@uth.tmc.edu) 
	 * @date 2005-10-03
	 * @param mask Image mask
	 */
	class CccCmp:public Cmp
	{
	  public:
		float cmp(EMData * image, EMData * with) const;

		string get_name() const
		{
			return "ccc";
		}

		string get_desc() const
		{
			return "Cross-correlation coefficient";
		}

		static Cmp *NEW()
		{
			return new CccCmp();
		}

		TypeDict get_param_types() const
		{
			TypeDict d;
			d.put("mask", EMObject::EMDATA, "image mask");
			return d;
		}

	};
	
	/** Squared Euclidean distance normalized by n between 'this' and 'with'*/
	//  I corrected this as there is no such thing as "variance between two images" 
	//  I corrected naive coding to avoid square
	//  Also, the equation in return statement was incorrect, grrrr!!! 
	//  Finally, I added mask option  PAP 04/23/06
	class SqEuclideanCmp:public Cmp
	{
	  public:
		SqEuclideanCmp() {}
		
		float cmp(EMData * image, EMData * with) const;

		string get_name() const
		{
			return "SqEuclidean";
		}

		string get_desc() const
		{
			return "Squared Euclidean distance (sum(a - b)^2)/n.";
		}

		static Cmp *NEW()
		{
			return new SqEuclideanCmp();
		}

		TypeDict get_param_types() const
		{
			TypeDict d;
			d.put("mask", EMObject::EMDATA, "image mask");
			return d;
		}

	};


	/** Use dot product of 2 same-size images to do the comparison.  // Added mask option PAP 04/23/06
	* For complex images, it does not check r/i vs a/p.
	* @author Steve Ludtke (sludtke@bcm.tmc.edu) 
	* @date 2005-07-13
	* @param negative Returns -1 * dot product, default true
	* @param normalize Returns normalized dot product -1.0 - 1.0
    */
	class DotCmp:public Cmp
	{
	  public:
		float cmp(EMData * image, EMData * with) const;

		string get_name() const
		{
			return "dot";
		}

		string get_desc() const
		{
			return "Dot product (default -1 * dot product)";
		}

		static Cmp *NEW()
		{
			return new DotCmp();
		}

		TypeDict get_param_types() const
		{
			TypeDict d;
			d.put("negative", EMObject::INT, "If set, returns -1 * dot product. Set by default so smaller is better");
			d.put("normalize", EMObject::INT, "If set, returns normalized dot product (cosine of the angle) -1.0 - 1.0.");
			d.put("mask", EMObject::EMDATA, "image mask");
			return d;
		}

	};

	/** This will calculate the dot product for each quadrant of the image and
	* return the worst value
	* @author Steve Ludtke (sludtke@bcm.tmc.edu) 
	* @date 2005-07-13
	* @param negative Returns -1 * dot product, default true
	* @param normalize Returns normalized dot product -1.0 - 1.0
	*/
	class QuadMinDotCmp:public Cmp
	{
	  public:
		float cmp(EMData * image, EMData * with) const;

		string get_name() const
		{
			return "quadmindot";
		}

		string get_desc() const
		{
			return "Caclultes dot product for each quadrant and returns worst value (default -1 * dot product)";
		}

		static Cmp *NEW()
		{
			return new QuadMinDotCmp();
		}

		TypeDict get_param_types() const
		{
			TypeDict d;
			d.put("negative", EMObject::INT, "If set, returns -1 * dot product. Default = true (smaller is better)");
			d.put("normalize", EMObject::INT, "If set, returns normalized dot product -1.0 - 1.0.");
			return d;
		}

	};

	
	/** Variance between two data sets after various modifications. 
	* Generally, 'this' should be noisy and 'with' should be less noisy. 
	* linear scaling (mx + b) of the densities in 'this' is performed 
	* to produce the smallest possible variance between images. 
	*
	* If keepzero is set, then zero pixels are left at zero (b is not added).
	* if matchfilt is set, then 'with' is filtered so its radial power spectrum matches 'this'
	* If invert is set, then (y-b)/m is applied to the second image rather than mx+b to the first.
	*
	* To modify 'this' to match the operation performed here, scale 
	* should be applied first, then b should be added
	*/
	class OptVarianceCmp:public Cmp
	{
	  public:
		OptVarianceCmp() : scale(0), shift(0) {}
		
		float cmp(EMData * image, EMData * with) const;

		string get_name() const
		{
			return "optvariance";
		}

		string get_desc() const
		{
			return "Real-space variance after density optimization, self should be noisy and target less noisy. Linear transform applied to density to minimize variance.";
		}

		static Cmp *NEW()
		{
			return new OptVarianceCmp();
		}

		TypeDict get_param_types() const
		{
			TypeDict d;
			d.put("invert", EMObject::INT, "If set, 'with' is rescaled rather than 'this'. 'this' should still be the noisier image.");
			d.put("keepzero", EMObject::INT, "If set, zero pixels will not be adjusted in the linear density optimization");
			d.put("matchfilt", EMObject::INT, "If set, with will be filtered so its radial power spectrum matches 'this' before density optimization of this");
			d.put("radweight", EMObject::INT, "upweight variances closer to the edge of the image");
			d.put("debug", EMObject::INT, "Performs various debugging actions if set.");
			return d;
		}

		float get_scale() const
		{
			return scale;
		}

		float get_shift() const
		{
			return shift;
		}
		
	private:
		mutable float scale;
		mutable float shift;
	};
	/** Amplitude weighted mean phase difference (radians) with optional
     * SNR weight. SNR should be an array as returned by ctfcurve()
     * 'data' should be the less noisy image, since it's amplitudes 
     * will be used to weight the phase residual. 2D only.
	 *
     * Use Phase Residual as a measure of similarity
     * Differential phase residual (DPR) is a measure of statistical
     * dependency between two averages, computed over rings in Fourier
     * space as a function of ring radius (= spatial frequency, or resolution) 
     */
	class PhaseCmp:public Cmp
	{
	  public:
		float cmp(EMData * image, EMData * with) const;

		string get_name() const
		{
			return "phase";
		}

		string get_desc() const
		{
			return "Mean phase difference";
		}

		static Cmp *NEW()
		{
			return new PhaseCmp();
		}

		TypeDict get_param_types() const
		{
			TypeDict d;
			return d;
		}
	};

	/** FRCCmp returns a quality factor based on FRC between images.
     *  Fourier ring correlation (FRC) is a measure of statistical
     * dependency between two averages, computed by comparison of
     * rings in Fourier space. 1 means prefect agreement. 0 means no
     * correlation.    
     */
	class FRCCmp:public Cmp
	{
	  public:
		float cmp(EMData * image, EMData * with) const;

		string get_name() const
		{
			return "frc";
		}

		string get_desc() const
		{
			return "Mean Fourier ring correlation";
		}

		static Cmp *NEW()
		{
			return new FRCCmp();
		}

		TypeDict get_param_types() const
		{
			TypeDict d;
			d.put("snr", EMObject::FLOATARRAY);
			return d;
		}
	};

	template <> Factory < Cmp >::Factory();

	void dump_cmps();
	map<string, vector<string> > dump_cmps_list();
}


#endif

/* vim: set ts=4 noet: */
