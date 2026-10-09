"""Small snapshot index and session caches; option chains are loaded on demand."""
import csv
import hashlib
import json
import os
import tempfile
from collections.abc import Mapping
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

NY = ZoneInfo('America/New_York')


def today():
    return datetime.now(NY).date().isoformat()


def atomic_text(path, text):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, name = tempfile.mkstemp(dir=path.parent, prefix=path.name+'.', suffix='.tmp')
    try:
        with os.fdopen(fd, 'w', encoding='utf-8') as f:
            f.write(text)
        os.replace(name, path)
    finally:
        if os.path.exists(name):
            os.unlink(name)


class Snapshot(Mapping):
    def __init__(self, path, record, cache):
        self.path, self.record, self.cache = path, record, cache
        self.day = record['day']

    def __getitem__(self, key):
        if key != 'payload':
            return self.record['header'][key]
        if self.cache.get('path') != self.path:
            obj = json.loads(self.path.read_text(encoding='utf-8'))
            self.cache.clear()
            self.cache.update(path=self.path, payload=obj['payload'])
        return self.cache['payload']

    def __iter__(self):
        return iter([*self.record['header'], 'payload'])

    def __len__(self):
        return len(self.record['header'])+1


def snapshot_refs(directory, pattern, cache_path=None, skip_invalid=False):
    directory = Path(directory)
    cache_path = Path(cache_path or directory/'.session-index.json')
    try:
        previous = json.loads(cache_path.read_text())
    except (OSError, ValueError):
        previous = {}
    records, shared, refs = {}, {}, []
    for path in sorted(directory.glob(pattern)):
        stat = path.stat()
        stamp = [stat.st_size, stat.st_mtime_ns]
        record = previous.get(path.name)
        if not record or record.get('stamp') != stamp:
            try:
                obj = json.loads(path.read_text(encoding='utf-8'))
                payload = obj['payload']
            except (ValueError,KeyError):
                if skip_invalid:continue
                raise
            day = payload.get('market_date') or ((payload.get('research_state') or {}).get('features') or {}).get('decision_date')
            day = day or datetime.fromisoformat(obj['captured_at_utc'].replace('Z','+00:00')).astimezone(NY).date().isoformat()
            record = dict(stamp=stamp, day=day, header={k:v for k,v in obj.items() if k!='payload'})
            del obj, payload
        records[path.name] = record
        refs.append(Snapshot(path, record, shared))
    if records != previous:
        atomic_text(cache_path, json.dumps(records, separators=(',',':')))
    return sorted(refs, key=lambda x:x.get('captured_at_utc',''))


def fingerprint(refs, algorithm=None):
    value=[[(r.path.name,r.record['stamp'],r.get('sha256')) for r in refs],algorithm]
    return hashlib.sha256(json.dumps(value,separators=(',',':')).encode()).hexdigest()


def write_csv(path, rows, fields=None):
    rows = list(rows)
    fields = fields or list(dict.fromkeys(k for r in rows for k in r))
    path = Path(path)
    path.parent.mkdir(parents=True,exist_ok=True)
    fd, name = tempfile.mkstemp(dir=path.parent, prefix=path.name+'.', suffix='.tmp')
    try:
        with os.fdopen(fd,'w',newline='',encoding='utf-8') as f:
            writer=csv.DictWriter(f,fieldnames=fields)
            writer.writeheader();writer.writerows(rows)
        os.replace(name,path)
    finally:
        if os.path.exists(name):os.unlink(name)


def merge_csv(directory, output):
    paths=sorted(Path(directory).glob('????-??-??.csv'))
    fields=[]
    for path in paths:
        with path.open(newline='',encoding='utf-8') as f:
            for field in csv.DictReader(f).fieldnames or []:
                if field not in fields:fields.append(field)
    if not fields:return 0
    output=Path(output);output.parent.mkdir(parents=True,exist_ok=True)
    fd,name=tempfile.mkstemp(dir=output.parent,prefix=output.name+'.',suffix='.tmp')
    count=0
    try:
        with os.fdopen(fd,'w',newline='',encoding='utf-8') as f:
            writer=csv.DictWriter(f,fieldnames=fields);writer.writeheader()
            for path in paths:
                with path.open(newline='',encoding='utf-8') as source:
                    for row in csv.DictReader(source):writer.writerow(row);count+=1
        os.replace(name,output)
    finally:
        if os.path.exists(name):os.unlink(name)
    return count


def build_intraday_sessions(root, day=None):
    from .intraday_dataset_v2 import build_intraday_dataset_v2
    root=Path(root)
    refs=snapshot_refs(root/'data/raw/intraday','intraday_options_*.json')
    from . import intraday_dataset_v2
    algorithm=hashlib.sha256(Path(intraday_dataset_v2.__file__).read_bytes()).hexdigest()
    groups={}
    for ref in refs:groups.setdefault(ref.day,[]).append(ref)
    output=root/'data/processed/intraday/intraday_options_v2.csv'
    directory=output.parent/'sessions'
    manifest=directory/'manifest.json'
    try:known=json.loads(manifest.read_text())
    except (OSError,ValueError):known={}
    # Seed prepared closed sessions from the existing validated CSV.
    if output.exists() and not manifest.exists():
        seeded={}
        with output.open(newline='',encoding='utf-8') as f:
            reader=csv.DictReader(f);fields=reader.fieldnames
            for row in reader:seeded.setdefault(row['market_date'],[]).append(row)
        for date,rows in seeded.items():
            write_csv(directory/(date+'.csv'),rows,fields)
            if {r['source_file'] for r in rows}=={r.path.name for r in groups.get(date,[])}:
                known[date]=fingerprint(groups[date],algorithm)
        del seeded
    selected=[day] if day else sorted(groups)
    for date in selected:
        daily=groups.get(date,[])
        target=directory/(date+'.csv')
        digest=fingerprint(daily,algorithm)
        if daily and (known.get(date)!=digest or not target.exists()):
            count=build_intraday_dataset_v2(root/'data/raw/intraday',target,snapshot_files=[r.path for r in daily])
            known[date]=digest
            print('SESSION_BUILT',date,count,flush=True)
        elif daily:print('SESSION_CACHED',date,flush=True)
    atomic_text(manifest,json.dumps(known,sort_keys=True))
    return merge_csv(directory,output)
