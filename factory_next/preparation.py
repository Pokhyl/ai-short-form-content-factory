"""Separate source, photo-corpus and narration stages for the replacement.

Provider transports, free-only accounting, source proofs and image inspection
remain shared infrastructure. Legacy paragraph repair and estimated visual-pool
selection are deliberately absent from this orchestration.
"""
from copy import deepcopy

from factory_v3.gemini import obj, array, string, validate_json
from factory_v3.grounding import validate_evidence, validate_script_review
from factory_v3.preparation import ResourceUnavailable
from material_first.engine import (validate_material, inspected_material, validate_story,
                                  MaterialResolutionUnavailable, probe_media)
from material_first.paragraphs import compact_materials, validate_native_surface, LANGUAGES
from material_first.photo_identity import pixels, same_photo
from material_first.presentation import TOPIC_POLICY, minimum_shots
from material_first.visuals import candidate_limit
from .duration import revision_word_target


class PreparationStages:
    def __init__(self, root, operations, authorize, *, probe=probe_media):
        self.root=root;self.operations=operations;self.authorize=authorize;self.probe=probe

    def research(self, context):
        self.authorize()
        request={**context['request'],'presentation_policy':TOPIC_POLICY,
                 'visual_validation_mode':'gemini'}
        brief=self.operations.research(deepcopy(request))
        facts=validate_evidence(brief['evidence'])
        required=brief['required_fact_ids']
        if not required or len(required)!=len(set(required)) or not set(required)<=facts.keys():
            raise ValueError('invalid required source coverage')
        # Queries are discovery hints. Photo suitability is decided from pixels.
        return {'request':{**request,'required_fact_ids':required},
                'evidence':brief['evidence'],'queries':brief['queries']}

    def materials(self, context):
        source=context['outputs']['research'];request=source['request'];evidence=source['evidence']
        facts=validate_evidence(evidence)
        candidates=self.operations.discover(deepcopy(request),deepcopy(source['queries']))
        if not isinstance(candidates,list) or len(candidates)>candidate_limit(request['seconds'],TOPIC_POLICY):
            raise ValueError('photo corpus exceeded bounded discovery budget')
        assets=[];photos=[];hashes=set();identities=set();fingerprints=[]
        for offset in range(0,len(candidates),4):
            batch=[]
            for candidate in candidates[offset:offset+4]:
                try:
                    asset=self.operations.download(deepcopy(candidate))
                    validate_material(self.root,asset,self.probe)
                except (ResourceUnavailable,MaterialResolutionUnavailable):
                    continue
                if asset.get('media_type')!='photo':continue
                if asset['id'] in identities or asset['sha256'] in hashes:continue
                fingerprint=asset.get('visual_fingerprint')
                if fingerprint is None:raise ValueError('photo identity fingerprint required')
                pixels(fingerprint)
                if fingerprint['source_sha256']!=asset['sha256']:
                    raise ValueError('photo fingerprint differs from source bytes')
                if any(same_photo(fingerprint,previous) for previous in fingerprints):continue
                identities.add(asset['id']);hashes.add(asset['sha256']);fingerprints.append(fingerprint)
                batch.append(asset)
            if not batch:continue
            receipts=self.operations.inspect_many(deepcopy(batch),deepcopy(evidence))
            if len(receipts)!=len(batch):raise ValueError('photo inspection omitted input')
            for asset,receipt in zip(batch,receipts):
                photo=inspected_material(asset,receipt,evidence,facts,'gemini')
                if photo is not None:assets.append(asset);photos.append(photo)
        if len(photos)<max(3,minimum_shots(request['seconds'],TOPIC_POLICY)):
            raise ValueError('insufficient distinct source-related photographs')
        return {'assets':assets,'photos':photos}

    def story(self, context):
        source=context['outputs']['research'];request=source['request'];evidence=source['evidence']
        photos=context['outputs']['materials']['photos']
        schema=obj({'beats':array(obj({'material_id':string(p['id'] for p in photos),
            'narration':{**string(),'maxLength':2400},
            'fact_ids':array(string(f['id'] for f in evidence['facts']),1,8)}),3,min(8,len(photos)))})
        seconds=request['seconds']
        instruction=(f"Write one coherent spoken explanation in native {LANGUAGES[request['language']]}. "
            f"Aim for {round(seconds*2.1)} words for {seconds} seconds of natural speech. "
            "Use only supplied source facts and photographed subjects. Cover every required_fact_id. "
            "Assign each paragraph a distinct supplied photo anchor related to its facts. "
            "Preserve mechanisms and meaning; do not claim the photograph literally shows an invisible process. "
            "Return natural narration directly; no word slots, scene durations or editing instructions.")
        draft,_=self.operations.gemini.generate('next-story',instruction,
            {**request,'evidence':evidence,'materials':compact_materials(photos)},schema)
        validate_json(draft,schema)
        scenes=validate_story(request,evidence,photos,draft)
        script=' '.join(s['narration'] for s in scenes)
        validate_native_surface(request['language'],script)
        review=self.operations.review_script({**request,'evidence':evidence,'materials':photos,
                                               'scenes':scenes,'script':script})
        validate_script_review(evidence,request['language'],script,scenes,review,topic=request['topic'])
        if review.get('native_language_quality') is not True:
            raise ValueError('independent native-language review failed')
        return {'scenes':scenes,'script':script,'review':review}

    def revise_story(self, context, measured_ms):
        """One source-grounded native rewrite after actually measuring TTS #1.

        One Gemini draft and one independent review, both inside the already
        claimed (never auto-replayed) voice stage. No invented photos/facts.
        """
        source=context['outputs']['research']
        request=source['request']
        evidence=source['evidence']
        photos=context['outputs']['materials']['photos']
        original=context['outputs']['story']
        count=len(original['scenes'])
        target=revision_word_target(original['script'],measured_ms,request['seconds'])
        schema=obj({'beats':array(obj({
            'material_id':string(p['id'] for p in photos),
            'narration':{**string(),'maxLength':2400},
            'fact_ids':array(string(f['id'] for f in evidence['facts']),1,8),
        }),count,count)})
        direction='expand' if measured_ms < request['seconds']*1000-1000 else 'shorten'
        instruction=(
            f"Rewrite the already reviewed narration as natural spoken "
            f"{LANGUAGES[request['language']]}. The first actual voice lasted "
            f"{measured_ms} ms; the requested video lasts {request['seconds']} seconds. "
            f"{direction.capitalize()} the speech while preserving all supplied "
            f"required facts, original claims, and reviewed photo grounding. "
            f"Aim for about {target} natural words (hint, NOT a word-slot contract). "
            "Use only provided evidence and real photographed subjects. Keep "
            "the original number of beats, each with a distinct photographed "
            "anchor and supported fact_ids. No narration of unseen mechanisms "
            "as if visibly photographed. Do not add unsourced facts, padding, "
            "repeated filler or an artificial ending. No timing or speed instructions. "
            "The next synthesized MP3 is independently measured and strictly "
            "rejected if it misses the target duration."
        )
        draft,_=self.operations.gemini.generate(
            'next-measured-duration-revision',instruction,
            {**request,'evidence':evidence,'materials':compact_materials(photos),
             'previous_reviewed_scenes':original['scenes'],
             'previous_reviewed_script':original['script'],
             'actual_voice_duration_ms':measured_ms},schema)
        validate_json(draft,schema)
        scenes=validate_story(request,evidence,photos,draft)
        script=' '.join(s['narration'] for s in scenes)
        validate_native_surface(request['language'],script)
        review=self.operations.review_script(
            {**request,'evidence':evidence,'materials':photos,
             'scenes':scenes,'script':script})
        validate_script_review(evidence,request['language'],script,scenes,
                               review,topic=request['topic'])
        if review.get('native_language_quality') is not True:
            raise ValueError('revised native-language review failed')
        return {'scenes':scenes,'script':script,'review':review}
