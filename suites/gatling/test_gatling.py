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
from tiden.case.apptestcase import AppTestCase
from tiden.util import log_print, with_setup


class TestGatling (AppTestCase):

    ignite_app: Ignite = property(lambda self: self.get_app('ignite'), None)
    gatling_app: Gatling = property(lambda self: self.get_app('gatling'), None)

    def __init__(self, *args):
        super().__init__(*args)
        self.add_app('gatling')
        self.add_app('ignite')

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
        rest_host = self.ignite_app.nodes[1]['host']
        rest_port = self.ignite_app.nodes[1]['rest_port']
        load_url = f"http://{rest_host}:{rest_port}/ignite?cmd=top"
        log_print(f"Starting HTTP Load -> {load_url}")
        duration = 60
        self.gatling_app.start(
            scenario="perftest.HttpLoadScenario",
            scenario_args={
                "base_url": load_url,
                "duration": duration,
                "load_factor": 100,
                "load_throttle": 5,
                "page_name": "Cluster topology"
            },
        )
        self.gatling_app.wait_scenario_completed(timeout=duration + 10)
        simulation_results = self.gatling_app.fetch_simulation_results()
        self.gatling_app.generate_report(simulation_results)
