from services.information_extractor import InformationExtractor

SAMPLE_TEXT = """
John Smith is the CEO of TechCorp Inc.
He works closely with Jane Doe, who serves as CTO.
TechCorp is headquartered in New York and has a development office in San Francisco.
The company specializes in AI software and machine learning solutions.
Sarah Johnson works as a senior developer at the San Francisco office.
"""


def test_extract_entities_finds_expected_types():
    entities = InformationExtractor.extract_entities(SAMPLE_TEXT)
    types_by_name = {e["name"]: e["type"] for e in entities}

    assert types_by_name["John Smith"] == "Person"
    assert types_by_name["New York"] == "Location"
    assert types_by_name["San Francisco"] == "Location"
    assert "TechCorp Inc" in types_by_name
    assert types_by_name["TechCorp Inc"] == "Organization"


def test_extract_entities_deduplicates_by_name():
    entities = InformationExtractor.extract_entities(SAMPLE_TEXT)
    names = [e["name"] for e in entities]
    assert len(names) == len(set(names))


def test_ceo_of_relationship_is_extracted():
    entities = InformationExtractor.extract_entities(SAMPLE_TEXT)
    relationships = InformationExtractor.extract_relationships(SAMPLE_TEXT, entities)

    ceo_rels = [r for r in relationships if r["type"] == "CEO_OF"]
    assert len(ceo_rels) == 1
    assert ceo_rels[0]["from"] == "John Smith"
    assert ceo_rels[0]["to"] == "TechCorp Inc"


def test_relationship_types_have_no_stray_whitespace():
    entities = InformationExtractor.extract_entities(SAMPLE_TEXT)
    relationships = InformationExtractor.extract_relationships(SAMPLE_TEXT, entities)

    for rel in relationships:
        assert rel["type"] == rel["type"].strip()


def test_has_position_relationship_is_extracted():
    text = "Jane Doe serves as CTO."
    entities = InformationExtractor.extract_entities(text)
    relationships = InformationExtractor.extract_relationships(text, entities)

    assert relationships == [
        {
            "from": "Jane Doe",
            "to": "CTO",
            "type": "HAS_POSITION",
            "properties": {
                "source": "pattern_match",
                "confidence": 0.7,
                "context": "Jane Doe serves as CTO",
            },
        }
    ]


def test_process_text_counts_are_consistent():
    result = InformationExtractor.process_text(SAMPLE_TEXT)

    assert result["entity_count"] == len(result["entities"])
    assert result["relationship_count"] == len(result["relationships"])
    assert result["extraction_summary"]["person_count"] == len(
        [e for e in result["entities"] if e["type"] == "Person"]
    )
