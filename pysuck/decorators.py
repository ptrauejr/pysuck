def synchronized(lock):
    def wrap(f):
        def call_func(*args, **kw):
            with lock:
                return f(*args, **kw)
        return call_func
    return wrap

