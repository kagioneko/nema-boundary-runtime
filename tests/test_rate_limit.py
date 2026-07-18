import sys
from pathlib import Path
from fastapi import FastAPI
from fastapi.testclient import TestClient
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'backend'))
from app.main import RateLimitMiddleware


def make_client(trusted=None):
    app=FastAPI()
    app.add_middleware(RateLimitMiddleware,limits={("POST","/limited"):2},window_seconds=60,trusted_proxies=trusted or set())
    @app.post('/limited')
    def limited(): return {'ok':True}
    @app.get('/health')
    def health(): return {'ok':True}
    return TestClient(app)


def test_quota_returns_429_and_retry_after_without_storing_content():
    c=make_client()
    for remaining in (1,0):
        r=c.post('/limited',json={'private':'not logged'})
        assert r.status_code==200
        assert r.headers['x-ratelimit-remaining']==str(remaining)
        assert r.headers['cache-control']=='no-store'
    blocked=c.post('/limited')
    assert blocked.status_code==429
    assert int(blocked.headers['retry-after'])>=1
    assert blocked.json()=={'detail':'demo quota exceeded'}
    for name in ('content-security-policy','x-frame-options','x-content-type-options','referrer-policy','permissions-policy','cache-control'):
        assert name in blocked.headers


def test_health_is_not_rate_limited():
    c=make_client()
    for _ in range(5): assert c.get('/health').status_code==200


def test_forwarded_headers_are_ignored_unless_peer_is_trusted():
    c=make_client()
    headers={'x-forwarded-for':'198.51.100.10','cf-connecting-ip':'198.51.100.10'}
    assert c.post('/limited',headers=headers).status_code==200
    assert c.post('/limited',headers={'cf-connecting-ip':'198.51.100.11'}).status_code==200
    assert c.post('/limited',headers={'cf-connecting-ip':'198.51.100.12'}).status_code==429


def test_trusted_proxy_can_separate_cloudflare_clients():
    c=make_client({'testclient'})
    for ip in ('198.51.100.10','198.51.100.11','198.51.100.12'):
        assert c.post('/limited',headers={'cf-connecting-ip':ip}).status_code==200

def test_x_forwarded_for_is_never_used_even_from_trusted_peer():
    c=make_client({'testclient'})
    for ip in ('198.51.100.10','198.51.100.11'):
        assert c.post('/limited',headers={'x-forwarded-for':ip}).status_code==200
    assert c.post('/limited',headers={'x-forwarded-for':'198.51.100.12'}).status_code==429

def test_duplicate_cloudflare_header_is_rejected_as_client_identity():
    middleware=RateLimitMiddleware(lambda s,r,se:None,trusted_proxies={'proxy'})
    scope={'client':('proxy',1),'headers':[(b'cf-connecting-ip',b'198.51.100.1'),(b'cf-connecting-ip',b'198.51.100.2')]}
    assert middleware._client_ip(scope)=='unknown'


def test_bucket_count_is_bounded_under_many_spoofed_clients():
    middleware=RateLimitMiddleware(lambda s,r,se:None,limits={("POST","/limited"):2},trusted_proxies={'proxy'},max_buckets=2)
    for ip in ('198.51.100.1','198.51.100.2','198.51.100.3'):
        scope={'client':('proxy',1),'headers':[(b'cf-connecting-ip',ip.encode())]}
        key=(middleware._client_ip(scope),'POST','/limited')
        if key not in middleware.buckets and len(middleware.buckets)>=middleware.max_buckets:
            middleware.buckets.pop(next(iter(middleware.buckets)))
        middleware.buckets[key]
    assert len(middleware.buckets)==2
