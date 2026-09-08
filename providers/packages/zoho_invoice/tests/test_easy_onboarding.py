from __future__ import annotations

from types import SimpleNamespace
import unittest

from adapter import Adapter


class EasyOnboardingTests(unittest.TestCase):
    def _context(self, *, existing=False):
        calls=[]
        def request(**kw):
            calls.append(kw)
            url=kw['url']
            if '/organizations/123' in url:
                return {'code':0,'organization':{'organization_id':'123','name':'Vib Tools'}}
            if '/items' in url and kw['method']=='GET':
                return {'code':0,'items':([{'item_id':'9001','name':'Invio Service','status':'active'}] if existing else [])}
            if '/items' in url and kw['method']=='POST':
                return {'code':0,'item':{'item_id':'9001','name':'Invio Service','status':'active'}}
            raise AssertionError((kw['method'],url))
        return SimpleNamespace(credentials={
            'accounts_server_url':'https://accounts.zoho.com','client_id':'cid','client_secret':'sec',
            'refresh_token':'refresh','organization_id':'123','default_item_id':''
        }, mode='Default', request=request), calls

    def test_creates_once_then_reuses_managed_invio_service(self):
        adapter=Adapter()
        adapter._access_token=lambda context, account: ('ACCESS','https://www.zohoapis.com')
        context,calls=self._context(existing=False)
        result=adapter.prepare_account(context)
        self.assertEqual(result.credential_updates['default_item_id'],'9001')
        self.assertEqual(result.account_label,'Vib Tools')
        self.assertEqual(sum(1 for c in calls if c['method']=='POST' and '/items' in c['url']),1)
        context2,calls2=self._context(existing=True)
        result2=adapter.prepare_account(context2)
        self.assertEqual(result2.credential_updates['default_item_id'],'9001')
        self.assertFalse(any(c['method']=='POST' and '/items' in c['url'] for c in calls2))

if __name__=='__main__': unittest.main()
