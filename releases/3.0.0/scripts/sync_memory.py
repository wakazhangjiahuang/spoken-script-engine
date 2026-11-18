#!/usr/bin/env python3
"""Idempotent feedback queue and validated GitHub write plan; host connector performs writes."""
import argparse,json,hashlib,os,tempfile
from pathlib import Path
import fcntl

def enqueue(event,queue):
 for k in ['task_id','source_hash','result_version','brand_scope','feedback']:
  if not event.get(k):raise ValueError('missing '+k)
 if event.get('performance_status')=='observed' and not all(k in event.get('metrics',{}) for k in ['window','sample','denominator','baseline']):raise ValueError('observed metrics lack context')
 key=hashlib.sha256(json.dumps([event[k] for k in ['task_id','source_hash','result_version','brand_scope']],ensure_ascii=False).encode()).hexdigest();queue=Path(queue);queue.parent.mkdir(parents=True,exist_ok=True)
 with (queue.parent/(queue.name+'.lock')).open('a') as lock:
  fcntl.flock(lock,fcntl.LOCK_EX);rows=[json.loads(x) for x in queue.read_text().splitlines() if x] if queue.exists() else []
  if any(x['event_id']==key for x in rows):return {'event_id':key,'duplicate':True,'sync_status':next(x['sync_status'] for x in rows if x['event_id']==key)}
  row=dict(event,event_id=key,sync_status='pending_sync',promotion_status='candidate');rows.append(row)
  fd,tmp=tempfile.mkstemp(dir=queue.parent,prefix='feedback-')
  with os.fdopen(fd,'w') as f:f.write(''.join(json.dumps(x,ensure_ascii=False)+'\n' for x in rows))
  os.replace(tmp,queue);return {'event_id':key,'duplicate':False,'sync_status':'pending_sync'}
def acknowledge(queue,event_id,commit_sha,readback_verified):
 if not re_sha(commit_sha) or readback_verified is not True:raise ValueError('exact committed readback must be verified before sync acknowledgement')
 queue=Path(queue)
 with (queue.parent/(queue.name+'.lock')).open('a') as lock:
  fcntl.flock(lock,fcntl.LOCK_EX);rows=[json.loads(x) for x in queue.read_text().splitlines() if x];matched=False
  for row in rows:
   if row['event_id']==event_id:row['sync_status']='synced';row['commit_sha']=commit_sha;matched=True
  if not matched:raise ValueError('event not found')
  fd,tmp=tempfile.mkstemp(dir=queue.parent,prefix='feedback-')
  with os.fdopen(fd,'w') as f:f.write(''.join(json.dumps(x,ensure_ascii=False)+'\n' for x in rows))
  os.replace(tmp,queue)
 return {'event_id':event_id,'sync_status':'synced','commit_sha':commit_sha}
def write_plan(repo,branch,head,base_tree,files):
 if not re_sha(head) or not re_sha(base_tree):raise ValueError('actual head/base_tree SHA required')
 if not files:raise ValueError('empty write')
 for path,content in files.items():
  if Path(path).is_absolute() or '..' in Path(path).parts:raise ValueError('unsafe write path')
  if not isinstance(content,str):raise ValueError('UTF-8 text required')
 return {'repository_full_name':repo,'branch_name':branch,'expected_sha':head,'force':False,'base_tree_sha':base_tree,'parent_sha':head,'tree_elements':[{'path':p,'mode':'100644','type':'blob','content':c} for p,c in files.items()],'steps':['create_tree(base_tree)','create_commit(parent=head)','update_ref(expected=head,force=false)','fetch_file(exact new commit) and verify hashes'],'sync_status':'planned_not_written'}
def re_sha(x):return isinstance(x,str) and len(x)==40 and all(c in '0123456789abcdef' for c in x)
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--event',required=True);p.add_argument('--queue',required=True);a=p.parse_args()
 try:print(json.dumps(enqueue(json.loads(Path(a.event).read_text()),a.queue),ensure_ascii=False))
 except (ValueError,OSError) as e:p.exit(2,str(e)+'\n')
