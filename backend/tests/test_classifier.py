def test_metadata_classifier_does_not_promote_uncalibrated_labels_to_strict_feed():
    from pulso.adapters.classifier import MetadataClassifier
    from pulso.config import Settings

    classifier = MetadataClassifier(Settings.testing())
    labels = classifier.classify(
        [{"id": "123", "description": "Uma receita simples", "hashtags": ["receita"]}], "Culinária"
    )
    assert labels[0]["video_id"] == "123"
    assert labels[0]["confidence"] < 0.8
    assert labels[0]["reviewed"] is False


def test_classifier_rejects_evidence_that_is_not_in_the_reference():
    import pytest

    from pulso.adapters.classifier import validate_classifications

    with pytest.raises(ValueError):
        validate_classifications(
            {
                "assignments": [
                    {
                        "video_id": "123",
                        "category": "Fitness",
                        "confidence": 0.99,
                        "evidence_excerpt": "invented statement",
                    }
                ]
            },
            [{"id": "123", "description": "Receita de pão", "hashtags": []}],
            False,
        )
