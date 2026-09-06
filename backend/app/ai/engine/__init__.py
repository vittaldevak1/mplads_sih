from .inference_pipeline import MPLADSForensicPredictor

_predictor = None

def get_predictor():
    global _predictor
    if _predictor is None:
        _predictor = MPLADSForensicPredictor()
    return _predictor

def get_predictor_with_stats(db_session):
    """Get predictor with constituency stats loaded for Q signal."""
    p = get_predictor()
    if not hasattr(p, 'constituency_stats') or not p.constituency_stats:
        p.load_constituency_stats(db_session)
    return p
