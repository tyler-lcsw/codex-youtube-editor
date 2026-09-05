import pytest

def test_tracker_dry_run_duplicate_and_resync(tmp_path):
    from tools.tracker import upsert_project,list_projects
    index=tmp_path/'tracker.sqlite'
    upsert_project(index,'p1',{'title':'Draft','stage':'idea'},'First',apply=False)
    assert not index.exists()
    upsert_project(index,'p1',{'title':'Draft','stage':'idea'},'First',apply=True)
    upsert_project(index,'p1',{'title':'Revised','stage':'script'},'Second',apply=True)
    rows=list_projects(index,stage='script')
    assert len(rows)==1 and rows[0]['script']=='Second' and rows[0]['properties']['title']=='Revised'
    assert list_projects(index,stage='idea')==[]

def test_distinct_ids_with_same_title_are_not_overwritten(tmp_path):
    from tools.tracker import upsert_project,list_projects
    for pid in ['one','two']:upsert_project(tmp_path/'db',pid,{'title':'Same'},pid,apply=True)
    assert len(list_projects(tmp_path/'db'))==2
