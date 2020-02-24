# ------------------------------------------------------------------------------
# Experiment class. The idea is that if multiple experiments are performed, and
# these should remain separate, all intermediate stored files and model states
# are stored within a directory for that experiment. In addition, the experiment
# directory contains the config.json file with the original configuration, as 
# well as the splitting of the dataset.
# ------------------------------------------------------------------------------

import os
import time
import sys
import numpy as np
import shutil

from src.utils.helper_functions import get_time_string
from src.utils.load_restore import join_path, pkl_dump, pkl_load, save_json, load_json
from src.utils.introspection import get_class

class Experiment:
    """A bundle of experiments runs with the same configuration. 
    :param config: A dictionary contains at least the following keys:
    - cross_validation: are the repetitions cross-validation folds?
    - nr_runs: number of repetitions/cross-validation folds
    """
    def __init__(self, config=None, load_exp_name=None):
        # Load an experiment for which a directory already exists
        if load_exp_name is not None:
            assert config is None
            self.name = load_exp_name
            self.path = join_path(['storage', 'experiments', self.name])
            self.config = load_json(path=self.path, name='config')
            self.splits = load_json(path=self.path, name='splits')
        # Create a new experiment directory
        else:
            self.config = config
            # The name is followed by a timestamp
            self.name = self.config.get('experiment_name', get_time_string())
            # Create root directory in ./storage/experiments
            self.path = join_path(['storage', 'experiments', self.name])
            os.makedirs(self.path)
            # Save 'config.json' file
            save_json(self.config, path=self.path, name='config')
        self.notes = self.config.get('experiment_notes', '')
        self.cross_validation = self.config['cross_validation']
        self.nr_repetitions = self.config['nr_runs']
        self.splits = [None for i in range(self.nr_repetitions)]

    def define_runs_splits(self, dataset):
        """Select which indexes make out the train, val and test sets for each 
        repitition."""

        self.splits = None #TODO

        save_json(self.splits, path=self.path, name='splits')

    def get_experiment_run(self, idx_k=0, notes=''):
        print(idx_k)
        class_path = self.config.get('experiment_class_path', 'src.utils.experiment.Experiment.ExperimentRun')
        return get_class(class_path)(root=self.path, dataset_ixs=self.splits[idx_k], name=str(idx_k), notes=self.notes+notes)     
            
class ExperimentRun:
    """Experiment runs within the same experiment differ only on the indexes 
    making up the train, validation and test splits.
    :param root: where will the experiment run files be saved?
    :param dataset_ixs: dictionary with keys 'train', 'val', 'test' and lists
        od indexes as values.
    :param name: name of the experiment
    :param notes: additional notes, to save in 'review' file
    """
    def __init__(self, root, dataset_ixs, name='', notes=None):
        self.name = name
        self.dataset_ixs = dataset_ixs
        # Create directories and assign to field
        self.paths = self._build_paths(root)
        # Set initial time
        self.time_start = time.time()
        # 'review.json' file
        self.review = dict()
        self.review['starting time'] = get_time_string()
        if notes:
            self.review['notes'] = notes

    def _build_paths(self, root):
        # Create root path inside the Experiment path
        paths = dict()
        paths['root'] = join_path([root, self.name])
        os.makedirs(paths['root'])
        # Creates subdirectories for:
        # - agent_states: for model and optimizer state dictionaries
        # - results: for results files and visualizations
        # - obj: for all other files
        # - tmp: temporal files which are deleted after finishing the exp
        # Datasets should be experiment-independent, however, indexes for train
        # and validation sets should be stored in the experiment's 'obj'.
        for subpath in ['agent_states', 'obj', 'results', 'tmp']:
            paths[subpath] = os.path.join(paths['root'], subpath)
            os.mkdir(paths[subpath])
        return paths

    def update_review(self, dictionary):
        """Update 'review.json' file with external information."""
        for key, value in dictionary.items():
            self.review[key] = value

    def write_summary_measures(self, results):
        """Template method. write selected measures into the review."""
        pass

    def finish(self, results = None, exception = None):
        elapsed_time = time.time() - self.time_start
        self.review['elapsed_time'] = '{0:.2f}'.format(elapsed_time/60)
        if results:
            self.review['state'] = 'SUCCESS'
            pkl_dump(results, path=self.paths['results'], name='results')
            self.write_summary_measures(results)
        else:
            self.review['state'] = 'FAILED: ' + str(exception)
            # TODO: store exception with better format, or whole error path
        save_json(self.review, self.paths['root'], 'review')
        shutil.rmtree(self.paths['tmp'])

    