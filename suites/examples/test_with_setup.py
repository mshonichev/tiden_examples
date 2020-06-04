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
from tiden.util import with_setup, known_issue


class TestWithSetup(GeneralTestCase):

    check_string = None

    def setup_test(self, **kwargs):
        self.check_string = kwargs

    def teardown(self):
        pass

    def test_without_with_setup(self):
        pass

    @with_setup(setup_test)
    def test_with_setup(self):
        pass

    @with_setup(setup_test, teardown)
    def test_with_setup_teardown(self):
        pass

    @with_setup(setup_test, LoadFactor=1.0)
    def test_with_setup_kwarg(self):
        assert self.check_string == {'LoadFactor': 1.0}, 'test kwarg != setup kwarg'

    @with_setup(setup_test, teardown, LoadFactor=1.0)
    def test_with_setup_teardown_kwarg(self):
        assert self.check_string == {'LoadFactor': 1.0}, 'test kwarg != setup kwarg'

    @with_setup(setup_test, LoadFactor=1.0, SnapshotCreationType='-single-partition')
    def test_with_setup_kwargs(self):
        print(self.check_string)
        assert self.check_string == {'LoadFactor': 1.0,
                                     'SnapshotCreationType': '-single-partition'}, 'test kwarg != setup kwarg'

    @with_setup(setup_test, teardown, LoadFactor=1.0, SnapshotCreationType='-archive')
    def test_with_setup_teardown_kwargs(self):
        print(self.check_string)
        assert self.check_string == {'LoadFactor': 1.0, 'SnapshotCreationType': '-archive'}, 'test kwarg != setup kwarg'

    @known_issue('IGN-0')
    def test_known_issue_passed(self):
        pass

    @known_issue('IGN-1')
    def test_known_issue_passed(self):
        assert False

