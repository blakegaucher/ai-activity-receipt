"""Review candidate: main builds/runs Docker only after separate owner approval.

Public baseline-only context; no registry credentials/push, models or scoring.
Importing this module does not build or run an image.
"""
import argparse
import base64
import dataclasses
import hashlib
import importlib.metadata
import json
import os
from pathlib import Path
import platform
import shutil
import subprocess
import sys
import time

TRACK = '1c744e1d6725340643a533f436517d72b53ca0e1'
TOOLKIT = '50fb2dc2b39c70f4cf81fcd269943782eddfaed0'
BASE = 'python:3.13.15-slim@sha256:37134a49d21d2120e4c4d73bb76f8a4ab9aef31f096f7ec2ead48c2feead4332'
ANSWER = 'e305c47d7dfca92e73b3304d24f937b26f0bf861082649e06629c92eae91b3d2'
SCHEMA = '8a997f21a929f09596db805430839b281548ad0babab29bd1f3daa8456d38049'


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def require(condition, message):
    # Guards remain active even if an interpreter is invoked with -O.
    if not condition:
        raise RuntimeError(message)


def base_ok(value):
    return value == BASE


def _text(value):
    return value.decode('utf-8', errors='replace') if isinstance(value, bytes) else (value or '')


def command(argv, report, env, timeout=60):
    start = time.monotonic()
    event = {'argv': argv, 'timeout_seconds': timeout}
    try:
        result = subprocess.run(argv, capture_output=True, text=True, env=env, timeout=timeout)
        event.update(exit=result.returncode, stdout=result.stdout, stderr=result.stderr)
        result.check_returncode()
        return result.stdout
    except subprocess.TimeoutExpired as exc:
        event.update(failure='TimeoutExpired', stdout=_text(exc.stdout), stderr=_text(exc.stderr))
        raise
    except Exception as exc:
        event.setdefault('failure', type(exc).__name__)
        raise
    finally:
        event['seconds'] = time.monotonic() - start
        report['events'].append(event)


def cleanup_containers(names, report, env):
    # Cleanup cannot mask the primary failure or prevent its evidence from being written.
    for name in reversed(names):
        try:
            command(['docker', 'rm', '-f', name], report, env, timeout=30)
        except Exception as exc:
            report.setdefault('cleanup_failures', []).append({'name': name, 'type': type(exc).__name__, 'message': str(exc)})
    if report.get('cleanup_failures'):
        report['status'] = 'FAILED'


def sandbox_args(name):
    return ['docker', 'run', '--name', name, '--platform', 'linux/amd64',
            '--read-only', '--user', '65534:65534', '--cap-drop=ALL',
            '--security-opt', 'no-new-privileges', '--runtime', 'runc',
            '--tmpfs', '/tmp:rw,noexec,nosuid,nodev,size=64m',
            '--pids-limit', '256', '--ulimit', 'nofile=1024:1024',
            '--ulimit', 'nproc=256:256', '--ulimit', 'fsize=67108864:67108864',
            '--cpus', '2', '--memory', '4g', '--memory-swap', '4g', '--network', 'none']


def run_args(image, unit, output, name):
    return sandbox_args(name) + [
            '--mount', f'type=bind,src={unit},dst=/input,readonly',
            '--mount', f'type=bind,src={output},dst=/output',
            '-e', 'QFBENCH_SEED=0', '-e', 'QFBENCH_NETWORK=none', image,
            'analyze', '--task', '/input/task.json', '--corpus', '/input/corpus',
            '--out', '/output/answer.json']


def tree_hashes(root):
    files = list(root.rglob('*'))
    require(all(not p.is_symlink() for p in files), 'Symlink in isolated public input/context')
    return {str(p.relative_to(root)): digest(p) for p in sorted(files) if p.is_file()}


