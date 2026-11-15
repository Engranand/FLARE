import { afterEach, describe, expect, it, vi } from 'vitest';
import { request, payload, queryScience } from './workstation';
afterEach(()=>vi.unstubAllGlobals());
describe('workstation API contracts',()=>{
 it('requests bounded observation pages without changing raw filters',async()=>{const fetcher=vi.fn().mockResolvedValue(new Response(JSON.stringify({items:[],total:0,page:2,page_size:25})));vi.stubGlobal('fetch',fetcher);await request('/workstation/observations?page=2&page_size=25');expect(fetcher.mock.calls[0][0]).toContain('page=2&page_size=25');});
 it('requests synthesis through existing intelligence API',async()=>{const fetcher=vi.fn().mockResolvedValue(new Response('{}'));vi.stubGlobal('fetch',fetcher);await queryScience('What is initial oxygen?');const body=JSON.parse(fetcher.mock.calls[0][1].body);expect(body).toEqual({question:'What is initial oxygen?',investigation:'PSI-25',synthesize:true});});
 it('propagates abort signals',async()=>{const fetcher=vi.fn().mockResolvedValue(new Response('{"data":{"counts":{}}}'));vi.stubGlobal('fetch',fetcher);const c=new AbortController();await payload('/summary',c.signal);expect(fetcher.mock.calls[0][1].signal).toBe(c.signal);});
 it('preserves an unavailable metric instead of replacing it with zero',async()=>{vi.stubGlobal('fetch',vi.fn().mockResolvedValue(new Response('{"data":{"counts":{"validated_results":null}}}')));expect(await payload('/summary')).toEqual({counts:{validated_results:null}});});
 it('surfaces sanitized backend failures',async()=>{vi.stubGlobal('fetch',vi.fn().mockResolvedValue(new Response('{"detail":"Scientific database is not configured."}',{status:503})));await expect(payload('/summary')).rejects.toThrow('not configured');});
});
