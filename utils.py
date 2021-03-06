import h5py
import logging
import matplotlib.pyplot as plt
import numpy as np
import os
import pickle
import scipy

from scipy.ndimage.filters import gaussian_filter

from typing import Any, Dict, List, Tuple





def val_parse(v):
    """parse values from si tags into python objects if possible from si parse
     Args:
         v: si tags
     Returns:
        v: python object
    """

    try:
        return eval(v)
    except:
        if v == 'true':
            return True
        elif v == 'false':
            return False
        elif v == 'NaN':
            return np.nan
        elif v == 'inf' or v == 'Inf':
            return np.inf
        else:
            return v


def si_parse(imd: str) -> Dict:
    """parse image_description field embedded by scanimage from get image description
     Args:
         imd: image description
    Returns:
        imd: the parsed description
    """

    imddata: Any = imd.split('\n')
    imddata = [i for i in imddata if '=' in i]
    imddata = [i.split('=') for i in imddata]
    imddata = [[ii.strip(' \r') for ii in i] for i in imddata]
    imddata = {i[0]: val_parse(i[1]) for i in imddata}
    return imddata




# %% Generate data
def gen_data(dims: Tuple[int, int] = (48, 48), N: int = 10, sig: Tuple[int, int] = (3, 3), tau: float = 1.,
             noise: float = .3, T: int = 2000,
             framerate: int = 30, firerate: float = .5, seed: int = 3, cmap: bool = False, truncate: float = np.exp(-2),
             difference_of_Gaussians: bool = True, fluctuating_bkgrd: List = [50, 300]) -> Tuple[
    np.ndarray, np.ndarray, np.ndarray, np.ndarray, np.ndarray, np.ndarray, np.ndarray, Tuple[int, int]]:
    bkgrd = 10  # fluorescence baseline
    np.random.seed(seed)
    boundary = 4
    M = int(N * 1.5)
    # centers = boundary + (np.array(GeneralizedHalton(2, seed).get(M)) *
    #                       (np.array(dims) - 2 * boundary)).astype('uint16')
    centers = boundary + (np.random.rand(M, 2) *
                          (np.array(dims) - 2 * boundary)).astype('uint16')
    trueA = np.zeros(dims + (M,), dtype='float32')
    for i in range(M):
        trueA[tuple(centers[i]) + (i,)] = 1.
    if difference_of_Gaussians:
        q = .75
        for n in range(M):
            s = (.67 + .33 * np.random.rand(2)) * np.array(sig)
            tmp = gaussian_filter(trueA[:, :, n], s)
            trueA[:, :, n] = np.maximum(tmp - gaussian_filter(trueA[:, :, n], q * s) *
                                        q ** 2 * (.2 + .6 * np.random.rand()), 0)

    else:
        for n in range(M):
            s = [ss * (.75 + .25 * np.random.rand()) for ss in sig]
            trueA[:, :, n] = gaussian_filter(trueA[:, :, n], s)
    trueA = trueA.reshape((-1, M), order='F')
    trueA *= (trueA >= trueA.max(0) * truncate)
    trueA /= np.linalg.norm(trueA, 2, 0)
    keep = np.ones(M, dtype=bool)
    overlap = trueA.T.dot(trueA) - np.eye(M)
    while keep.sum() > N:
        keep[np.argmax(overlap * np.outer(keep, keep)) % M] = False
    trueA = trueA[:, keep]
    trueS = np.random.rand(N, T) < firerate / float(framerate)
    trueS[:, 0] = 0
    for i in range(N // 2):
        trueS[i, :500 + i * T // N * 2 // 3] = 0
    trueC = trueS.astype('float32')
    for i in range(N):
        # * (.9 + .2 * np.random.rand())))
        gamma = np.exp(-1. / (tau * framerate))
        for t in range(1, T):
            trueC[i, t] += gamma * trueC[i, t - 1]

    if fluctuating_bkgrd:
        K = np.array([[np.exp(-(i - j) ** 2 / 2. / fluctuating_bkgrd[0] ** 2)
                       for i in range(T)] for j in range(T)])
        ch = np.linalg.cholesky(K + 1e-10 * np.eye(T))
        truef = 1e-2 * ch.dot(np.random.randn(T)).astype('float32') / bkgrd
        truef -= truef.mean()
        truef += 1
        K = np.array([[np.exp(-(i - j) ** 2 / 2. / fluctuating_bkgrd[1] ** 2)
                       for i in range(dims[0])] for j in range(dims[0])])
        ch = np.linalg.cholesky(K + 1e-10 * np.eye(dims[0]))
        trueb = 3 * 1e-2 * \
                np.outer(
                    *ch.dot(np.random.randn(dims[0], 2)).T).ravel().astype('float32')
        trueb -= trueb.mean()
        trueb += 1
    else:
        truef = np.ones(T, dtype='float32')
        trueb = np.ones(np.prod(dims), dtype='float32')
    trueb *= bkgrd
    Yr = np.outer(trueb, truef) + noise * np.random.randn(
        *(np.prod(dims), T)).astype('float32') + trueA.dot(trueC)

    if cmap:
        import caiman as cm
        Y = np.reshape(Yr, dims + (T,), order='F')
        Cn = cm.local_correlations(Y)
        plt.figure(figsize=(20, 3))
        plt.plot(trueC.T)
        plt.figure(figsize=(20, 3))
        plt.plot((trueA.T.dot(Yr - bkgrd) / np.sum(trueA ** 2, 0).reshape(-1, 1)).T)
        plt.figure(figsize=(12, 4))
        plt.subplot(131)
        plt.scatter(*centers[keep].T[::-1], c='g')
        plt.scatter(*centers[~keep].T[::-1], c='r')
        plt.imshow(Y[:T // 10 * 10].reshape(dims +
                                            (T // 10, 10)).mean(-1).max(-1), cmap=cmap)
        plt.title('Max')
        plt.subplot(132)
        plt.scatter(*centers[keep].T[::-1], c='g')
        plt.scatter(*centers[~keep].T[::-1], c='r')
        plt.imshow(Y.mean(-1), cmap=cmap)
        plt.title('Mean')
        plt.subplot(133)
        plt.scatter(*centers[keep].T[::-1], c='g')
        plt.scatter(*centers[~keep].T[::-1], c='r')
        plt.imshow(Cn, cmap=cmap)
        plt.title('Correlation')
        plt.show()
    return Yr, trueC, trueS, trueA, trueb, truef, centers, dims  # XXX dims is always the same as passed into the function?


# %%
def save_object(obj, filename: str) -> None:
    with open(filename, 'wb') as output:
        pickle.dump(obj, output, pickle.HIGHEST_PROTOCOL)


def load_object(filename: str) -> Any:
    with open(filename, 'rb') as input_obj:
        obj = pickle.load(input_obj)
    return obj


# %%



def save_dict_to_hdf5(dic: Dict, filename: str, subdir: str = '/') -> None:
    ''' Save dictionary to hdf5 file
    Args:
        dic: dictionary
            input (possibly nested) dictionary
        filename: str
            file name to save the dictionary to (in hdf5 format for now)
    '''

    with h5py.File(filename, 'w') as h5file:
        recursively_save_dict_contents_to_group(h5file, subdir, dic)


def load_dict_from_hdf5(filename: str) -> Dict:
    ''' Load dictionary from hdf5 file
    Args:
        filename: str
            input file to load
    Returns:
        dictionary
    '''

    with h5py.File(filename, 'r') as h5file:
        return recursively_load_dict_contents_from_group(h5file, '/')


def recursively_save_dict_contents_to_group(h5file: h5py.File, path: str, dic: Dict) -> None:
    '''
    Args:
        h5file: hdf5 object
            hdf5 file where to store the dictionary
        path: str
            path within the hdf5 file structure
        dic: dictionary
            dictionary to save
    '''
    # argument type checking
    if not isinstance(dic, dict):
        raise ValueError("must provide a dictionary")

    if not isinstance(path, str):
        raise ValueError("path must be a string")

    if not isinstance(h5file, h5py._hl.files.File):
        raise ValueError("must be an open h5py file")

    # save items to the hdf5 file
    for key, item in dic.items():
        key = str(key)

        if key == 'g':
            logging.info(key + ' is an object type')
            item = np.array(list(item))
        if key == 'g_tot':
            item = np.asarray(item, dtype=np.float)
        if key in ['groups', 'idx_tot', 'ind_A', 'Ab_epoch', 'coordinates',
                   'loaded_model', 'optional_outputs', 'merged_ROIs', 'tf_in',
                   'tf_out']:
            logging.info(['groups', 'idx_tot', 'ind_A', 'Ab_epoch', 'coordinates', 'loaded_model', 'optional_outputs',
                          'merged_ROIs',
                          '** not saved'])
            continue

        if isinstance(item, list) or isinstance(item, tuple):
            item = np.array(item)
        if not isinstance(key, str):
            raise ValueError("dict keys must be strings to save to hdf5")
        # save strings, numpy.int64, numpy.int32, and numpy.float64 types
        if isinstance(item, (np.int64, np.int32, np.float64, str, np.float, float, np.float32, int)):
            h5file[path + key] = item
            if not h5file[path + key].value == item:
                raise ValueError('The data representation in the HDF5 file does not match the original dict.')
        # save numpy arrays
        elif isinstance(item, np.ndarray):
            try:
                h5file[path + key] = item
            except:
                item = np.array(item).astype('|S32')
                h5file[path + key] = item
            if not np.array_equal(h5file[path + key].value, item):
                raise ValueError('The data representation in the HDF5 file does not match the original dict.')
        # save dictionaries
        elif isinstance(item, dict):
            recursively_save_dict_contents_to_group(h5file, path + key + '/', item)
        elif 'sparse' in str(type(item)):
            logging.info(key + ' is sparse ****')
            h5file[path + key + '/data'] = item.tocsc().data
            h5file[path + key + '/indptr'] = item.tocsc().indptr
            h5file[path + key + '/indices'] = item.tocsc().indices
            h5file[path + key + '/shape'] = item.tocsc().shape
        # other types cannot be saved and will result in an error
        elif item is None or key == 'dview':
            h5file[path + key] = 'NoneType'
        elif key in ['dims', 'medw', 'sigma_smooth_snmf', 'dxy', 'max_shifts',
                     'strides', 'overlaps', 'gSig']:
            logging.info(key + ' is a tuple ****')
            h5file[path + key] = np.array(item)
        elif type(item).__name__ in ['CNMFParams', 'Estimates']:  # parameter object
            recursively_save_dict_contents_to_group(h5file, path + key + '/', item.__dict__)
        else:
            raise ValueError("Cannot save %s type for key '%s'." % (type(item), key))


def recursively_load_dict_contents_from_group(h5file: h5py.File, path: str) -> Dict:
    '''load dictionary from hdf5 object
    Args:
        h5file: hdf5 object
            object where dictionary is stored
        path: str
            path within the hdf5 file
    '''

    ans: Dict = {}
    for key, item in h5file[path].items():

        if isinstance(item, h5py._hl.dataset.Dataset):
            val_set = np.nan
            if isinstance(item.value, str):
                if item.value == 'NoneType':
                    ans[key] = None
                else:
                    ans[key] = item.value
            elif key in ['dims', 'medw', 'sigma_smooth_snmf', 'dxy', 'max_shifts', 'strides', 'overlaps']:

                if type(item.value) == np.ndarray:
                    ans[key] = tuple(item.value)
                else:
                    ans[key] = item.value
            else:
                if type(item.value) == np.bool_:
                    ans[key] = bool(item.value)
                else:
                    ans[key] = item.value

        elif isinstance(item, h5py._hl.group.Group):
            if key == 'A':
                data = item[path + key + '/data']
                indices = item[path + key + '/indices']
                indptr = item[path + key + '/indptr']
                shape = item[path + key + '/shape']
                ans[key] = scipy.sparse.csc_matrix((data[:], indices[:],
                                                    indptr[:]), shape[:])
            else:
                ans[key] = recursively_load_dict_contents_from_group(h5file, path + key + '/')
    return ans




