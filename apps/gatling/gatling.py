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

from tiden.apps import App, NodeStatus
from tiden import TidenException, log_print, log_put
from copy import deepcopy
from time import time, sleep
from sys import stdout


class Gatling(App):
    gatling_home = None
    gatling_jar = None
    test_dir = None

    scenario = None
    scenario_args = None
    jvm_options = None

    start_timeout = 5

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
        self.start_timeout = Gatling.start_timeout

    def setup(self):
        super().setup()
        self.gatling_jar = self.config['artifacts'][self.name]['remote_path']
        self.gatling_home = "%s/%s" % (self.config['rt']['remote']['test_module_dir'], self.name)
        self.add_nodes()

    def add_nodes(self):
        for host in self.get_hosts():
            for node_idx in range(0, self.get_servers_per_host()):
                self.add_node(host)

    def add_node(self, host=None):
        node_idx = len(self.nodes)
        self.nodes[node_idx] = {
            'host': host,
            'status': NodeStatus.NEW,
            'run_dir': "%s/%s" % (self.gatling_home, "server.%d" % node_idx)
        }

    def rotate_node_log(self, node_idx):
        run_counter = 0 if 'run_counter' not in self.nodes[node_idx] else self.nodes[node_idx]['run_counter'] + 1
        self.test_dir = self.config['rt']['remote']['test_dir']
        self.nodes[node_idx].update({
            'run_counter': run_counter,
            'log': "%s/%s" % (self.test_dir, "node.%d.%s.%d.log" % (node_idx, self.name, run_counter)),
        })

    def start(self, scenario, scenario_args, jvm_options=None):
        def _pack_val(arg, val):
            res = str(val)
            if ' ' in res:
                return '"' + '-D' + arg + '=' + res + '"'
            return '-D' + arg + '=' + res

        self.scenario = scenario
        self.scenario_args = deepcopy(scenario_args)
        self.jvm_options = Gatling.default_jvm_options.copy()
        if jvm_options:
            self.jvm_options.extend(jvm_options)
        self.jvm_options.extend([
            _pack_val(arg, val) for arg, val in self.scenario_args.items()
        ])
        self.start_nodes()
        self.wait_scenario_started()

    def wait_scenario_started(self):
        started_log_message = f'Simulation {self.scenario} started...'
        self.wait_message(started_log_message, timeout=self.start_timeout)

    def wait_scenario_completed(self, timeout):
        completed_log_message = f'Simulation {self.scenario} completed'
        self.wait_message(completed_log_message, timeout=timeout)

    def stop(self):
        self.kill_nodes()

    def _print_wait_for(self, message, node_idxs, time, timeout, done):
        log_put(f"Waiting for '{message}' at nodes [{', '.join(node_idxs)}], {time}/{timeout} sec")
        if done:
            stdout.flush()
            log_print('')

    def wait_message(self, message, nodes_idx=None, timeout=30):
        if nodes_idx is None:
            node_idxs = self.nodes.keys().copy()
        elif isinstance(nodes_idx, int):
            node_idxs = [nodes_idx]
        else:
            node_idxs = [int(node_idx) for node_idx in nodes_idx]

        self.wait_for(
            action=lambda: self.grep_log(*node_idxs, message={'regex': message}),
            condition=lambda result: all([
                node_id in result and
                'message' in result[node_id] and
                result[node_id]['message'] == message
                for node_id in node_idxs
            ]),
            timeout=timeout,
            interval=2,
            progress_ticks=3,
            progress=lambda t, done: self._print_wait_for(message, node_idxs, t, timeout, done)
        )

    def wait_for(
            self,
            condition=lambda x: True,
            action=lambda: None,
            timeout=30,
            interval=1,
            progress_ticks=5,
            progress=lambda t, done: None,
            failed=lambda x: False,
            success=lambda x: True
    ):
        end_time = time() + timeout
        i = 0
        progress(end_time - time(), False)
        try:
            while True:
                result = action()
                if condition(result):
                    return success(result)
                elif failed is not None and failed(result):
                    return False
                if time() > end_time:
                    return False
                sleep(interval)
                if progress and progress_ticks and i % progress_ticks == 0:
                    progress(end_time - time(), False)
                i += 1
        finally:
            if progress:
                progress(end_time - time(), True)

    def start_nodes(self):
        start_command = {}
        pids = {}
        nodes_to_start = []
        for node_idx, node in self.nodes.items():
            self.rotate_node_log(node_idx)
            nodes_to_start.append(node_idx)
            host = node['host']
            if host not in start_command:
                start_command[host] = []
            start_command[host].extend(self.get_node_start_commands(node_idx))
            pids[node_idx] = len(start_command[host]) - 1
            node['status'] = NodeStatus.STARTING
        log_print("Start gatling node(s): %s" % nodes_to_start)
        result = self.ssh.exec(start_command)
        for node_idx, node in self.nodes.items():
            host = node['host']
            node['pid'] = int(result[host][pids[node_idx]].strip())
            if not node['pid']:
                raise TidenException(f"Can't start application {self.name} node {node_idx} at host {host}")
        check_command = {}
        status = {}
        for node_idx, node in self.nodes.items():
            host = node['host']
            if host not in check_command:
                check_command[host] = []
            check_command[host].extend(self.get_node_check_commands(node_idx))
            status[node_idx] = len(check_command[host]) - 1
        result = self.ssh.exec(check_command)
        for node_idx, node in self.nodes.items():
            host = node['host']
            if not result[host][status[node_idx]]:
                raise TidenException(f"Can't start application {self.name} node {node_idx} at host {host}")
            node['status'] = NodeStatus.STARTED
            log_print(f"Gatling node {node_idx} started on {host} with PID {node['pid']}")

    def start_node(self, node_idx):
        self.rotate_node_log(node_idx)
        node = self.nodes[node_idx]
        host = node['host']
        start_commands = self.get_node_start_commands(node_idx)
        start_command = {host: start_commands}
        node['status'] = NodeStatus.STARTING
        log_print("Start gatling node(s): %s" % [node_idx])
        result = self.ssh.exec(start_command)
        node['pid'] = int(result[host][len(start_commands) - 1].strip())
        check_commands = self.get_node_check_commands(node_idx)
        check_command = {host: check_commands}
        result = self.ssh.exec(check_command)
        if not result[host][0]:
            raise TidenException(f"Can't start application {self.name} node {node_idx} at host {host}")
        node['status'] = NodeStatus.STARTED
        log_print(f"Gatling node {node_idx} started on {host} with PID {node['pid']}")

    def get_node_check_commands(self, node_idx):
        return [
            'sleep 1; pid -p %d -f | grep java 2>/dev/null' % self.nodes[node_idx]['pid'],
        ]

    def get_node_start_commands(self, node_idx):
        return [
            'mkdir -p %s' % self.nodes[node_idx]['run_dir'],
            'cd %s; nohup java %s -cp %s %s -nr -s %s 1>%s 2>&1 & echo $!' % (
                self.nodes[node_idx]['run_dir'],
                ' '.join(self.jvm_options),
                self.gatling_jar,
                self.class_name,
                self.scenario,
                self.nodes[node_idx]['log'],
            ),
        ]

    def get_servers_per_host(self):
        if 'gatling' in self.config['environment']:
            return int(self.config['environment']['gatling'].get('servers_per_host', 1))
        else:
            return int(self.config['environment'].get('servers_per_host', 1))

    def check_requirements(self):
        self.require_artifact('gatling')

    def get_hosts(self):
        if 'gatling' in self.config['environment']:
            return self.config['environment']['gatling'].get('server_hosts', [])
        else:
            return self.config['environment'].get('server_hosts', [])

