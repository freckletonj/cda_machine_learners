import aiohttp

_session = None


def get_session():
    global _session
    if _session is None:
        _session = aiohttp.ClientSession()
    return _session


def close_session():
    global _session
    if _session is not None:
        _session.close()
        _session = None
