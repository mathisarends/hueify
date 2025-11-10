def singleton(cls):
    original_new = cls.__new__
    instance = None

    def new_new(cls_inner, *args, **kwargs):
        nonlocal instance
        if instance is None:
            if original_new is object.__new__:
                instance = original_new(cls_inner)
            else:
                instance = original_new(cls_inner, *args, **kwargs)
        return instance

    cls.__new__ = staticmethod(new_new)
    return cls