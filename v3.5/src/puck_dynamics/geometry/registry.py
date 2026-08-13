_FEATURE_REGISTRY = {}


def register_feature(name: str, cls: type):
    _FEATURE_REGISTRY[name] = cls
    return cls


def get_registered_features():
    return dict(_FEATURE_REGISTRY)
