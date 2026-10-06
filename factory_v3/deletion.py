"""Physical per-request media removal with a durable no-reuse tombstone."""
import json
import os
import shutil
from pathlib import Path
from uuid import UUID

MEDIA_DIRECTORIES = ('catalog', 'voiceovers', 'alignments', 'visuals', 'renders')

def marker(root, request_id):
    root = Path(root).resolve()
    directory = root / 'deleted-requests'
    if directory.is_symlink():
        raise ValueError('deletion records escape media root')
    return directory / (str(UUID(str(request_id))) + '.json')

def ensure_visible(root, request_id):
    if marker(root, request_id).exists():
        raise KeyError('request deleted')

def deleted_ids(root):
    directory = marker(root, '00000000-0000-0000-0000-000000000000').parent
    result = []
    for path in directory.glob('*.json'):
        try: result.append(str(UUID(path.stem)))
        except ValueError: continue
    return result

def remove_media(root, request_id):
    root = Path(root).resolve()
    request_id = str(UUID(str(request_id)))
    receipt = marker(root, request_id)
    folders = []
    for category in MEDIA_DIRECTORIES:
        parent = root / category
        folder = parent / request_id
        if parent.is_symlink() or folder.is_symlink() or not folder.resolve().is_relative_to(root):
            raise ValueError('media removal escapes owned request directory')
        if folder.exists() and not folder.is_dir():
            raise ValueError('request media must be a directory')
        folders.append(folder)
    if receipt.exists() and json.loads(receipt.read_text())['state'] == 'deleted':
        return {'id':request_id, 'deleted':True}
    receipt.parent.mkdir(parents=True, exist_ok=True)
    record = {'id':request_id, 'state':'deleting'}
    def save():
        temp = receipt.with_suffix('.tmp')
        with temp.open('w') as stream:
            json.dump(record,stream);stream.flush();os.fsync(stream.fileno())
        temp.replace(receipt)
        descriptor=os.open(receipt.parent,os.O_RDONLY)
        try: os.fsync(descriptor)
        finally: os.close(descriptor)
    save()
    # Only directories owned by this exact UUID; shared provider caches and
    # other request media are not followed or removed.
    for folder in folders:
        if folder.exists(): shutil.rmtree(folder)
    if any(folder.exists() for folder in folders):
        raise OSError('request media removal incomplete')
    record['state']='deleted';save()
    return {'id':request_id, 'deleted':True}
