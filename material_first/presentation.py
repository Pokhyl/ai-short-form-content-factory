"""Whole-photo presentation and exact, frame-counted delivery duration.

Narration and visual cuts are separate: a sentence may span several photos.
Original TTS bytes are retained; tempo fitting changes speed but not pitch.
This module does not certify source facts or unseen-photo relevance.
"""
import math
from pathlib import Path
import json
from .rendering import probe,sha,run

FPS=30
PHOTO_FILTER='scale=1080:1920:force_original_aspect_ratio=decrease:force_divisible_by=2,pad=1080:1920:(ow-iw)/2:(oh-ih)/2:color=0x101820,setsar=1,fps=30,format=yuv420p'

def preferred_shots(seconds):
    if type(seconds) is not int or seconds not in {15,30,45,60}: raise ValueError('unsupported duration')
    return math.ceil(seconds/2)

def visual_timeline(seconds, count):
    preferred_shots(seconds)
    if type(count) is not int or not math.ceil(seconds/2.5)<=count<=32:
        raise ValueError('not enough distinct photographs for requested cadence')
    frames=seconds*FPS
    return [{'start_frame':frames*i//count,'end_frame':frames*(i+1)//count}
            for i in range(count)]

def tempo_factor(source_seconds,target_seconds):
    preferred_shots(target_seconds)
    if not math.isfinite(source_seconds) or source_seconds <= 0:
        raise ValueError('invalid source audio duration')
    factor=source_seconds/target_seconds
    if not .65<=factor<=1.5: raise ValueError('narration too far from requested time')
    return factor

def render_whole_photos(directory, audio_source, photos, seconds):
    """Exclusive new artifact; never overwrites source audio or photographs."""
    directory=Path(directory);audio_source=Path(audio_source);photos=[Path(x) for x in photos]
    timeline=visual_timeline(seconds,len(photos));hashes=[sha(p) for p in photos]
    if len(set(hashes))!=len(hashes): raise ValueError('repeated photo bytes')
    original_ms=round(float(probe(audio_source)['format']['duration'])*1000)
    source_audio_hash=sha(audio_source)
    rate=tempo_factor(original_ms/1000,seconds)
    directory.mkdir(parents=True,exist_ok=False)
    # Use a lossless fitted track so the expected audio duration is exact.
    # Keep the encoded original immutable; no new TTS and no second synthesis.
    fitted=directory/'fitted.wav'
    run(['ffmpeg','-nostdin','-v','error','-n','-i',str(audio_source),'-vn',
         '-af',f'atempo={rate:.10f},apad,atrim=duration={seconds}',
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
           'audio_tempo_factor':rate,'fitted_audio_sha256':sha(fitted),'audio_policy':'pitch-preserving tempo fit, original unchanged',
           'new_tts_calls':0,'full_decode_pass':True,'video_sha256':sha(final),
           'timeline':timeline,'photos':[{'path':str(p),'sha256':h} for p,h in zip(photos,hashes)]}
    (directory/'proof.json').write_text(json.dumps(proof,indent=2)+'\n')
    for segment in segments:segment.unlink()
    silent.unlink()
    return proof
