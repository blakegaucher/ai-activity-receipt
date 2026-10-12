"""Source-only regression tests. Every subprocess is mocked; no Docker/network calls.

Synthetic image IDs are test fixtures, never runtime or competition evidence.
"""
import ast
import json
from pathlib import Path
import subprocess
import tempfile
import unittest
from unittest import mock

import container_gate as gate


PINNED_REFERENCE = 'python@sha256:37134a49d21d2120e4c4d73bb76f8a4ab9aef31f096f7ec2ead48c2feead4332'
PULL = ['docker', 'pull', '--platform', 'linux/amd64', PINNED_REFERENCE]
INSPECT = ['docker', 'image', 'inspect', PINNED_REFERENCE]
REPO = Path(__file__).resolve().parents[3]


def image(volumes=None, architecture='amd64', os_name='linux'):
    return {'Id': 'sha256:mock-base-not-runtime-evidence',
            'Architecture': architecture, 'Os': os_name,
            'Config': {'Volumes': volumes}}


class ContainerGateTests(unittest.TestCase):
    def setUp(self):
        # Fail closed if any test forgets to supply a subprocess fixture.
        patcher = mock.patch.object(gate.subprocess, 'run',
                                    side_effect=AssertionError('Unconfigured subprocess in source-only test'))
        self.run = patcher.start()
        self.addCleanup(patcher.stop)
        self.report = {'events': []}
        self.env = {'SOURCE_ONLY_TEST': '1'}

    def completed(self, argv, stdout='', stderr='', code=0):
        return subprocess.CompletedProcess(argv, code, stdout, stderr)

    def prepare(self, inspected):
        self.run.side_effect = [self.completed(PULL, 'mock pull only\n'),
                                self.completed(INSPECT, json.dumps(inspected))]
        gate.prepare_base_image(gate.BASE, self.report, self.env)

    def test_cold_daemon_pull_precedes_inspect(self):
        local_images = {}

        def cold_store(argv, **kwargs):
            if argv == PULL:
                local_images[PINNED_REFERENCE] = image()
                return self.completed(argv, 'mock pull only\n')
            if argv == INSPECT:
                if PINNED_REFERENCE not in local_images:
                    return self.completed(argv, '[]\n', 'mock No such image\n', 1)
                return self.completed(argv, json.dumps([local_images[PINNED_REFERENCE]]))
            raise AssertionError('Unexpected command')

        self.run.side_effect = cold_store
        gate.prepare_base_image(gate.BASE, self.report, self.env)
        self.assertEqual([c.args[0] for c in self.run.call_args_list], [PULL, INSPECT])
        self.assertEqual(self.report['base_image_reference'], PINNED_REFERENCE)
        self.assertEqual(self.report['image_volume_policy']['base']['status'], 'PASS')
        for call in self.run.call_args_list:
            self.assertEqual(call.kwargs, dict(capture_output=True, text=True,
                                               env=self.env, timeout=60))

    def test_unreviewed_or_moving_base_rejected_before_subprocess(self):
        for value in ['python:3.13.15-slim', 'python:latest', PINNED_REFERENCE,
                      gate.BASE.replace('37134a49', '47134a49')]:
            with self.subTest(value=value), self.assertRaises(RuntimeError):
                gate.prepare_base_image(value, self.report, self.env)
        self.run.assert_not_called()

    def test_pull_failure_is_preserved_without_inspect_or_retry(self):
        self.run.side_effect = [self.completed(PULL, '', 'mock unavailable\n', 1)]
        with self.assertRaises(subprocess.CalledProcessError):
            gate.prepare_base_image(gate.BASE, self.report, self.env)
        self.assertEqual(self.run.call_count, 1)
        self.assertEqual(self.report['events'][0]['stderr'], 'mock unavailable\n')
        self.assertEqual(self.report['events'][0]['exit'], 1)
        self.assertEqual(self.report['events'][0]['failure'], 'CalledProcessError')
        self.assertNotIn('base_image', self.report)

    def test_inspect_failure_is_preserved_without_retry(self):
        self.run.side_effect = [self.completed(PULL),
                                self.completed(INSPECT, '[]\n', 'mock No such image\n', 1)]
        with self.assertRaises(subprocess.CalledProcessError):
            gate.prepare_base_image(gate.BASE, self.report, self.env)
        self.assertEqual(self.run.call_count, 2)
        self.assertEqual(self.report['events'][-1]['stderr'], 'mock No such image\n')
        self.assertNotIn('base_image', self.report)

    def test_pull_timeout_is_preserved_without_retry(self):
        self.run.side_effect = subprocess.TimeoutExpired(PULL, 60,
                                                         output=b'mock partial', stderr=b'mock timeout')
        with self.assertRaises(subprocess.TimeoutExpired):
            gate.prepare_base_image(gate.BASE, self.report, self.env)
        event = self.report['events'][0]
        self.assertEqual(self.run.call_count, 1)
        self.assertEqual(event['timeout_seconds'], 60)
        self.assertEqual(event['failure'], 'TimeoutExpired')
        self.assertEqual(event['stdout'], 'mock partial')
        self.assertEqual(event['stderr'], 'mock timeout')

    def test_malformed_inspect_shapes_fail_closed(self):
        for inspected in [[], [image(), image()], {}, [None], ['not an image']]:
            with self.subTest(inspected=inspected), self.assertRaises(RuntimeError):
                self.prepare(inspected)

    def test_invalid_inspect_json_fails_closed(self):
        self.run.side_effect = [self.completed(PULL), self.completed(INSPECT, 'invalid JSON')]
        with self.assertRaises(json.JSONDecodeError):
            gate.prepare_base_image(gate.BASE, self.report, self.env)
        self.assertEqual(self.run.call_count, 2)
        self.assertEqual(len(self.report['events']), 2)

    def test_base_platform_must_be_linux_amd64(self):
        for architecture, os_name in [('arm64', 'linux'), ('amd64', 'windows'), (None, 'linux')]:
            with self.subTest(architecture=architecture, os_name=os_name), self.assertRaises(RuntimeError):
                self.prepare([image(architecture=architecture, os_name=os_name)])

    def test_null_and_empty_volumes_pass_for_both_roles(self):
        for role in ['base', 'candidate']:
            for volumes in [None, {}]:
                with self.subTest(role=role, volumes=volumes):
                    gate.require_no_declared_volumes(image(volumes), role, self.report)
                    self.assertEqual(self.report['image_volume_policy'][role]['config_volumes'], volumes)
                    self.assertEqual(self.report['image_volume_policy'][role]['status'], 'PASS')

    def test_declared_or_malformed_volumes_rejected_for_both_roles(self):
        for role in ['base', 'candidate']:
            for volumes in [{'/data': {}}, [], '', False, 0]:
                with self.subTest(role=role, volumes=volumes), self.assertRaises(RuntimeError):
                    gate.require_no_declared_volumes(image(volumes), role, self.report)
                self.assertEqual(self.report['image_volume_policy'][role]['status'], 'FAIL')

    def test_missing_or_malformed_config_rejected_for_both_roles(self):
        for role in ['base', 'candidate']:
            for inspected in [{}, {'Config': None}, {'Config': []}, {'Config': 'bad'}]:
                with self.subTest(role=role, inspected=inspected), self.assertRaises(RuntimeError):
                    gate.require_no_declared_volumes(inspected, role, self.report)

    def test_base_volumes_are_recorded_then_rejected(self):
        with self.assertRaises(RuntimeError):
            self.prepare([image({'/data': {}})])
        self.assertEqual(self.run.call_count, 2)
        self.assertEqual(self.report['base_image'][0]['Id'], 'sha256:mock-base-not-runtime-evidence')
        self.assertEqual(self.report['image_volume_policy']['base']['status'], 'FAIL')

    def test_sandbox_resource_and_network_guards_unchanged(self):
        args = gate.sandbox_args('mock-only')
        for option, value in [('--platform', 'linux/amd64'), ('--user', '65534:65534'),
                              ('--cap-drop=ALL', None), ('--security-opt', 'no-new-privileges'),
                              ('--runtime', 'runc'), ('--network', 'none'),
                              ('--cpus', '2'), ('--memory', '4g'), ('--memory-swap', '4g'),
                              ('--pids-limit', '256'), ('--read-only', None)]:
            self.assertIn(option, args)
            if value is not None:
                self.assertEqual(args[args.index(option) + 1], value)
        run = gate.run_args('mock-image', '/mock/unit', '/mock/output', 'mock-only')
        self.assertIn('type=bind,src=/mock/unit,dst=/input,readonly', run)
        self.assertIn('QFBENCH_NETWORK=none', run)
        self.assertIn('QFBENCH_SEED=0', run)
        self.run.assert_not_called()

    def test_frozen_pins_and_hash_controls_unchanged(self):
        self.assertEqual(gate.TRACK, '5d3b726a49b8ea218543e4d24319895874dcff6e')
        self.assertEqual(gate.TOOLKIT, 'bd01548e34d21fd660d88fd06157078fb25ece4e')
        self.assertEqual(gate.BASE, 'python:3.13.15-slim@sha256:37134a49d21d2120e4c4d73bb76f8a4ab9aef31f096f7ec2ead48c2feead4332')
        self.assertEqual(gate.ANSWER, 'e305c47d7dfca92e73b3304d24f937b26f0bf861082649e06629c92eae91b3d2')
        self.assertEqual(gate.SCHEMA, '8a997f21a929f09596db805430839b281548ad0babab29bd1f3daa8456d38049')

    def test_token_boundary_exactly_preserves_historical_meaning(self):
        tree = ast.parse(Path(gate.__file__).read_text())
        values = [node.value for node in ast.walk(tree) if isinstance(node, ast.Assign)
                  and any(isinstance(t, ast.Subscript) and isinstance(t.slice, ast.Constant)
                          and t.slice.value == 'token_boundary' for t in node.targets)]
        self.assertEqual(len(values), 1)
        self.assertEqual(ast.literal_eval(values[0]),
                         'No fresh tokenizer/NLI run. October 2 local 37/37 evidence remains historical '
                         'under its prior exact source pin; this pin-advanced smoke does not relabel that '
                         'evidence or attest current-source tokenizer/NLI parity.')

    def test_main_keeps_checks_before_build_and_execution(self):
        source = Path(gate.__file__).read_text()
        self.assertLess(source.index("require(digest(schema) == SCHEMA"), source.index('prepare_base_image(args.base'))
        self.assertLess(source.index('prepare_base_image(args.base'), source.index("command(['docker', 'build'"))
        self.assertLess(source.index("require_no_declared_volumes(info, 'candidate'"),
                        source.index("probe_name = 'agenthon-python-probe'"))
        self.assertIn("unit = track / 'units/t4-EXAMPLE-eps-beat'", source)
        self.assertIn("track / 'baselines/baseline_agent'", source)
        self.assertIn("require(before == after, 'Public corpus/input bytes changed')", source)
        self.assertIn("require(report['answer_sha256'] == ANSWER", source)
        self.assertIn('cleanup_containers(names, report, env)', source)
        self.assertIn('raise primary_failure', source)

    def test_manual_workflow_keeps_exact_authorization_guards(self):
        workflow = (REPO / '.github/workflows/agenthon-container-smoke.yml').read_text()
        tree = workflow.split('on:\n', 1)[1].split('\npermissions:', 1)[0]
        self.assertIn('  workflow_dispatch:', tree)
        self.assertNotIn('push:', tree)
        self.assertNotIn('pull_request:', tree)
        self.assertNotIn('schedule:', tree)
        for guard in ["github.repository == 'blakegaucher/ai-activity-receipt'",
                      "github.ref == 'refs/heads/competition/agenthon-container-530-toolkit260-draft'",
                      'github.sha == inputs.approved_commit',
                      "inputs.confirmation == 'CONTAINER_ONLY'", 'github.event.repository.private == false']:
            self.assertIn(guard, workflow)
        self.assertIn(gate.TRACK, workflow)
        self.assertIn(gate.TOOLKIT, workflow)
        self.assertIn(gate.BASE, workflow)
        self.assertIn('cancel-in-progress: false', workflow)
        self.assertNotIn('docker push', workflow)
        self.assertNotIn('docker login', workflow)

    def test_ci_compiles_helper_and_runs_only_mocked_regressions(self):
        ci = (REPO / '.github/workflows/validate-receipts.yml').read_text()
        self.assertIn('python -m compileall -q validate_receipts.py derive_receipt.py adapters mappings research benchmark competition/agenthon/container', ci)
        self.assertIn("python -m unittest discover -s competition/agenthon/container -p 'test_container_gate.py' -v", ci)
        self.assertNotIn('container_gate.py\n', ci)

    def test_public_baseline_license_is_included_without_vendoring_task_data(self):
        source = Path(gate.__file__).read_text()
        dockerfile = (Path(__file__).parent / 'Dockerfile').read_text()
        self.assertIn("shutil.copy2(track / 'LICENSE', context / 'LICENSE')", source)
        self.assertIn('COPY LICENSE ./LICENSE', dockerfile)
        self.assertNotIn('COPY units', dockerfile)
        self.assertNotIn('VOLUME', dockerfile)
        self.assertNotIn('RUN ', dockerfile)

    def test_cleanup_failure_does_not_mask_primary_failure(self):
        self.report['failure'] = {'type': 'MockPrimaryFailure', 'message': 'mock only'}
        self.run.side_effect = [self.completed(['docker', 'rm', '-f', 'mock-only'], '', 'mock cleanup failure', 1)]
        gate.cleanup_containers(['mock-only'], self.report, self.env)
        self.assertEqual(self.report['failure']['type'], 'MockPrimaryFailure')
        self.assertEqual(self.report['status'], 'FAILED')
        self.assertEqual(self.report['cleanup_failures'][0]['name'], 'mock-only')

    def test_symlink_in_context_is_rejected(self):
        with tempfile.TemporaryDirectory(prefix='agenthon-source-only-test-') as task_dir:
            root = Path(task_dir)
            (root / 'link').symlink_to(root / 'absent-mock-target')
            with self.assertRaises(RuntimeError):
                gate.tree_hashes(root)
        self.run.assert_not_called()


if __name__ == '__main__':
    unittest.main()
