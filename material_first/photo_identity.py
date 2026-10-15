"""Reject resized/re-encoded copies without changing a source photograph."""
import base64
import math
import subprocess


def fingerprint(path, sha256, width, height, *, algorithm='rgb32-sift-v2'):
    if algorithm not in {'rgb32-v1', 'rgb32-sift-v2'}:
        raise ValueError('unknown photo fingerprint')
    raw=subprocess.check_output(['ffmpeg','-v','error','-i',str(path),'-vf',
        'scale=32:32:flags=area,format=rgb24','-frames:v','1','-threads','1','-f','rawvideo','-'],timeout=20)
    if len(raw)!=3072:raise ValueError('photo fingerprint decode incomplete')
    result = {'algorithm':algorithm,'source_sha256':sha256,'width':width,'height':height,
              'rgb':base64.b64encode(raw).decode()}
    if algorithm == 'rgb32-sift-v2':
        from .photo_geometry import describe
        result['geometry'] = describe(path)
    return result


def pixels(receipt):
    if receipt.get('algorithm') not in {'rgb32-v1','rgb32-sift-v2'}:raise ValueError('unknown photo fingerprint')
    raw=base64.b64decode(receipt['rgb'],validate=True)
    if len(raw)!=3072 or receipt['width']<=0 or receipt['height']<=0:
        raise ValueError('invalid photo fingerprint')
    return raw


def same_photo(left,right):
    a,b=pixels(left),pixels(right)
    if left.get('algorithm') == right.get('algorithm') == 'rgb32-sift-v2':
        from .photo_geometry import same_view
        if same_view(left['geometry'], right['geometry']) or same_view(right['geometry'], left['geometry']):
            return True
    if abs(left['width']/left['height']-right['width']/right['height'])>0.005:
        return False
    if a==b:return True
    ma,mb=sum(a)/len(a),sum(b)/len(b)
    aa=sum((x-ma)**2 for x in a);bb=sum((x-mb)**2 for x in b)
    # Almost blank sky/flat backgrounds are ambiguous. Do not reject a
    # different object because both occupy very few pixels.
    if min(aa,bb)/len(a)<64:return False
    correlation=sum((x-ma)*(y-mb) for x,y in zip(a,b))/math.sqrt(aa*bb)
    return correlation>=0.995
