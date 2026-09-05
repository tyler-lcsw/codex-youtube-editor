"""Evidence-based production gates driven by docs/production-rules.md at runtime.

This coordinates review; it cannot establish the truth of a reviewer's judgment.
Raw media utilities remain usable for diagnostics, not a substitute for this workflow.
"""
import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import re
import subprocess
import uuid
from .jobs import file_hash
from .run_state import atomic_json, file_lock
from .runtime.worker import terminate_group

ROOT = Path(__file__).resolve().parents[1]
RULES = ROOT / 'docs/production-rules.md'
PHASES = ('before', 'during', 'after')
ACCEPTED = {'before': {'planned', 'not_applicable'},
            'during': {'pass', 'not_applicable'}, 'after': {'pass', 'not_applicable'}}


def now():
    return datetime.now(timezone.utc).isoformat()


def read_rules(path=RULES):
    path = Path(path); raw = path.read_bytes(); text = raw.decode('utf-8')
    if any(not re.fullmatch(r'## R\d+\s*', h) for h in re.findall(r'^## .*$', text, re.M)):
        raise ValueError('Every second-level heading must be a stable rule ID')
    blocks = re.split(r'^## (R\d+)\s*$', text, flags=re.M)
    rules = []; seen = set()
    for i in range(1, len(blocks), 2):
        key, rule = blocks[i], blocks[i + 1].strip()
        if key in seen or not rule.startswith('DO ') or '\n## ' in rule:
            raise ValueError('Rules need unique stable R IDs and text starting with DO or DO NOT')
        seen.add(key); rules.append({'id': key, 'rule': rule})
    if not rules:
        raise ValueError('No production rules found; refusing empty policy')
    metadata = re.findall(r'<!-- final-required: (.*?) -->', blocks[0])
    required = metadata[0].split() if len(metadata) == 1 else []
    if len(metadata) > 1 or not set(required) <= seen:
        raise ValueError('Invalid final-required rule IDs')
    return {'path': str(path.resolve()), 'sha256': hashlib.sha256(raw).hexdigest(), 'rules': rules, 'final_required': required}


def folder(project):
    return Path(project).resolve() / 'work/quality'


def state(project):
    p = folder(project) / 'state.json'
    return json.loads(p.read_text()) if p.exists() else {
        'schema_version': 1, 'revision': 0, 'reviews': {p: {} for p in PHASES},
        'actions': [], 'deliverables': [], 'status': 'unreviewed'}


def save(project, data):
    atomic_json(folder(project) / 'state.json', data)


def snapshot(paths):
    result = []
    for path in paths:
        p = Path(path).resolve()
        if not p.is_file() or p.stat().st_size == 0:
            raise ValueError(f'Missing or empty evidence/artifact: {p}')
        result.append({'path': str(p), 'sha256': file_hash(p)})
    return result


def current(items):
    try:
        return bool(items) and snapshot([x['path'] for x in items]) == items
    except (OSError, ValueError, KeyError):
        return False


def checklist(project, phase, rules_path=RULES):
    if phase not in PHASES:
        raise ValueError('Unknown phase')
    policy = read_rules(rules_path); data = state(project)
    return {'phase': phase, 'policy_sha256': policy['sha256'], 'policy_path': policy['path'], 'final_required': policy['final_required'],
            'instructions': 'Read every rule. Record individual reasons and evidence. Pending is not a pass. Evidence paths resolve from the command working directory.',
            'rules': [{**r, 'previous_review': data['reviews'][phase].get(r['id']),
                       'status': 'pending', 'reason': '', 'evidence': []} for r in policy['rules']]}


