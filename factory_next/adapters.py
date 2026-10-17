"""Bind the existing reviewed source, voice and media components to Pipeline.

This is not a production route. The optional gate must do no provider dispatch,
write or quota reservation. All stages themselves may have external side effects
and must never be automatically retried after ambiguous execution.
"""
from copy import deepcopy


class FactoryNextAdapters:
    def __init__(self, preparation, voice, media, *, preflight_gate=None):
        self.preparation=preparation
        self.voice_stages=voice
        self.media=media
        self.preflight_gate=preflight_gate

    def preflight(self, stage, context):
        if self.preflight_gate is not None:
            self.preflight_gate(stage,deepcopy(context))

    def research(self, context):
        return self.preparation.research(context)

    def materials(self, context):
        return self.preparation.materials(context)

    def story(self, context):
        return self.preparation.story(context)

    def voice(self, context):
        return self.voice_stages.voice(context)

    def alignment(self, context):
        return self.voice_stages.alignment(context)

    def render(self, context):
        return self.media.render(context)

    def audit(self, context):
        return self.media.audit(context)
