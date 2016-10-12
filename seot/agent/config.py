import kaptan


CONFIG_FILE_PATH = "conf/config.yml"


_kaptan_config = None


def get(key=None):
    return _kaptan_config.get(key)


def init():
    global _kaptan_config
    try:
        _kaptan_config = kaptan.Kaptan(handler="yaml")
        _kaptan_config.import_config(CONFIG_FILE_PATH)
    except:
        pass
