import logging
from typing import Optional, Tuple, Union

import anndata
import numba
import numpy as np
import pandas as pd
import scipy.sparse as sp_sparse

logger = logging.getLogger(__name__)


def get_from_registry(adata: anndata.AnnData, key: str) -> np.ndarray:
    """
    Returns the object in AnnData associated with the key in ``.uns['_scvi']['data_registry']``.

    Parameters
    ----------
    adata
        anndata object already setup with `scvi.data.setup_anndata()`
    key
        key of object to get from ``adata.uns['_scvi]['data_registry']``

    Returns
    -------
    The requested data

    Examples
    --------
    >>> import scvi
    >>> adata = scvi.data.cortex()
    >>> adata.uns['_scvi']['data_registry']
    {'X': ['_X', None],
    'batch_indices': ['obs', 'batch'],
    'local_l_mean': ['obs', '_scvi_local_l_mean'],
    'local_l_var': ['obs', '_scvi_local_l_var'],
    'labels': ['obs', 'labels']}
    >>> batch = get_from_registry(adata, "batch_indices")
    >>> batch
    array([[0],
           [0],
           [0],
           ...,
           [0],
           [0],
           [0]])
    """
    data_loc = adata.uns["_scvi"]["data_registry"][key]
    attr_name, attr_key = data_loc["attr_name"], data_loc["attr_key"]

    data = getattr(adata, attr_name)
    if attr_key != "None":
        if isinstance(data, pd.DataFrame):
            data = data.loc[:, attr_key]
        else:
            data = data[attr_key]
    if isinstance(data, pd.Series):
        data = data.to_numpy().reshape(-1, 1)
    return data


def _compute_library_size(
    data: Union[sp_sparse.spmatrix, np.ndarray]
) -> Tuple[np.ndarray, np.ndarray]:
    sum_counts = data.sum(axis=1)
    masked_log_sum = np.ma.log(sum_counts)
    if np.ma.is_masked(masked_log_sum):
        logger.warning(
            "This dataset has some empty cells, this might fail inference."
            "Data should be filtered with `scanpy.pp.filter_cells()`"
        )
    log_counts = masked_log_sum.filled(0)
    local_mean = (np.mean(log_counts).reshape(-1, 1)).astype(np.float32)
    local_var = (np.var(log_counts).reshape(-1, 1)).astype(np.float32)
    return local_mean, local_var


def _compute_library_size_batch(
    adata,
    batch_key: str,
    local_l_mean_key: str = None,
    local_l_var_key: str = None,
    layer=None,
    copy: bool = False,
):
    """
    Computes the library size.

    Parameters
    ----------
    adata
        anndata object containing counts
    batch_key
        key in obs for batch information
    local_l_mean_key
        key in obs to save the local log mean
    local_l_var_key
        key in obs to save the local log variance
    layer
        if not None, will use this in adata.layers[] for X
    copy
        if True, returns a copy of the adata

    Returns
    -------
    type
        anndata.AnnData if copy was True, else None

    """
    if batch_key is None:
        batch_indices = [0] * adata.n_obs
    elif batch_key is not None and batch_key in adata.obs_keys():
        batch_indices = adata.obs[batch_key]
    else:
        raise ValueError("batch_key not valid key in obs dataframe")

    local_means = np.zeros((adata.shape[0], 1))
    local_vars = np.zeros((adata.shape[0], 1))
    for i_batch in np.unique(batch_indices):
        idx_batch = np.squeeze(batch_indices == i_batch)
        if layer is not None:
            if layer not in adata.layers.keys():
                raise ValueError("layer not a valid key for adata.layers")
            data = adata[idx_batch].layers[layer]
        else:
            data = adata[idx_batch].X
        (local_means[idx_batch], local_vars[idx_batch]) = _compute_library_size(data)
    if local_l_mean_key is None:
        local_l_mean_key = "_scvi_local_l_mean"
    if local_l_var_key is None:
        local_l_var_key = "_scvi_local_l_var"

    if copy:
        copy = adata.copy()
        copy.obs[local_l_mean_key] = local_means
        copy.obs[local_l_var_key] = local_vars
        return copy
    else:
        adata.obs[local_l_mean_key] = local_means
        adata.obs[local_l_var_key] = local_vars


def _check_nonnegative_integers(
    data: Union[pd.DataFrame, np.ndarray, sp_sparse.spmatrix]
):
    """Approximately checks values of data to ensure it is count data."""
    if isinstance(data, np.ndarray):
        data = data
    elif issubclass(type(data), sp_sparse.spmatrix):
        data = data.data
    elif isinstance(data, pd.DataFrame):
        data = data.to_numpy()
    else:
        raise TypeError("data type not understood")

    check = data[:10]
    return _check_is_counts(check)


@numba.njit(cache=True)
def _check_is_counts(data):
    for d in data.flat:
        if d < 0 or d % 1 != 0:
            return False
    return True


def _get_batch_mask_protein_data(
    adata: anndata.AnnData,
    protein_expression_obsm_key: str,
    batch_key: Optional[str] = None,
):
    """
    Returns a list with length number of batches where each entry is a mask.

    The mask is over cell measurement columns that are present (observed)
    in each batch. Absence is defined by all 0 for that protein in that batch.
    """
    pro_exp = adata.obsm[protein_expression_obsm_key]
    pro_exp = pro_exp.to_numpy() if isinstance(pro_exp, pd.DataFrame) else pro_exp
    try:
        batches = adata.obs[batch_key].values
    except KeyError:
        batches = np.array([0] * adata.n_obs)
    batch_mask = {}
    for b in np.unique(batches):
        b_inds = np.where(batches.ravel() == b)[0]
        batch_sum = pro_exp[b_inds, :].sum(axis=0)
        all_zero = batch_sum == 0
        batch_mask[b] = ~all_zero

    return batch_mask
