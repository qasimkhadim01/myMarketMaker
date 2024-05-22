import time
import hashlib
import hmac

from connectivity.gateio import Api


def genSignRest(method, url, query_string=None, payload_string=None):
    t = time.time()
    m = hashlib.sha512()
    m.update((payload_string or "").encode('utf-8'))
    hashed_payload = m.hexdigest()
    s = '%s\n%s\n%s\n%s\n%s' % (method, url, query_string or "", hashed_payload, t)
    sign = hmac.new(Api.SECRET_KEY.encode('utf-8'), s.encode('utf-8'), hashlib.sha512).hexdigest()
    return {'KEY': Api.API_KEY, 'Timestamp': str(t), 'SIGN': sign}
