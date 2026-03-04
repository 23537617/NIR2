def metadata(*args, **kwargs):
    def wrapper(cls):
        return cls
    return wrapper
