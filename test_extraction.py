from services.information_extractor import InformationExtractor

test_text = """
John Smith is the CEO of TechCorp Inc.
He works closely with Jane Doe, who serves as CTO.
TechCorp is headquartered in New York and has a development office in San Francisco.
The company specializes in AI software and machine learning solutions.
Sarah Johnson works as a senior developer at the San Francisco office.
"""

result = InformationExtractor.process_text(test_text)
print("=== Extraction Results ===")
print(f"Entity count: {result['entity_count']}")
print(f"Relationship count: {result['relationship_count']}")
print("\n=== Entity List ===")
for entity in result["entities"]:
    print(f" - {entity['name']} ({entity['type']})")
print("\n=== Relationship List ===")
for rel in result["relationships"]:
    print(f" - {rel['from']} --[{rel['type']}]--> {rel['to']}")
