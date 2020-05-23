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

    @known_issue('GG-0')
    def test_known_issue_passed(self):
        pass
