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

# !/usr/bin/env python3

from tiden.case.generaltestcase import GeneralTestCase
from tiden.util import repeated_test
from tiden.priority_decorator import test_priority


class TestRepeatedTest(GeneralTestCase):
    pass_test_dir = []

    def test_without_decorator(self):
        self.pass_test_dir.append(self.config['rt']['test_method'])

    @repeated_test(2)
    def test_with_repeated_test(self):
        self.pass_test_dir.append('{}_{}'.format(self.config['rt']['test_method'], '1'))
        self.pass_test_dir.append('{}_{}'.format(self.config['rt']['test_method'], '2'))

    @repeated_test(2, test_names=['example'])
    def test_with_repeated_test_and_not_full_test_names(self):
        self.pass_test_dir.append('{}_{}'.format(self.config['rt']['test_method'], 'example'))
        self.pass_test_dir.append('{}_{}'.format(self.config['rt']['test_method'], '2'))

    @repeated_test(2, test_names=['first', 'second'])
    def test_with_repeated_test_and_full_test_names(self):
        self.pass_test_dir.append('{}_{}'.format(self.config['rt']['test_method'], 'first'))
        self.pass_test_dir.append('{}_{}'.format(self.config['rt']['test_method'], 'second'))

    @test_priority.LOW
    def test_check_directories(self):
        self.pass_test_dir.append(self.config['rt']['test_method'])
        result = self.ssh.exec_on_host(self.config['environment']['server_hosts'][0], [
            'ls {}/{} | grep test'.format(self.config['rt']['remote']['test_module_dir'],
                                          self.config['rt']['test_class'])])
        dir_list = ''.join(list(result.values())[0]).splitlines()
        assert set(dir_list) == set(self.pass_test_dir), 'assert list of test dirs on server and expected are equal'

