from app.main import RuleBasedNarrative

FLAT_TIME_DNA = {"morning": 10, "lunch": 10, "evening": 10, "night": 10}


def test_academic_takes_priority_over_everything_else():
    result = RuleBasedNarrative.generate(
        "Manhattan", vitality=90, office=90, uni=3, time_dna={**FLAT_TIME_DNA, "night": 90}
    )
    assert result["persona"] == "Manhattan Student Hub"
    assert "student foot traffic" in result["description"]


def test_nightlife_needs_both_high_vitality_and_high_night_traffic():
    result = RuleBasedNarrative.generate(
        "Brooklyn", vitality=80, office=0, uni=0, time_dna={**FLAT_TIME_DNA, "night": 50}
    )
    assert result["persona"] == "Brooklyn Nightlife District"
    assert "Vitality: 80%" in result["description"]


def test_high_vitality_alone_falls_through_to_a_lower_priority_archetype():
    # Same vitality as the nightlife case, but night traffic stays low, so
    # this must NOT match Nightlife.
    result = RuleBasedNarrative.generate(
        "Brooklyn", vitality=80, office=0, uni=0, time_dna=FLAT_TIME_DNA
    )
    assert result["persona"] != "Brooklyn Nightlife District"


def test_corporate_high_office_alone():
    result = RuleBasedNarrative.generate(
        "Manhattan", vitality=10, office=75, uni=0, time_dna=FLAT_TIME_DNA
    )
    assert result["persona"] == "Manhattan Business Center"
    assert "office buildings" in result["description"]


def test_mixed_use_moderate_office_and_vitality():
    result = RuleBasedNarrative.generate(
        "Queens", vitality=55, office=55, uni=0, time_dna=FLAT_TIME_DNA
    )
    assert result["persona"] == "Dynamic Queens Hub"
    assert "Live-Work-Play" in result["description"]


def test_commuter_morning_peak():
    result = RuleBasedNarrative.generate(
        "Bronx", vitality=10, office=10, uni=0, time_dna={**FLAT_TIME_DNA, "morning": 65}
    )
    assert result["persona"] == "Major Transit Anchor"
    assert "outbound commuter flow" in result["description"]


def test_residential_low_vitality_and_office():
    result = RuleBasedNarrative.generate(
        "Staten Island", vitality=5, office=5, uni=0, time_dna=FLAT_TIME_DNA
    )
    assert result["persona"] == "Local Neighborhood Stop"
    assert "community-focused" in result["description"]


def test_standard_fallback_when_no_archetype_thresholds_are_met():
    result = RuleBasedNarrative.generate(
        "Brooklyn", vitality=40, office=40, uni=0, time_dna=FLAT_TIME_DNA
    )
    assert result["persona"] == "Brooklyn Local Stop"


def test_time_desc_reflects_the_actual_peak_bucket_not_just_the_archetype():
    # Standard archetype, but peak bucket is "night" — the time sentence
    # should describe late-night ridership even though the persona doesn't.
    result = RuleBasedNarrative.generate(
        "Brooklyn", vitality=40, office=40, uni=0, time_dna={**FLAT_TIME_DNA, "night": 90}
    )
    assert "Late Night" in result["description"]
