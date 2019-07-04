import logging
import os

import loompy

from scvi.dataset.dataset import DownloadableDataset

logger = logging.getLogger(__name__)


class LoomDataset(DownloadableDataset):
    """Loads a potentially remote `.loom` file.

    :param filename: File name to use when saving/loading the data.
    :param save_path: Location to use when saving/loading the data.
    :param url: URL to download the data from.
    :param batch_indices_attribute_name: Name of the attribute containing batch indices.
    :param labels_attribute_name: Name of the attribute containing labels.
    :param gene_names_attribute_name: Name of the attribute containing gene names.
    :param cell_types_attribute_name: Name of the attribute containing cell types.
    :param delayed_populating: Switch for delayed populating mechanism.

    Examples:
        >>> # Loading a remote dataset
        >>> remote_loom_dataset = LoomDataset("osmFISH_SScortex_mouse_all_cell.loom", save_path='data/',
        ... url='http://linnarssonlab.org/osmFISH/osmFISH_SScortex_mouse_all_cells.loom')
        >>> # Loading a local dataset
        >>> local_loom_dataset = LoomDataset("osmFISH_SScortex_mouse_all_cell.loom", save_path='data/')
    """

    def __init__(
        self,
        filename: str,
        save_path: str = "data/",
        url: str = None,
        batch_indices_attribute_name: str = "BatchID",
        labels_attribute_name: str = "ClusterID",
        gene_names_attribute_name: str = "Gene",
        cell_types_attribute_name: str = "CellTypes",
        delayed_populating: bool = False,
    ):
        self.batch_indices_attribute_name = batch_indices_attribute_name
        self.labels_attribute_name = labels_attribute_name
        self.gene_names_attribute_name = gene_names_attribute_name
        self.cell_types_attribute_name = cell_types_attribute_name
        super().__init__(
            urls=url,
            filenames=filename,
            save_path=save_path,
            delayed_populating=delayed_populating,
        )

    def populate(self):
        logger.info("Preprocessing dataset")
        (
            gene_names,
            labels,
            batch_indices,
            cell_types,
            cell_attributes_dict,
            gene_attributes_dict,
            global_attributes_dict,
        ) = (None, None, None, None, None, None, None)

        ds = loompy.connect(os.path.join(self.save_path, self.filenames[0]))
        select = ds[:, :].sum(axis=0) > 0  # Take out cells that don't express any gene
        if not all(select):
            logger.warning("Removing non-expressing cells")

        for row_attribute_name in ds.ra:
            if row_attribute_name == self.gene_names_attribute_name:
                gene_names = ds.ra[self.gene_names_attribute_name]
            else:
                gene_attributes_dict = gene_attributes_dict if gene_attributes_dict is not None else {}
                gene_attributes_dict[row_attribute_name] = ds.ra[row_attribute_name]

        for column_attribute_name in ds.ca:
            if column_attribute_name == self.batch_indices_attribute_name:
                batch_indices = ds.ca[self.batch_indices_attribute_name][select]
            elif column_attribute_name == self.labels_attribute_name:
                labels = ds.ra[self.labels_attribute_name][select]
            else:
                cell_attributes_dict = cell_attributes_dict if cell_attributes_dict is not None else {}
                cell_attributes_dict[column_attribute_name] = ds.ra[
                    column_attribute_name
                ][select]

        for global_attribute_name in ds.attrs:
            if global_attribute_name == self.cell_types_attribute_name:
                cell_types = ds.attrs[self.cell_types_attribute_name]
            else:
                global_attributes_dict = global_attributes_dict if global_attributes_dict is not None else {}
                global_attributes_dict[global_attribute_name] = ds.attrs[global_attribute_name]

        if global_attributes_dict is not None:
            self.global_attributes_dict = global_attributes_dict

        data = ds[:, select].T  # change matrix to cells by genes
        ds.close()

        logger.info("Finished preprocessing dataset")
        self.populate_from_data(
            X=data,
            batch_indices=batch_indices,
            labels=labels,
            gene_names=gene_names,
            cell_types=cell_types,
            cell_attributes_dict=cell_attributes_dict,
            gene_attributes_dict=gene_attributes_dict,
        )


class RetinaDataset(LoomDataset):
    """Loads retina dataset.

    The dataset of bipolar cells contains after their original pipeline for filtering 27,499 cells and
    13,166 genes coming from two batches. We use the cluster annotation from 15 cell-types from the author.
    We also extract their normalized data with Combat and use it for benchmarking.

    Examples:
        >>> gene_dataset = RetinaDataset()
    """

    def __init__(self, save_path: str = "data/", delayed_populating: bool = False):
        super().__init__(
            filename="retina.loom",
            save_path=save_path,
            url="https://github.com/YosefLab/scVI-data/raw/master/retina.loom",
            delayed_populating=delayed_populating,
        )
        self.cell_types = [
            "RBC",
            "MG",
            "BC5A",
            "BC7",
            "BC6",
            "BC5C",
            "BC1A",
            "BC3B",
            "BC1B",
            "BC2",
            "BC5D",
            "BC3A",
            "BC5B",
            "BC4",
            "BC8_9",
        ]
