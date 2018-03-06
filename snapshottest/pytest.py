from __future__ import absolute_import
import pytest

from .module import SnapshotModule, SnapshotTest
from .diff import PrettyDiff
from .reporting import reporting_lines, diff_report


def pytest_addoption(parser):
    group = parser.getgroup('snapshottest')
    group.addoption(
        '--snapshot-update',
        action='store_true',
        default=False,
        dest='snapshot_update',
        help='Update the snapshots.'
    )
    group.addoption(
        '--snapshot-verbose',
        action='store_true',
        default=False,
        help='Dump diagnostic and progress information.'
    )


class PyTestSnapshotTest(SnapshotTest):

    def __init__(self, request=None):
        self.request = request
        super(PyTestSnapshotTest, self).__init__()

    @property
    def module(self):
        module_path = self.request.node.fspath.strpath
        if getattr(self.request.config.inicfg, 'config', False) and \
           self.request.config.inicfg.config.sections.has_key('snapshottest') and \
           self.request.config.inicfg.config.sections['snapshottest'].has_key('snapshot_parent_dir'):
            module_path = self.request.config.inicfg.config.sections['snapshottest']['snapshot_parent_dir']
        return SnapshotModule.get_module_for_testpath(module_path)

    @property
    def update(self):
        return self.request.config.option.snapshot_update

    @property
    def test_name(self):
        cls_name = getattr(self.request.node.cls, '__name__', '')
        return '{}{} {}'.format(
            '{}.'.format(cls_name) if cls_name else '',
            self.request.node.name,
            self.curr_snapshot
        )


class SnapshotSession(object):
    def __init__(self, config):
        self.verbose = config.getoption("snapshot_verbose")
        self.config = config

    def display(self, tr):
        if not SnapshotModule.has_snapshots():
            return

        tr.write_sep("=", "SnapshotTest summary")

        for line in reporting_lines('pytest'):
            tr.write_line(line)


def pytest_assertrepr_compare(op, left, right):
    if isinstance(left, PrettyDiff) and op == "==":
        return diff_report(left, right)


@pytest.fixture
def snapshot(request):
    with PyTestSnapshotTest(request) as snapshot_test:
        yield snapshot_test


def pytest_terminal_summary(terminalreporter):
    if terminalreporter.config.option.snapshot_update:
        for module in SnapshotModule.get_modules():
            module.delete_unvisited()
            module.save()

    terminalreporter.config._snapshotsession.display(terminalreporter)


@pytest.mark.trylast  # force the other plugins to initialise, fixes issue with capture not being properly initialised
def pytest_configure(config):
    config._snapshotsession = SnapshotSession(config)
    # config.pluginmanager.register(bs, "snapshottest")
