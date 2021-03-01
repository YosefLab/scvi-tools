from anndata import read_csv, read_h5ad, read_loom, read_text

from ._anndata import (
    register_tensor_from_anndata,
    setup_anndata,
    transfer_anndata_setup,
    view_anndata_setup,
)
from ._anndatarecorder import AnnDataRecorder
from ._datasets import (
    annotation_simulation,
    brainlarge_dataset,
    breast_cancer_dataset,
    cortex,
    dataset_10x,
    frontalcortex_dropseq,
    heart_cell_atlas_subsampled,
    mouse_ob_dataset,
    pbmc_dataset,
    pbmcs_10x_cite_seq,
    prefrontalcortex_starmap,
    purified_pbmc_dataset,
    retina,
    seqfish,
    seqfishplus,
    smfish,
    spleen_lymph_cite_seq,
    synthetic_iid,
)
from ._preprocessing import organize_cite_seq_10x, poisson_gene_selection
from ._read import read_10x_atac
from ._utils import get_from_registry

__all__ = [
    "setup_anndata",
    "AnnDataRecorder",
    "get_from_registry",
    "view_anndata_setup",
    "poisson_gene_selection",
    "organize_cite_seq_10x",
    "pbmcs_10x_cite_seq",
    "spleen_lymph_cite_seq",
    "dataset_10x",
    "purified_pbmc_dataset",
    "brainlarge_dataset",
    "synthetic_iid",
    "pbmc_dataset",
    "cortex",
    "seqfish",
    "seqfishplus",
    "smfish",
    "breast_cancer_dataset",
    "mouse_ob_dataset",
    "retina",
    "prefrontalcortex_starmap",
    "frontalcortex_dropseq",
    "annotation_simulation",
    "transfer_anndata_setup",
    "register_tensor_from_anndata",
    "read_h5ad",
    "read_csv",
    "read_loom",
    "read_text",
    "read_10x_atac",
    "heart_cell_atlas_subsampled",
]
