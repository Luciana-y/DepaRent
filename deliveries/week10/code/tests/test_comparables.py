import numpy as np
import pytest

import src.comparables as comparables
from conftest import row_to_property
from src.clustering import FEATURES, PRICE_COLUMNS, load_training_frame
from src.comparables import STRATEGY_DISTRICT, STRATEGY_EXPANDED, ComparablesIndex, get_comparables, get_index


def _cluster_of(ids):
    idx = get_index()
    lookup = dict(zip(idx.ids, idx.labels))
    return {lookup[i] for i in ids}


def test_five_results_same_cluster_and_self_excluded(representative_rows):
    for row in representative_rows:
        out = get_comparables(row_to_property(row, with_location=False), n=5, exclude_ids=[row["id_anuncio"]])
        ids = [c["id_anuncio"] for c in out["comparables"]]
        assert len(ids) == 5 and len(set(ids)) == 5
        assert row["id_anuncio"] not in ids
        assert _cluster_of(ids) == {out["cluster_id"]}


def test_district_priority_when_enough_candidates(representative_rows):
    for row in representative_rows:
        out = get_comparables(row_to_property(row, with_location=False), n=5, exclude_ids=[row["id_anuncio"]])
        if out["candidatos_mismo_distrito"] >= 5:
            assert out["strategy"] == STRATEGY_DISTRICT
            assert all(c["mismo_distrito"] and c["distrito"] == row["distrito"] for c in out["comparables"])


def test_expanded_fallback_keeps_same_district_first(training_frame):
    idx = get_index()
    # Distrito real con menos de 5 anuncios en total: obliga al fallback.
    counts = training_frame["distrito"].value_counts()
    sparse = counts[counts < 5].index[0]
    row = training_frame[(training_frame["distrito"] == sparse) & training_frame["banos"].notna()].iloc[0]
    out = get_comparables(row_to_property(row, with_location=False), n=5, exclude_ids=[row["id_anuncio"]])
    assert out["strategy"] == STRATEGY_EXPANDED
    assert len(out["comparables"]) == 5
    flags = [c["mismo_distrito"] for c in out["comparables"]]
    assert flags == sorted(flags, reverse=True)  # primero los del mismo distrito
    assert sum(flags) == out["candidatos_mismo_distrito"]
    assert _cluster_of([c["id_anuncio"] for c in out["comparables"]]) == {out["cluster_id"]}
    assert idx is get_index()


def test_distances_finite_and_sorted_within_groups(representative_rows):
    for row in representative_rows:
        comps = get_comparables(row_to_property(row, with_location=False), n=5)["comparables"]
        for flag in (True, False):
            d = [c["distancia_similitud"] for c in comps if c["mismo_distrito"] is flag]
            assert all(np.isfinite(x) and x >= 0 for x in d)
            assert d == sorted(d)


def test_similarity_space_has_no_price(model):
    idx = get_index()
    assert idx.X.shape[1] == len(FEATURES)
    assert not set(FEATURES) & set(PRICE_COLUMNS)
    assert get_comparables({"distrito": "Lince", "area_total": 70, "dormitorios": 2, "banos": 2,
                            "amenidades": []})["similarity_features"] == FEATURES


def test_changing_prices_does_not_change_comparables(model, monkeypatch, representative_rows):
    rng = np.random.default_rng(0)

    def shuffled_prices(path=None):
        df = load_training_frame(path)
        for col in PRICE_COLUMNS:
            if col in df:
                df[col] = rng.permutation(df[col].to_numpy())
        return df

    monkeypatch.setattr(comparables, "load_training_frame", shuffled_prices)
    perturbed = ComparablesIndex(model)
    original = get_index()
    for row in representative_rows:
        prop = row_to_property(row, with_location=False)
        a = [c["id_anuncio"] for c in original.get_comparables(prop)["comparables"]]
        b = [c["id_anuncio"] for c in perturbed.get_comparables(prop)["comparables"]]
        assert a == b


@pytest.mark.parametrize("n", [0, -1, 2.5, True])
def test_invalid_n(n):
    with pytest.raises(ValueError):
        get_comparables({"distrito": "Lince", "area_total": 70, "dormitorios": 2, "banos": 2, "amenidades": []}, n=n)