def main():
    parser = argparse.ArgumentParser()
    for key in ['track', 'toolkit', 'dockerfile', 'base', 'evidence']:
        parser.add_argument('--' + key, required=True)
    args = parser.parse_args()
    if not base_ok(args.base):
        parser.error('base must equal the exact reviewed Python Linux/amd64 manifest reference')
    track, toolkit = Path(args.track).resolve(), Path(args.toolkit).resolve()
    evidence = Path(args.evidence).resolve()
    evidence.mkdir(parents=True, exist_ok=False)
    report = {'status': 'FAILED', 'scope': '5.2.2 bounded participant-container interface only',
              'production_parity': 'NOT LOCALLY ATTESTABLE', 'events': [],
              'source_pins': {'track': TRACK, 'toolkit_v2.5.1': TOOLKIT, 'base': BASE}}
    env = dict(os.environ)
    env.update(DOCKER_CONFIG=str(evidence / 'empty-docker-config'), HF_HUB_OFFLINE='1',
               TRANSFORMERS_OFFLINE='1', PYTHONDONTWRITEBYTECODE='1')
    Path(env['DOCKER_CONFIG']).mkdir()
    names = []
    primary_failure = None
    try:
        require(platform.python_version() == '3.13.15', 'Host checker Python mismatch')
        for root, expected in [(track, TRACK), (toolkit, TOOLKIT)]:
            require(command(['git', '-C', str(root), 'rev-parse', 'HEAD'], report, env).strip() == expected, 'Source commit mismatch')
            require(not command(['git', '-C', str(root), 'status', '--porcelain'], report, env).strip(), 'Source checkout is dirty')
        latest = command(['git', 'ls-remote', 'https://github.com/Agenthon-2026/track4-analysis-public.git', 'refs/heads/main'], report, env)
        require(latest.split()[0] == TRACK, 'Official Track 4 main advanced: stop before Docker')
        report['docker'] = command(['docker', 'version'], report, env)
        report['host'] = {'uname': command(['uname', '-a'], report, env), 'python': sys.version,
                          'python_executable': sys.executable, 'cpu_count': os.cpu_count(),
                          'memory': Path('/proc/meminfo').read_text(),
                          'installed_versions': {d.metadata['Name']: d.version for d in importlib.metadata.distributions()}}
        require(importlib.metadata.version('qfbench2-common') == '2.5.1', 'Toolkit version mismatch')
        schema = toolkit / 'common/qfbench2_common/schemas/analysis.schema.json'
        require(digest(schema) == SCHEMA, 'Current Analysis schema byte mismatch')
        context = evidence / 'context'
        context.mkdir()
        tree_hashes(track / 'baselines/baseline_agent')
        shutil.copytree(track / 'baselines/baseline_agent', context / 'baseline_agent', ignore=shutil.ignore_patterns('__pycache__'))
        shutil.copy2(track / 'baselines/baseline_agent.py', context / 'baseline_agent.py')
        shutil.copy2(args.dockerfile, context / 'Dockerfile')
        report['build_context_hashes'] = tree_hashes(context)
        unit = track / 'units/t4-EXAMPLE-eps-beat'
        before = tree_hashes(unit)
        report['input_hashes'] = before
        command(['docker', 'build', '--platform', 'linux/amd64', '--pull', '--build-arg',
                 'PYTHON_BASE=' + args.base, '--tag', 'agenthon-smoke:local', str(context)], report, env, timeout=600)
        info = json.loads(command(['docker', 'image', 'inspect', 'agenthon-smoke:local'], report, env))[0]
        require(info['Architecture'] == 'amd64' and info['Os'] == 'linux', 'Built image platform mismatch')
        require(info['Config']['Labels']['qfbench2.interface_version'] == '2.0', 'Interface label mismatch')
        report['image'] = info
        probe_name = 'agenthon-python-probe'
        names.append(probe_name)  # Also cleaned if the client times out during creation/run.
        report['container_python'] = command(sandbox_args(probe_name) + ['--entrypoint', 'python', info['Id'], '--version'], report, env, timeout=60).strip()
        require(report['container_python'] == 'Python 3.13.15', 'Runtime interpreter mismatch')
        report['python_probe_inspect'] = json.loads(command(['docker', 'inspect', probe_name], report, env))
        report['base_image'] = json.loads(command(['docker', 'image', 'inspect', args.base], report, env))
        report['identity_boundary'] = 'Local image ID/config digest only; no participant registry manifest was created or pushed'
        output = evidence / 'output'
        output.mkdir(mode=0o777)
        output.chmod(0o777)  # Only this task-created empty output directory.
        name = 'agenthon-bounded-smoke'
        names.append(name)
        command(run_args(info['Id'], unit, output, name), report, env, timeout=600)
        report['container_inspect'] = json.loads(command(['docker', 'inspect', name], report, env))
        after = tree_hashes(unit)
        report['input_hashes_after'] = after
        require(before == after, 'Public corpus/input bytes changed')
        files = list(output.rglob('*'))
        require(all(not p.is_symlink() for p in files), 'Output contains a symlink')
        require({str(p.relative_to(output)) for p in files} == {'answer.json'}, 'Output tree differs from required answer.json')
        answer_path = output / 'answer.json'
        require(answer_path.stat().st_size <= 64 * 1024 * 1024, 'Aggregate output exceeds 64 MiB')
        report['answer_sha256'] = digest(answer_path)
        report['answer_bytes_base64'] = base64.b64encode(answer_path.read_bytes()).decode('ascii')
        require(report['answer_sha256'] == ANSWER, 'Changed answer bytes; preserve failure without normalization')
        answer = json.loads(answer_path.read_text())
        sys.path.insert(0, str(track))
        import jsonschema
        schema_data = json.loads(schema.read_text())
        jsonschema.Draft202012Validator.check_schema(schema_data)
        errors = [{'path': list(e.absolute_path), 'message': e.message}
                  for e in jsonschema.Draft202012Validator(schema_data).iter_errors(answer)]
        report['schema_errors'] = errors
        require(not errors, 'Draft 2020-12 schema failed')
        from baselines.guardrails_example.citation_rail import check_claim_rules
        findings = [dataclasses.asdict(f) for f in check_claim_rules(answer, unit, token_counter=None)]
        report['claim_findings'] = findings
        require(all(f['code'] == 'claim_tokens_unchecked' for f in findings), 'Unexpected deterministic claim finding')
        report['token_boundary'] = ('No fresh tokenizer/NLI run. October 2 local 37/37 evidence remains historical '\n                                    'under its prior exact source pin; this pin-advanced smoke does not relabel that '\n                                    'evidence or attest current-source tokenizer/NLI parity.')
        report['limits'] = {'cpus': 2, 'memory_gib': 4, 'smoke_timeout_seconds': 600,
                            'build_timeout_seconds': 600, 'probe_timeout_seconds': 60,
                            'cleanup_timeout_per_container_seconds': 30,
                            'parity': 'lower-resource offline smoke; organizer 16 CPU/128 GiB/House/GPU/Final parity unverified'}
        report['status'] = 'CONTAINER_SMOKE_PASS_NOT_COMPETITION_SCORE'
    except Exception as exc:
        primary_failure = exc
        report['failure'] = {'type': type(exc).__name__, 'message': str(exc)}
    finally:
        cleanup_containers(names, report, env)
        report_path = evidence / 'report.json'
        report_path.write_text(json.dumps(report, indent=2) + '\n')
        print(json.dumps(report, indent=2))
        print('REPORT_SHA256', digest(report_path))
    if primary_failure is not None:
        raise primary_failure
    require(report['status'] == 'CONTAINER_SMOKE_PASS_NOT_COMPETITION_SCORE', 'Cleanup failed; retained evidence, no PASS')


if __name__ == '__main__':
    main()