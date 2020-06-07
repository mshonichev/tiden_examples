#!/usr/bin/env python3
#
# Copyright 2017-2020 GridGain Systems.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.


from copy import deepcopy
from tiden.apps.javaapp import JavaApp
from tiden.sshpool import SshPool
from os import makedirs, path


class Gatling(JavaApp):
    scenario = None
    scenario_args = None
    scenario_jvm_options = None

    class_name = 'io.gatling.app.Gatling'

    default_jvm_options = [
        '-server',
        '-Xms512M',
        '-Xmx2048M',
        '-XX:+UseG1GC',
        '-XX:MaxGCPauseMillis=30',
        '-XX:G1HeapRegionSize=16m',
        '-XX:InitiatingHeapOccupancyPercent=75',
        '-XX:+ParallelRefProcEnabled',
        '-XX:-UseBiasedLocking',
        '-XX:+PerfDisableSharedMem',
        '-XX:+OptimizeStringConcat',
        '-XX:+UseThreadPriorities',
        '-XX:ThreadPriorityPolicy=42',
        '-Djava.net.preferIPv4Stack=true',
        '-Djava.net.preferIPv6Addresses=false',
    ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def start(self, scenario, scenario_args, jvm_options=None):
        self.scenario = scenario
        self.scenario_args = deepcopy(scenario_args)
        self.scenario_jvm_options = jvm_options
        self.start_nodes()
        self.wait_scenario_started()

    def wait_scenario_started(self):
        started_log_message = f'Simulation {self.scenario} started...'
        self.wait_message(started_log_message, timeout=self.start_timeout)

    def wait_scenario_completed(self, timeout):
        completed_log_message = f'Simulation {self.scenario} completed'
        self.wait_message(completed_log_message, timeout=timeout)

    def stop(self, wait=True, timeout=120):
        if wait:
            self.wait_scenario_completed(timeout)
        self.kill_nodes()

    def get_node_args(self, node_idx):
        return f'-nr -s {self.scenario}'

    def get_node_jvm_options(self, node_idx):
        def _pack_val(arg, val):
            res = str(val)
            if ' ' in res:
                return '"' + '-D' + arg + '=' + res + '"'
            return '-D' + arg + '=' + res

        jvm_options_arr = [super().get_node_jvm_options(node_idx)]
        if self.scenario_jvm_options:
            jvm_options_arr.extend(self.scenario_jvm_options)
        jvm_options_arr.extend([
            _pack_val(arg, val) for arg, val in self.scenario_args.items()
        ])

        return ' '.join(jvm_options_arr)

    def fetch_simulation_results(self, unpack=True):
        """
        Fetch Gatling simulation results to test directory
        :param unpack: unpack fetched archives after downloading
        :return: list of fetched simulation runs directories
        """
        # Gatling produces simulation results into
        # {run_dir}/results/<scenarioname>-<timestamp>/simulation.log
        # files.
        # We rename and pack each file one by one to
        # {run_dir}/results/<scenarioname>-<timestamp>/<node_id>-<timestamp>-simulation.log.tar.gz
        # removing original simulation.log files to conserve space
        # then download all files to
        # {test_dir}/results/<scenarioname>-<mintimestamp>/<node_id>-<timestamp>-simulation.log.tar.gz
        # where <mintimestamp> is min <timestamp> over nodes.
        # then unpack and remove logs one by one

        result = self.ssh.exec_at_nodes(
            self.nodes, lambda node_idx, node:
            f'if [ -d {node["run_dir"]}/results ]; then'
            f'  cd {node["run_dir"]}/results; '
            f'  ls -1 | while read dir; do'
            f'    if [ -d $dir ]; then '
            f'      stamp=$(echo $dir | cut -d "-" -f 2);'
            f'      for file in $dir/*.*; do'
            f'         if [ -f $file ]; then'
            f'           res_file=$(dirname $file)/{node_idx}-$stamp-$(basename $file);'
            f'           mv $file $res_file;'
            f'           cd $(dirname $res_file);'
            f'           tar -czf $(basename $res_file).tar.gz $(basename $res_file) 2>>pack_errors.txt 1>&2;'
            f'           res=$?; '
            f'           cd {node["run_dir"]}/results;'
            f'           if [ $res -eq 0 ]; then'
            f'             rm $res_file;'
            f'             echo $res_file.tar.gz;'
            f'           fi;'
            f'        fi;'
            f'      done;'
            f'    fi;'
            f'  done;'
            f'fi'
        )
        scenarios_files = self._get_scenarios_files(result)

        for scenario_name, scenario_files in scenarios_files.items():
            local_path = path.join(self.test_dir, 'results', scenario_name)
            makedirs(local_path, exist_ok=True)
            self.ssh.download_from_nodes(self.nodes, scenario_files, local_path)

        return scenarios_files.keys()

    def _get_scenarios_files(self, results):
        scenario_files = {}
        all_data = {
            node_id: node_data.rstrip().splitlines() for node_id, node_data in results.items()
        }
        if not all_data:
            return {}
        scenario_count = 0
        scenario_names = {}
        scenario_data = {}
        for node_id, node_data in all_data.items():
            node_scenario_dirnames = {}
            for filepath in node_data:
                if '/' not in filepath:
                    continue
                dir_name, filename = filepath.split('/')
                if dir_name not in node_scenario_dirnames.keys():
                    node_scenario_dirnames[dir_name] = []
                node_scenario_dirnames[dir_name].append(dir_name + '/' + filename)
            node_scenario_count = len(node_scenario_dirnames)
            if scenario_count < node_scenario_count:
                scenario_count = node_scenario_count
            for scenario_n, dir_name in enumerate(node_scenario_dirnames):
                if scenario_n not in scenario_names:
                    scenario_names[scenario_n] = []
                scenario_names[scenario_n].append(dir_name)
                if scenario_n not in scenario_data:
                    scenario_data[scenario_n] = {}
                scenario_data[scenario_n][node_id] = node_scenario_dirnames[dir_name].copy()

        for scenario_n, scenario_node_names in scenario_names.items():
            min_timestamp = None
            scenario_name = None
            for scenario_node_name in scenario_node_names:
                if '-' not in scenario_node_name:
                    continue
                node_scenario_name, node_timestamp = scenario_node_name.split('-')
                if scenario_name is None:
                    scenario_name = node_scenario_name
                else:
                    if scenario_name != node_scenario_name:
                        continue
                if min_timestamp is None:
                    min_timestamp = node_timestamp
                else:
                    if int(min_timestamp) > int(node_timestamp):
                        min_timestamp = node_timestamp
            if scenario_name is None:
                continue
            scenario_name = scenario_name + '-' + min_timestamp
            scenario_files[scenario_name] = deepcopy(scenario_data[scenario_n])

        return scenario_files

    def generate_report(self, simulation_name, remove=True):
        """
        Generate HTML reports from fetched simulation results
        :param simulation_name:
        :param remove: remove original files after generation
        :return:
        """
        if type(simulation_name) == type(''):
            simulation_names = [simulation_name]
        else:
            simulation_names = simulation_name
        for simulation_name in simulation_names:
            pass
