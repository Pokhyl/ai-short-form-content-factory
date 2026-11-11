from factory_next.preparation import _inspection_contract_batches


def test_inspection_batches_partition_different_visual_roles_and_preserve_order():
    assets = [
        {"id": "a", "visual_targets": [{"id": "machine"}]},
        {"id": "b", "visual_targets": [{"id": "paper"}]},
        {"id": "c", "visual_targets": [{"id": "machine"}]},
    ]

    groups = _inspection_contract_batches(assets)

    assert [[asset["id"] for asset in group] for group in groups] == [
        ["a", "c"],
        ["b"],
    ]


def test_inspection_batches_partition_qualification_contract_too():
    assets = [
        {"id": "a", "visual_targets": [], "visual_qualification_protocol": "qualified-target-v1"},
        {"id": "b", "visual_targets": []},
    ]

    groups = _inspection_contract_batches(assets)

    assert [[asset["id"] for asset in group] for group in groups] == [["a"], ["b"]]
