from __future__ import annotations
from types import SimpleNamespace
from urllib.parse import parse_qs, urlsplit
import unittest
from adapter import Adapter

class EasyOnboardingTests(unittest.TestCase):
    def test_creates_managed_service_with_provider_requestid(self):
        calls=[]
        def request(**kw):
            calls.append(kw)
            url=kw['url']
            if url.endswith('/oauth2/v1/tokens/bearer'):
                return {'access_token':'ACCESS','refresh_token':'REFRESH-2'}
            if '/companyinfo/123' in url:
                return {'CompanyInfo':{'Id':'123','CompanyName':'Vib Tools QBO'}}
            if '/query?' in url:
                q=parse_qs(urlsplit(url).query).get('query',[''])[0]
                if 'FROM Item' in q:
                    return {'QueryResponse':{}}
                if 'FROM Account' in q:
                    return {'QueryResponse':{'Account':{'Id':'42','Name':'Sales of Product Income','AccountType':'Income','AccountSubType':'SalesOfProductIncome','Active':True}}}
            if '/item?' in url and kw['method']=='POST':
                return {'Item':{'Id':'77','Name':'Invio Service','Active':True}}
            raise AssertionError((kw['method'],url))
        context=SimpleNamespace(credentials={'client_id':'cid','client_secret':'sec','refresh_token':'REFRESH-1','realm_id':'123','default_item_id':'','redirect_uri':'http://localhost:8768/callback'},mode='Sandbox',request=request)
        result=Adapter().prepare_account(context)
        self.assertEqual(result.credential_updates,{'refresh_token':'REFRESH-2','default_item_id':'77'})
        create=next(c for c in calls if c['method']=='POST' and '/item?' in c['url'])
        self.assertTrue(create['idempotency_key'].startswith('invio-onboarding-'))
        self.assertIn('requestid=',create['url'])

if __name__=='__main__': unittest.main()