def record(project, phase, entries, reviewer, rules_path=RULES):
    if phase not in PHASES or not isinstance(reviewer, str) or not reviewer.strip():
        raise ValueError('Phase and named reviewer are required')
    policy = read_rules(rules_path); ids = {r['id'] for r in policy['rules']}
    pending = {}; allowed = ACCEPTED[phase] | {'pending', 'fail'}
    for entry in entries:
        key = entry.get('id')
        if key not in ids or key in pending or entry.get('status') not in allowed:
            raise ValueError('Unknown/duplicate rule or invalid disposition')
        if not isinstance(entry.get('reason'), str) or not entry['reason'].strip():
            raise ValueError('Every disposition needs an individual explanation')
        evidence = snapshot(entry.get('evidence', []))
        if not evidence:
            raise ValueError('Every disposition needs a durable evidence file, including non-applicability')
        pending[key] = {k: entry[k] for k in ('status', 'reason')}
        pending[key].update(evidence=evidence, reviewer=reviewer, time=now(), policy_sha256=policy['sha256'])
    if not pending:
        raise ValueError('No review entries')
    with file_lock(folder(project) / '.lock'):
        data = state(project)
        for key, review in pending.items():
            review.update(revision=data['revision'], deliverables=data['deliverables'])
            data['reviews'][phase][key] = review
        data['status'] = 'in_review'; save(project, data)
    return gate(project, phase, rules_path)


def gate(project, phase, rules_path=RULES):
    if phase not in PHASES:
        raise ValueError('Unknown phase')
    policy = read_rules(rules_path); data = state(project); failures = []
    for rule in policy['rules']:
        review = data['reviews'][phase].get(rule['id'])
        reason = None
        if not review: reason = 'missing review'
        elif review['policy_sha256'] != policy['sha256']: reason = 'rules changed; reread and reassess'
        elif review['status'] not in ACCEPTED[phase]: reason = review['status']
        elif phase == 'after' and rule['id'] in policy['final_required'] and review['status'] != 'pass': reason = 'Final review cannot be waived'
        elif not current(review['evidence']): reason = 'evidence changed or disappeared'
        elif phase != 'before' and review['revision'] != data['revision']: reason = 'editing activity changed'
        elif phase == 'after' and review['deliverables'] != data['deliverables']: reason = 'delivery selection changed'
        if reason: failures.append({'id': rule['id'], 'reason': reason})
    if phase != 'before':
        unresolved = [a['id'] for a in data['actions'] if a['status'] != 'succeeded' and not current(a.get('resolution', {}).get('evidence', []))]
        if unresolved: failures.append({'id': 'actions', 'reason': 'Unresolved actions: ' + ', '.join(unresolved)})
    if phase == 'after' and not current(data['deliverables']):
        failures.append({'id': 'deliverables', 'reason': 'Register nonempty, unchanged delivery files before final QA'})
    return {'phase': phase, 'policy_sha256': policy['sha256'], 'passed': not failures, 'failures': failures}


def set_deliverables(project, paths, rules_path=RULES):
    read_rules(rules_path); files = snapshot(paths)
    if not files: raise ValueError('At least one deliverable is required')
    with file_lock(folder(project) / '.lock'):
        data = state(project); data['deliverables'] = files; data['status'] = 'in_review'; save(project, data)
    return files


def run_action(project, command, rule_ids, reason, evidence, rules_path=RULES, timeout=3600, stage=None):
    policy = read_rules(rules_path)
    if not command or not reason.strip() or not rule_ids or not set(rule_ids) <= {r['id'] for r in policy['rules']}:
        raise ValueError('Action needs a command, purpose and applicable current rule IDs')
    files = snapshot(evidence)
    if not files: raise ValueError('Action needs an edit plan or other durable evidence')
    # Serialize editing actions; the state lock itself is held only while writing metadata.
    with file_lock(folder(project) / '.action.lock'):
        if (Path(project).resolve() / 'work/studio/project.json').is_file():
            from .studio_workflow import require_action
            require_action(project, 'edit' if stage is None else stage)
        if not gate(project, 'before', rules_path)['passed']:
            raise ValueError('Pre-production gate failed; run checklist/gate before and resolve findings')
        action = {'id': uuid.uuid4().hex, 'command': command, 'rules': rule_ids, 'reason': reason,
                  'evidence': files, 'policy_sha256': policy['sha256'], 'started': now(), 'status': 'running'}
        with file_lock(folder(project) / '.lock'):
            data = state(project); data['revision'] += 1; data['actions'].append(action)
            data['status'] = 'editing'; save(project, data)
        process = None
        try:
            with (folder(project) / (action['id'] + '.log')).open('w') as log:
                process = subprocess.Popen(command, stdout=log, stderr=subprocess.STDOUT, start_new_session=True)
                code = process.wait(timeout=timeout)
            action.update(status='succeeded' if code == 0 else 'failed', exit_code=code)
        except BaseException as error:
            if process is not None: terminate_group(process)
            action.update(status='failed', exit_code=-1, error=type(error).__name__)
            raise
        finally:
            action['finished'] = now()
            with file_lock(folder(project) / '.lock'):
                data = state(project)
                data['actions'] = [action if a['id'] == action['id'] else a for a in data['actions']]
                save(project, data)
        return action


