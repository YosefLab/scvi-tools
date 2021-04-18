import numpy as np
from functools import partial

from scvi.external.wscvi import WVAE, WSCVI
from scvi.model import SCVI
from scvi.data import synthetic_iid
from scvi.utils import DifferentialComputation
from scvi.utils._differential import estimate_delta, estimate_pseudocounts_offset


def test_features():
    a = np.random.randn(
        100,
    )
    b = 3 + np.random.randn(
        100,
    )
    c = -3 + np.random.randn(
        100,
    )
    alls = np.concatenate([a, b, c])
    delta = estimate_delta(alls)
    assert delta >= 0.4 * 3
    assert delta <= 6

    scales_a = np.random.rand(100, 50)
    where_zero_a = np.zeros(50, dtype=bool)
    where_zero_a[:10] = True
    scales_a[:, :10] = 1e-6

    scales_b = np.random.rand(100, 50)
    where_zero_b = np.zeros(50, dtype=bool)
    where_zero_b[-10:] = True
    scales_b[:, -10:] = 1e-7
    offset = estimate_pseudocounts_offset(
        scales_a=scales_a,
        scales_b=scales_b,
        where_zero_a=where_zero_a,
        where_zero_b=where_zero_b,
    )
    assert offset <= 1e-6


def test_scvi_new_de():
    adata = synthetic_iid()
    model = SCVI(adata=adata, use_observed_lib_size=False)
    model.train(
        max_epochs=5,
    )
    model_fn = partial(model.get_population_expression, return_numpy=True)
    dc = DifferentialComputation(model_fn=model_fn, adata=adata)
    cell_idx1 = np.asarray(adata.obs.labels == "label_1")
    cell_idx2 = ~cell_idx1

    dc.get_bayes_factors(cell_idx1, cell_idx2, mode="change", use_permutation=True)
    dc.get_bayes_factors(cell_idx1, cell_idx2, mode="change", use_permutation=True, eps=None, delta=None)


def test_wscvi():
    adata = synthetic_iid()
    model = WSCVI(adata=adata, n_latent=5, loss_type="IWELBO", n_particles=25)
    model.train(
        max_epochs=5,
    )

    # Checking that function output shapes make sense
    idx = adata.obs.labels.values == "label_0"
    n_cells = idx.sum()
    scdl = model._make_data_loader(adata=adata, indices=idx, batch_size=128)
    outs = model._inference_loop(scdl, n_samples=25)
    assert outs["log_px_zs"].shape == outs["log_qz"].shape
    assert outs["log_px_zs"].shape == (25 * n_cells, n_cells)

    # Overall scale sampling
    outs = model.get_population_expression(indices=idx)

    # Differential expression
    model_fn = partial(model.get_population_expression, return_numpy=True)
    dc = DifferentialComputation(model_fn=model_fn, adata=adata)
    cell_idx1 = np.asarray(adata.obs.labels == "label_1")
    cell_idx2 = ~cell_idx1

    dc.get_bayes_factors(cell_idx1, cell_idx2, mode="change", use_permutation=True)