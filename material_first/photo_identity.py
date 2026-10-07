"""Reject resized/re-encoded copies without changing a source photograph."""
import base64
import math
import subprocess


def fingerprint(path, sha256, width, height):
    raw=subprocess.check_output(['ffmpeg','-v','error','-i',str(path),'-vf',
        'scale=32:32:flags=area,format=rgb24','-frames:v','1','-threads','1','-f','rawvideo','-'],timeout=20)
    if len(raw)!=3072:raise ValueError('photo fingerprint decode incomplete')
    return {'algorithm':'rgb32-v1','source_sha256':sha256,'width':width,'height':height,
            'rgb':base64.b64encode(raw).decode()}


def pixels(receipt):
    if receipt.get('algorithm')!='rgb32-v1':raise ValueError('unknown photo fingerprint')
    raw=base64.b64decode(receipt['rgb'],validate=True)
    if len(raw)!=3072 or receipt['width']<=0 or receipt['height']<=0:
        raise ValueError('invalid photo fingerprint')
    return raw


def same_photo(left,right):
    a,b=pixels(left),pixels(right)
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
