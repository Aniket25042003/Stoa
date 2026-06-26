from stoa_core.enrichment.pipeline import parse_competitor_names


def test_parse_competitor_names():
    names = parse_competitor_names("Acme, Beta Inc\nGamma")
    assert names == ["Acme", "Beta Inc", "Gamma"]


def test_parse_competitor_names_max():
    notes = ", ".join(f"Comp{i}" for i in range(10))
    assert len(parse_competitor_names(notes, max_names=5)) == 5
