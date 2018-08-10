import numpy as np

from . import GeneExpressionDataset
from . import LoomDataset


class SyntheticDataset(GeneExpressionDataset):
    def __init__(self, batch_size=200, nb_genes=100, n_batches=2, n_labels=3):
        # Generating samples according to a ZINB process
        data = np.random.negative_binomial(5, 0.3, size=(n_batches, batch_size, nb_genes))
        mask = np.random.binomial(n=1, p=0.7, size=(n_batches, batch_size, nb_genes))
        newdata = (data * mask)  # We put the batch index first
        labels = np.random.randint(0, n_labels, size=(n_batches, batch_size, 1))
        super(SyntheticDataset, self).__init__(
            *GeneExpressionDataset.get_attributes_from_list(newdata, list_labels=labels),
            gene_names=np.arange(nb_genes).astype(np.str), cell_types=np.arange(n_labels).astype(np.str)
        )


class SyntheticUMI(LoomDataset):
    def __init__(self, save_path='data/'):
        super(SyntheticUMI, self).__init__(filename='umi.loom',
                                           save_path=save_path,
                                           url='https://github.com/YosefLab/scVI-data/raw/master/umi.loom')


class SyntheticNONUMI(LoomDataset):
    def __init__(self, save_path='data/'):
        super(SyntheticNONUMI, self).__init__(filename='nonumi.loom',
                                              save_path=save_path,
                                              url='https://github.com/YosefLab/scVI-data/raw/master/nonumi.loom')
