"""Whole-photo presentation and exact, frame-counted delivery duration.

Narration and visual cuts are separate: a sentence may span several photos.
Original TTS speech keeps its natural speed; only a short silent tail is allowed.
This module does not certify source facts or unseen-photo relevance.
"""
import math
from pathlib import Path
import json
from .rendering import probe,sha,run

FPS=30
PHOTO_FILTER='scale=1080:1920:force_original_aspect_ratio=decrease:force_divisible_by=2,pad=1080:1920:(ow-iw)/2:(oh-ih)/2:color=0x101820,setsar=1,fps=30,format=yuv420p'

LEGACY_POLICY = 'whole-photo-exact-v1'
CALM_POLICY = 'whole-photo-exact-v2'
TOPIC_POLICY = 'whole-photo-topic-v3'
CALM_POLICIES = {CALM_POLICY, TOPIC_POLICY}
WHOLE_POLICIES = {LEGACY_POLICY, *CALM_POLICIES}

def preferred_shots(seconds, policy=LEGACY_POLICY):
    if type(seconds) is not int or seconds not in {15,30,45,60}: raise ValueError('unsupported duration')
    if policy not in WHOLE_POLICIES: raise ValueError('unsupported cadence policy')
    return math.ceil(seconds/(3.5 if policy in CALM_POLICIES else 2))

def minimum_shots(seconds, policy=LEGACY_POLICY):
    preferred_shots(seconds, policy)
    return math.ceil(seconds/(5 if policy in CALM_POLICIES else 2.5))

def phrase_frames(timings, source_duration_ms, seconds):
    if not math.isfinite(source_duration_ms) or source_duration_ms <= 0:
        raise ValueError('invalid source duration for phrase timing')
    result = set()
    for timing in timings:
        start, end = timing['start_ms'], timing['end_ms']
        if not all(math.isfinite(x) for x in (start, end)) or not 0 <= start < end <= source_duration_ms:
            raise ValueError('phrase timing outside source voice')
        result.update(round(x/source_duration_ms*seconds*FPS) for x in (start,end))
    return sorted(x for x in result if 0 < x < seconds*FPS)

