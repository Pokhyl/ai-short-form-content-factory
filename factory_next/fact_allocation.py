"""Allocate existing source facts without changing visual eligibility or coverage."""
from copy import deepcopy


def allocate_scene_facts(scenes):
    if not isinstance(scenes, list) or not 1 <= len(scenes) <= 8:
        raise ValueError("bounded source-bound scenes required")
    allowed = []
    for scene in scenes:
        facts = scene.get("evidence_ids")
        if (not isinstance(facts, list) or not facts or
                any(not isinstance(f, str) or not f for f in facts) or
                len(set(facts)) != len(facts)):
            raise ValueError("unique existing fact identities required")
        allowed.append(sorted(facts))
    # Maximum bipartite matching gives as many scenes as possible a distinct
    # fact. Augmentation prevents an early flexible scene stealing the sole
    # eligible fact of a later scene. All edges come from the reviewed plan.
    owner = {}
    def match(index, visited):
        for fact in allowed[index]:
            if fact in visited:
                continue
            visited.add(fact)
            if fact not in owner or match(owner[fact], visited):
                owner[fact] = index
                return True
        return False
    for index in reversed(range(len(scenes))):
        match(index, set())
    assigned = [[] for _ in scenes]
    for fact, index in sorted(owner.items()):
        assigned[index].append(fact)
    # Cover remaining facts exactly once. Keep their original eligibility.
    all_facts = sorted(set(f for facts in allowed for f in facts))
    for fact in all_facts:
        if fact not in owner:
            index = min((i for i, facts in enumerate(allowed) if fact in facts),
                        key=lambda i: (len(assigned[i]), i))
            assigned[index].append(fact)
    # More visual beats than facts can require a repeated claim. Preserve
    # every beat, choosing the least-repeated eligible fact deterministically.
    uses = {f: sum(f in group for group in assigned) for f in all_facts}
    for index, group in enumerate(assigned):
        if not group:
            fact = min(allowed[index], key=lambda f: (uses[f], f))
            group.append(fact)
            uses[fact] += 1
    return [{**deepcopy(scene), "evidence_ids": sorted(facts)}
            for scene, facts in zip(scenes, assigned)]