def resolve_action(project, action_id, reason, evidence):
    files = snapshot(evidence)
    if not reason.strip() or not files: raise ValueError('Resolution needs a reason and evidence')
    with file_lock(folder(project) / '.lock'):
        data = state(project); action = next((a for a in data['actions'] if a['id'] == action_id), None)
        if not action or action['status'] == 'running': raise ValueError('Unknown or still-running action')
        action['resolution'] = {'reason': reason, 'evidence': files, 'time': now()}
        data['status'] = 'in_review'; save(project, data)


def finalize(project, rules_path=RULES):
    with file_lock(folder(project) / '.lock'):
        checks = [gate(project, p, rules_path) for p in PHASES]
        if not all(g['passed'] for g in checks):
            raise ValueError('Cannot complete production: ' + json.dumps(checks))
        data = state(project); policy = read_rules(rules_path)
        receipt = {'status': 'qa_complete', 'time': now(), 'policy_sha256': policy['sha256'],
                   'revision': data['revision'], 'deliverables': data['deliverables'], 'checks': checks,
                   'publication_authorized': False}
        data['status'] = 'qa_complete'; save(project, data)
        atomic_json(folder(project) / 'completion.json', receipt)
        return receipt


def require_complete(project):
    p = folder(project) / 'completion.json'
    if not p.exists(): raise ValueError('Final production QA receipt required')
    receipt = json.loads(p.read_text()); data = state(project)
    if (receipt['policy_sha256'] != read_rules()['sha256'] or receipt['revision'] != data['revision']
            or receipt['deliverables'] != data['deliverables'] or data['status'] != 'qa_complete'
            or not all(gate(project, phase)['passed'] for phase in PHASES)):
        raise ValueError('Production QA is stale or incomplete; reassess and finalize')
    return receipt


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('command', choices=['checklist', 'record', 'gate', 'run', 'deliverables', 'resolve', 'finalize', 'status'])
    p.add_argument('project', type=Path); p.add_argument('--phase', choices=PHASES, default='before')
    p.add_argument('--file', type=Path); p.add_argument('--reviewer'); p.add_argument('--rules', nargs='+')
    p.add_argument('--reason', default=''); p.add_argument('--evidence', nargs='+', default=[])
    p.add_argument('--paths', nargs='+', default=[]); p.add_argument('--action-id'); p.add_argument('--timeout', type=float, default=3600)
    p.add_argument('--stage', help='Studio workflow stage; defaults to edit for Studio projects')
    import sys
    argv = sys.argv[1:]; split = argv.index('--') if '--' in argv else len(argv)
    a = p.parse_args(argv[:split]); command = argv[split+1:]
    try:
        if a.command == 'checklist': result = checklist(a.project, a.phase)
        elif a.command == 'record':
            if not a.file: p.error('--file required')
            payload = json.loads(a.file.read_text())
            if payload.get('phase') != a.phase: raise ValueError('Checklist phase does not match requested phase')
            if payload.get('policy_sha256') != read_rules()['sha256']: raise ValueError('Checklist policy changed; generate a fresh checklist')
            result = record(a.project, a.phase, payload['rules'], a.reviewer)
        elif a.command == 'gate': result = gate(a.project, a.phase)
        elif a.command == 'run': result = run_action(a.project, command, a.rules or [], a.reason, a.evidence, timeout=a.timeout, stage=a.stage)
        elif a.command == 'deliverables': result = set_deliverables(a.project, a.paths)
        elif a.command == 'resolve': result = resolve_action(a.project, a.action_id, a.reason, a.evidence)
        elif a.command == 'finalize': result = finalize(a.project)
        else: result = {phase: gate(a.project, phase) for phase in PHASES}
        print(json.dumps(result, indent=2, ensure_ascii=False))
        if isinstance(result, dict) and (result.get('passed') is False or result.get('exit_code', 0) != 0): raise SystemExit(1)
    except (ValueError, OSError, KeyError) as error:
        p.exit(1, str(error) + '\n')

if __name__ == '__main__': main()
