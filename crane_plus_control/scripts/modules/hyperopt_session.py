#!/usr/bin/env python
# -*- coding:utf-8 -*-
###
# File Created: Wednesday, 16th January 2019 10:02:24 am
# Modified By: Charlene Leong
# Last Modified: Thursday, January 17th 2019, 1:27:58 pm
# Author: Charlene Leong (charleneleong84@gmail.com)
###

import sys
from timeit import default_timer as timer
from collections import OrderedDict
import itertools

import csv
import json
import pprint
import pandas as pd
import numpy as np
from functools import partial

import rospkg
import rospy
import std_msgs.msg

import moveit_commander
from moveit_msgs.srv import GetPlannerParams, SetPlannerParams
import moveit_msgs.msg

from hyperopt import hp, rand, tpe, Trials, fmin, STATUS_OK
from hyperopt.pyll.stochastic import sample

from session import Session


class HyperOptSession(Session):
    """Constructor for parameter tuning session
    
    Args:
        Session (object): Session object initiates session with default funcitons
    """

    def __init__(self, mode):
        super(HyperOptSession, self).__init__(mode)
        rospy.loginfo('Initialising hyperopt parameter tuning session')

    def _objective(self, params):
        self.n_trial += 1
        # Extract param set
        params_config = params['params_config']
        params_set = params['params_set']

        # Set new params
        planner_params = moveit_msgs.msg.PlannerParams()
        planner_params.keys = params_set.keys()
        planner_params.values = [str(v) for v in params_set.values()]
        self.group.set_planner_id(params_config['planner'])
        self.planner_config.set_planner_params(
            params_config['planner'], planner_params)

        # Execute experiment for iter times and get planning and run_time stats
        stats = super(HyperOptSession, self)._get_stats(
            params_config['start_pose'], params_config['target_pose'])

        # loss = sum(stats.values())
        loss = stats['avg_path_length']

        rospy.loginfo('n_trial: %d loss: %.4f avg_run_time: %.4f avg_plan_time: %.4f avg_dist: %.4f avg_path_length: %.4f',
                      self.n_trial, loss, stats['avg_run_time'], stats['avg_plan_time'], stats['avg_dist'], stats['avg_path_length'])

        # Create OrderedDict to write to CSV
        result = OrderedDict([('n_trial', self.n_trial), ('loss', loss)])
        planner_params = OrderedDict([('planner', params_config['planner']), ('start_pose', params_config['start_pose']), (
            'target_pose', params_config['target_pose'])])
        stats = OrderedDict([('avg_runs', stats['avg_runs']), ('avg_runtime', stats['avg_run_time']), ('avg_plan_time', stats['avg_plan_time']),
                             ('avg_dist', stats['avg_dist']), ('avg_path_length', stats['avg_path_length'])])
        result = OrderedDict(list(result.items()) +
                             list(planner_params.items() + list(stats.items())))
        # Need to save params as str for csv
        result_csv = OrderedDict(
            list(result.items()) + [('params', str(params_set))])
        result = OrderedDict(list(result.items()) +
                             [('params', params_set), ('status', STATUS_OK)])
        # print(json.dumps(result_csv, indent=4))     # Print OrderedDict nicely

        result_df = pd.DataFrame(
            dict(result_csv), columns=result.keys(), index=[0])
        with open(self.results_path, 'a') as f:
            result_df.to_csv(f, header=False, index=False)

        return dict(result)

    def _optimise_obj(self, start_pose, target_pose):
        # Write headers
        with open(self.results_path, 'w') as f:
            writer = csv.writer(f)
            writer.writerow(['n_trial', 'loss', 'planner', 'start_pose', 'target_pose', 'avg_runs', 'avg_runtime',
                             'avg_plan_time', 'avg_dist', 'avg_path_length', 'params'])

        # Setting up the parameter search space and parameters
        for planner, params_set in self.planner_config.iteritems():
            params_set = dict(self.planner_config[planner].items())
            for k, v in params_set.iteritems():
                if isinstance(v, list):
                    begin_range = v[0]
                    end_range = v[1]
                    step = v[2]
                    # Discrete uniform dist
                    params_set[k] = hp.quniform(
                        k, begin_range, end_range, step)
            params = {}
            params['params_set'] = params_set
            params['params_config'] = {
                'planner': planner, 'start_pose': start_pose, 'target_pose': target_pose}

            print('\n')
            rospy.loginfo('Executing %s on %s:  Max trials: %d Averaging over %d runs', self.mode,
                          params['params_config']['planner'], self.max_trials, self.iter)
            self.n_trial = 0        # Reset to n_trials to zero for each planner
            if self.mode == 'tpe':
                algo = partial(tpe.suggest,
                               # Sample 1000 candidate and select candidate that has highest Expected Improvement (EI)
                               n_EI_candidates=100,
                               # Use 20% of best observations to estimate next set of parameters
                               gamma=0.2,
                               # First 20 trials are going to be random
                               n_startup_jobs=20)
            elif self.mode == 'rand':
                algo = rand.suggest

            trials = Trials()
            best = fmin(fn=self._objective, space=params, algo=algo,
                        max_evals=self.max_trials, trials=trials)

        #     self.results_df[planner] = trials.results
        #     # pprint.pprint(trials.results)

        # pprint.pprint(self.results_df)

    def run(self):
        pass