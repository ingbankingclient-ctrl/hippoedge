from app.utils import sanitize_objective_payload


def test_market_and_prediction_fields_are_removed_recursively():
    raw={"cheval":"A","cote":3.2,"Note_IA":95,"nested":{"popularite":99,"record":"1'13\"2"},"pronostics":[1,2,3]}
    out=sanitize_objective_payload(raw)
    assert out["cheval"]=="A"
    assert "cote" not in out
    assert "Note_IA" not in out
    assert "popularite" not in out["nested"]
    assert out["nested"]["record"]=="1'13\"2"
    assert "pronostics" not in out
