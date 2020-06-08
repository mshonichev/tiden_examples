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

from apps.gatling import Gatling
from tiden.apps.ignite import Ignite
from tiden.apps.profiler import Profiler
from tiden.case.apptestcase import AppTestCase
from tiden.util import log_print, with_setup
from os import path, makedirs


class TestGatling (AppTestCase):

    ignite_app: Ignite = property(lambda self: self.get_app('ignite'), None)
    gatling_app: Gatling = property(lambda self: self.get_app('gatling'), None)
    profiler_app: Profiler = property(lambda self: self.get_app('profiler'), None)

    def __init__(self, *args):
        super().__init__(*args)
        self.add_app('gatling')
        self.add_app('ignite')
        if self.has_profiler():
            self.add_app('profiler', profiler='async_flamegraph')

    def setup(self):
        self.create_app_config_set(
            Ignite,
            addresses=self.ignite_app.get_hosts('server'),
            zookeeper_enabled=False,
        )
        super().setup()

    def setup_test(self):
        self.ignite_app.set_node_option(
            '*', 'config', Ignite.config_builder.get_config('server')
        )
        self.ignite_app.start_nodes()
        self.ignite_app.cu.activate()

    def teardown_test(self):
        self.gatling_app.stop(wait=False)
        self.ignite_app.stop_nodes(force=True)

    @with_setup(setup_test, teardown_test)
    def test_run_gatling_test(self):
        """
        Start Ignite, put some load onto REST endpoint
        """
        duration = 120
        warmup = 60
        cooldown = 10

        if self.has_profiler():
            log_print(f"Start profiling Ignite nodes")
            self.profiler_app.update_options(nodes=self.ignite_app.nodes, warmup=warmup, duration=duration-cooldown)
            self.profiler_app.start()

        rest_port = self.ignite_app.nodes[1]['rest_port']
        rest_host = self.ignite_app.nodes[1]['host']
        load_url = f"http://{rest_host}:{rest_port}/ignite?cmd=top"
        log_print(f"Starting HTTP Load -> {load_url}")
        self.gatling_app.start(
            scenario="perftest.HttpLoadScenario",
            scenario_args={
                "base_url": load_url,
                "duration": duration + warmup,
                "load_factor": 100,                 # number of virtual users
                "load_throttle": 2,                 # delay between requests
                "page_name": "Cluster topology"
            },
        )

        self.gatling_app.wait_scenario_completed(timeout=duration + warmup + cooldown)

        simulation_results = self.gatling_app.fetch_simulation_results()
        simulation_report = self.gatling_app.generate_report(simulation_results)
        for simulation_name, simulation_stats in simulation_report.items():
            log_print(f'Simulation \'{simulation_name}\' statistics', color='green')
            for line in simulation_stats:
                log_print(line, color='green')
            log_print(f'Detailed report: file:///{self.gatling_app.test_dir}/results/{simulation_name}/index.html')

        if self.has_profiler():
            profiling_files = self.tiden.ssh.ls(dir_path=self.profiler_app.remote_test_dir + '/*.svg', params='-1')
            local_dir = path.join(self.profiler_app.test_dir, 'profile')
            makedirs(local_dir, exist_ok=True)
            local_profiling_files = self.tiden.ssh.download(profiling_files, local_dir)
            for file in local_profiling_files:
                log_print(f'Flamegraph: file:///{self.profiler_app.test_dir}/profile/{file}')

    def has_profiler(self):
        return 'flamegraph' in self.tiden.config['artifacts']
