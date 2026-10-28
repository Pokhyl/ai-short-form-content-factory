"""Require the relevant subject to be the visual focus, not incidental scenery."""
from factory_v3.gemini import obj, string, BOOL
POLICY = 'primary-subject-v1'
INSTRUCTION = (
    ' Independently assess subject_focus from the whole image before deciding acceptance. '
    'Name the dominant visual subject, then explain its direct relation to the requested topic. '
    'relevant_content_is_primary is true only when the topic, its documented physical part, '
    'or a relevant process stage is a primary recognizable subject of the composition. '
    'unrelated_subject_dominates is true when attention is instead on unrelated people, '
    'performances, vehicles, products or other objects, with the relevant detail merely '
    'incidental weather, background, lighting or scenery. Such images must be rejected. '
    'Do not infer topic relevance from a shared word or a caption alone. '
    'People are allowed when the requested topic concerns those people or their action; '
    'this is not a ban on any subject category. Scientific diagrams must likewise focus '
    'on the documented topic. Hidden mechanisms need not become visible, but their '
    'actual contextual subject must dominate the picture. '
)
def schema():
    return obj({'dominant_subject': string(), 'topic_connection': string(),
                'relevant_content_is_primary': BOOL, 'unrelated_subject_dominates': BOOL})

def accepted(focus):
    return (isinstance(focus,dict)
            and focus.get('relevant_content_is_primary') is True
            and focus.get('unrelated_subject_dominates') is False
            and all(isinstance(focus.get(k),str) and focus[k].strip()
                    for k in ('dominant_subject','topic_connection')))
