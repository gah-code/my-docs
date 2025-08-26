from notalink.settings import get_settings
def test_settings_dirs():
    s = get_settings()
    assert s.DATA_DIR and s.TRACES_DIR