def visual_timeline(seconds, count, policy=LEGACY_POLICY, boundaries=()):
    preferred_shots(seconds, policy)
    maximum = math.floor(seconds/2.5) if policy in CALM_POLICIES else 32
    if type(count) is not int or not minimum_shots(seconds, policy)<=count<=maximum:
        raise ValueError('not enough distinct photographs for requested cadence')
    frames=seconds*FPS
    if policy == LEGACY_POLICY:
        return [{'start_frame':frames*i//count,'end_frame':frames*(i+1)//count} for i in range(count)]
    if any(type(x) is not int or not 0 < x < frames for x in boundaries):
        raise ValueError('invalid phrase boundary frame')
    # Prefer nearby paragraph boundaries while retaining a moderate cadence.
    # Feasibility bounds prevent either a flash frame or a long final hold.
    edges=[0]
    for i in range(1,count):
        remaining=count-i
        low=max(edges[-1]+75, frames-remaining*150)
        high=min(edges[-1]+150, frames-remaining*75)
        target=max(low,min(high,round(frames*i/count)))
        nearby=[x for x in boundaries if low<=x<=high and abs(x-target)<=27]
        edges.append(min(nearby,key=lambda x:(abs(x-target),x)) if nearby else target)
    edges.append(frames)
    return [{'start_frame':a,'end_frame':b} for a,b in zip(edges,edges[1:])]

def validate_timeline(seconds, count, timeline, policy=LEGACY_POLICY):
    visual_timeline(seconds,count,policy)
    if not isinstance(timeline,list) or len(timeline)!=count: raise ValueError('visual timeline count differs')
    cursor=0
    for cut in timeline:
        if set(cut)!={'start_frame','end_frame'} or type(cut['start_frame']) is not int or type(cut['end_frame']) is not int:
            raise ValueError('invalid visual frame interval')
        if cut['start_frame']!=cursor or cut['end_frame']<=cursor: raise ValueError('visual frames not consecutive')
        if policy in CALM_POLICIES and not 75<=cut['end_frame']-cursor<=150:
            raise ValueError('visual hold outside moderate cadence')
        cursor=cut['end_frame']
    if cursor!=seconds*FPS: raise ValueError('visual frames do not cover requested duration')
    return timeline

def tempo_factor(source_seconds,target_seconds):
    preferred_shots(target_seconds)
    if not math.isfinite(source_seconds) or source_seconds <= 0:
        raise ValueError('invalid source audio duration')
    # A duration mismatch must never be concealed by changing speech speed.
    # At most one second of trailing silence preserves the requested frame count.
    if not 0 <= target_seconds - source_seconds <= 1:
        raise ValueError('natural narration must end within one second of requested time; changing speech speed is forbidden')
    return 1.0

def render_whole_photos(directory, audio_source, photos, seconds, *, policy=LEGACY_POLICY, timeline=None):
    """Exclusive new artifact; never overwrites source audio or photographs."""
    directory=Path(directory);audio_source=Path(audio_source);photos=[Path(x) for x in photos]
    timeline=validate_timeline(seconds,len(photos), timeline if timeline is not None else visual_timeline(seconds,len(photos),policy),policy);hashes=[sha(p) for p in photos]
    if len(set(hashes))!=len(hashes): raise ValueError('repeated photo bytes')
    original_ms=round(float(probe(audio_source)['format']['duration'])*1000)
    source_audio_hash=sha(audio_source)
    rate=tempo_factor(original_ms/1000,seconds)
    directory.mkdir(parents=True,exist_ok=False)
    # Use a lossless fitted track so the expected audio duration is exact.
    # Keep the encoded original immutable; no new TTS and no second synthesis.
    fitted=directory/'fitted.wav'
    run(['ffmpeg','-nostdin','-v','error','-n','-i',str(audio_source),'-vn',
         '-af',f'apad,atrim=duration={seconds}',
         '-ar','48000','-ac','1','-c:a','pcm_s16le',str(fitted)])
    if round(float(probe(fitted)['format']['duration'])*1000)!=seconds*1000:
        raise ValueError('fitted audio duration differs from requested time')
    segments=[]
    for i,(photo,cut) in enumerate(zip(photos,timeline)):
        segment=directory/f'segment-{i:02d}.mp4'
        run(['ffmpeg','-nostdin','-v','error','-n','-loop','1','-framerate',str(FPS),
             '-i',str(photo),'-vf',PHOTO_FILTER,'-an','-c:v','libx264','-threads','1',
             '-preset','ultrafast','-crf','21','-pix_fmt','yuv420p',
             '-frames:v',str(cut['end_frame']-cut['start_frame']),str(segment)])
        segments.append(segment)
    (directory/'concat.txt').write_text(''.join(f"file '{s}'\n" for s in segments))
    silent=directory/'silent.mp4'
    run(['ffmpeg','-nostdin','-v','error','-n','-f','concat','-safe','0','-i',str(directory/'concat.txt'),'-c','copy',str(silent)])
    final=directory/'final.mp4'
    run(['ffmpeg','-nostdin','-v','error','-n','-i',str(silent),'-i',str(fitted),
         '-map','0:v:0','-map','1:a:0','-c:v','copy','-c:a','aac','-b:a','192k',
         # Concat rounds segment container durations. Reset packet timestamps
         # from the frame index as well as counting frames (no B-frames).
         '-bsf:v',f'setts=pts=N/({FPS}*TB):dts=N/({FPS}*TB):duration=1/({FPS}*TB)',
         '-t',str(seconds),'-movflags','+faststart',str(final)])
    info=probe(final);v=[s for s in info['streams'] if s['codec_type']=='video'];a=[s for s in info['streams'] if s['codec_type']=='audio']
    if len(v)!=1 or len(a)!=1 or len(info['streams'])!=2:
        raise ValueError('unexpected output streams')
    if ((v[0]['width'],v[0]['height'],v[0]['pix_fmt'],v[0]['r_frame_rate'])
            !=(1080,1920,'yuv420p','30/1') or v[0]['codec_name']!='h264'
            or a[0]['codec_name']!='aac'):
        raise ValueError('unexpected encoded media format')
    if (int(v[0]['nb_frames'])!=seconds*FPS
            or round(float(info['format']['duration'])*1000)!=seconds*1000
            or round(float(v[0]['duration'])*1000)!=seconds*1000):
        raise ValueError('encoded duration differs from requested frames')
    run(['ffmpeg','-nostdin','-v','error','-xerror','-i',str(final),'-f','null','-'])
    if sha(audio_source)!=source_audio_hash or any(sha(p)!=h for p,h in zip(photos,hashes)):
        raise ValueError('source bytes changed during render')
    proof={'format':'1080x1920 H264 yuv420p 30fps AAC','requested_seconds':seconds,
           'actual_duration_ms':round(float(info['format']['duration'])*1000),
           'frame_count':int(v[0]['nb_frames']),'shot_count':len(photos),'unique_photo_count':len(set(hashes)),
           'framing':'whole photograph, aspect preserved, solid matte, no crop or blur',
           'source_audio_sha256':source_audio_hash,'source_audio_duration_ms':original_ms,
           'audio_tempo_factor':rate,'fitted_audio_sha256':sha(fitted),'audio_policy':'natural speed, at most one second trailing silence, original unchanged',
           'new_tts_calls':0,'full_decode_pass':True,'video_sha256':sha(final),
           'timeline':timeline,'photos':[{'path':str(p),'sha256':h} for p,h in zip(photos,hashes)]}
    (directory/'proof.json').write_text(json.dumps(proof,indent=2)+'\n')
    for segment in segments:segment.unlink()
    silent.unlink()
    return proof
