"""Fit a tiny MP3 overrun by removing verified terminal silence only."""
import array
import hashlib
import json
import subprocess
import sys


def _run(args):
    return subprocess.check_output(args,stderr=subprocess.PIPE,timeout=20)


def trim_terminal_silence(source, destination, measured_ms, seconds):
    target=seconds*1000
    if not 0<measured_ms-target<=750:
        return None
    probe=json.loads(_run(['ffprobe','-v','error','-show_streams','-of','json',str(source)]))
    streams=probe['streams']
    if len(streams)!=1 or streams[0].get('codec_name')!='mp3':return None
    rate=int(streams[0]['sample_rate']);channels=int(streams[0]['channels'])
    if rate not in (22050,24000,44100,48000) or channels not in (1,2):return None
    # Preserve compressed frames. A new Xing header changes decoder delay,
    # so explicitly omit it and verify the actual decoded prefix below.
    _run(['ffmpeg','-v','error','-n','-i',str(source),'-t',f'{(target-48)/1000:.3f}',
          '-c:a','copy','-write_xing','0','-id3v2_version','0',str(destination)])
    def pcm(path):
        return _run(['ffmpeg','-v','error','-i',str(path),'-f','s16le','-acodec','pcm_s16le','-'])
    original=pcm(source);retained=pcm(destination)
    if not retained or len(retained)>=len(original) or original[:len(retained)]!=retained:
        return None
    samples=array.array('h');samples.frombytes(original)
    if sys.byteorder!='little':samples.byteswap()
    guard=round(rate*channels*.1)
    boundary=len(retained)//2
    # -60dBFS peak ceiling across BOTH the retained 100ms guard and removed
    # suffix. Never shorten spoken content, pauses within speech, or tempo.
    peak=max(abs(v) for v in samples[max(0,boundary-guard):])
    if peak>32:return None
    measured=json.loads(_run(['ffprobe','-v','error','-show_format','-of','json',str(destination)]))
    duration=round(float(measured['format']['duration'])*1000)
    if not target-2100<=duration<=target:return None
    return {'policy':'verified-terminal-silence-v1','original_duration_ms':measured_ms,
            'duration_ms':duration,'removed_ms':measured_ms-duration,
            'guard_ms':100,'guard_and_removed_peak_s16':peak,'exact_pcm_prefix':True,
            'original_sha256':hashlib.sha256(source.read_bytes()).hexdigest(),
            'sha256':hashlib.sha256(destination.read_bytes()).hexdigest()}
