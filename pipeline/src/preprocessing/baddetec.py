import numpy as np
from sklearn.neighbors.kde import KernelDensity
from sklearn.grid_search import GridSearchCV

def bad_chan_detect(inEEG, method, **kwargs):
    out = ''
    out += '<h3> DETECTING BAD CHANNELS </h3>'
    if method == 'KDE':
        out += '<p> Detecting bad channels with a Kernel Density Estimator </p>'
        bad_chan_list = []
        for patient in range(inEEG.shape[3]):
            bc_t = []
            for trial in range(inEEG.shape[2]):
                bcs = prob_baddetec(inEEG[:, :, patient],
                            kwargs["threshold"], kdewrap)
                bc_t.append(bcs)
                out += "Detected bad channels: " + str(bcs)
            bad_chan_list.append(bc_t)
        return bad_chan_list, out



def reshape(inEEG):
    r"""Reshape the data from the inputted format (timesteps, num channels, num patients) to (time, channels).

    Parameters
    ----------
    inEEG : array_like (3d or 2d)
        Paradigm data characterized by: (timesteps, num channels, num patients). If data previously transformed into (time, channels), also accept and don't alter.

    Returns
    -------
    inEEG: array_like(2d)
        (time, channels)

    Raises
    ------
    DimensionException
        Input is not 2d or 3d, not interpretable

    Examples
    --------
    These are written in doctest format, and should illustrate how to
    use the function.

    First with a 2D array input (preformatted)
    >>> success1 = np.column_stack([sin] * 50)
    >>> print success1.shape
    (1000L, 50L)
    >>> reshaped = reshape(success1).shape
    >>> print reshaped.shape
    (1000L, 50L)
    
    Now with 3D input (2 patients)
    >>> dummy = np.dstack([success1] * 2)
    >>> print dummy.shape
    (1000L, 50L, 2L)
    >>> reshaped = reshape(dummy).shape
    >>> print reshaped.shape
    (2000L, 50L)

    """
    if len(inEEG.shape) == 3:
        electrodes = inEEG.shape[1]
        times = inEEG.shape[0]
        trials = inEEG.shape[2]
        return np.reshape(inEEG, (inEEG.shape[0] * inEEG.shape[2], inEEG.shape[1]))
    elif len(inEEG.shape) != 1 and len(inEEG.shape) != 2:
        # fail case
        print "fail"
    else:
        return inEEG


def kdewrap(indata, kernel):
    r"""A wrapper for the KDE implementation from the scikit-learn package.

    Kernel density estimates are a method of estimating the distribution of a dataset non-parametrically.
    Basically, without any outside parameters bounding the data, we generate a distribution representing the data from a base kernel function.
    For each point, the base kernel function is generated, and the kernel is altered based on the distance between each individual point and every other point.
    Combining these kernels creates a fairly accurate density function of the data.

    Parameters
    ----------
    indata : list (data points per timestep)
        For a given electrode, a list of all the values for each timestamp
    kernel : string
        'gaussian', 'tophat', 'epanechnikov', 'exponential', 'linear', 'cosine' Choose which base kernel function to use.

    Returns
    -------
    kde.score_samples(indata[:, np.newaxis]): arraylike (timesteps, 1)
        Return an array of the densities for each electrode value and where it lies in the kernel function

    Notes
    -----
    For notes and refernces go to: https://github.com/NeuroDataDesign/orange-panda/blob/master/notes/bad_chan_detect/baddetec/kernel-probability-density.pdf

    Examples
    --------
    These are written in doctest format, and should illustrate how to
    use the function.

    >>> inEEG = [0.2, 0.5, 3.6, 2.2, ...]
    >>> probdist = kdewrap(inEEG, 'gaussian')
    probdist = [...]

    """
    grid = GridSearchCV(KernelDensity(),
                    {'bandwidth': np.linspace(0.1, 1.0, 30)},
                    cv=10) # 20-fold cross-validation
    grid.fit(indata[:, None])
    kde = KernelDensity(kernel=kernel, bandwidth=grid.best_params_["bandwidth"]).fit(indata[:, np.newaxis])
    return kde.score_samples(indata[:, np.newaxis])

def prob_baddetec(inEEG, threshold, probfunc):
    r"""Detect bad electrodes based on probability

    Based on whether the joint probability of an electrode's time values (decided by a probability function passed in
    via the parameters) is too different from the other electrodes.

    Parameters
    ----------
    inEEG : numpy array (timesteps, channels, patients)
        For a given electrode, a list of all the values for each timestamp
    threshold : integer
        The number of standard deviations away from the mean joint probability counts an electrode's probability can be
        for it to count as a bad electrode
    probfunc : function. In this case takes in data and kernel as arguments
        function to make probability distribution

    Returns
    -------
    inEEG : original data
        Return original data because isn't changed
    o : string
        output string for basic comprehension of output
    badelec: list
        List of bad electrodes from list

    Notes
    -----
    Pseudocode located at: https://github.com/NeuroDataDesign/orange-panda/blob/master/notes/bad_chan_detect/baddetec/bad-electrode-detection.pdf

    """
    electrodes = inEEG.shape[1]
    
    # Start by reshaping data (if necessary)
    if len(inEEG.shape) == 3:
        shapeEEG = np.reshape(inEEG, (inEEG.shape[0] * inEEG.shape[2], inEEG.shape[1]))
    elif len(inEEG.shape) != 1 and len(inEEG.shape) != 2:
        # fail case
        return -1
    
    # Then, initialize a probability vector of electrode length
    probvec = np.zeros(electrodes)
    
    # iterate through electrodes and get joint probs
    for i in range(0, electrodes):
        # get prob distribution
        probdist = probfunc(shapeEEG[:, i], 'gaussian')
        print "BadDetect done for " + str(i)
        # using probdist find joint prob
        probvec[i] = np.sum(probdist) 
    
    # normalize probvec
    # first calc mean
    avg = np.mean(probvec)
    # then st, d dev
    stddev = np.std(probvec)
    # then figure out which electrodes are bad
    badelec = []
    #print probvec
    for i in range(0, len(probvec)):
        #print i, avg, stddev, (avg - probvec[i]) / stddev
        if ((avg - probvec[i]) / stddev) >= threshold:
            badelec.append(i)
            
    return badelec

def good_elec(inEEG, badelec):
    r"""Detect bad electrodes based on probability

    Based on whether the joint probability of an electrode's time values (decided by a probability function passed in
    via the parameters) is too different from the other electrodes.

    Parameters
    ----------
    inEEG : numpy array (timesteps, channels, patients)
        For a given electrode, a list of all the values for each timestamp
    badelec : list
        List of all bad electrode indices in inEEG

    Returns
    -------
    newEEG: array (timesteps, good channels, patients)
        delete all bad electrode columns for the EEG data

    """
    return np.delete(inEEG, badelec, 1)