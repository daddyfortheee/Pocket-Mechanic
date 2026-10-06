from app.project_planner import build_project_plan

def test_metadata_does_not_select_a_project():
    result=build_project_plan('Build a bookshelf',{'item':{'name':'Tile shower'},'media':[{'filename':'paint.jpg'}]})
    assert result['title']=='DIY project plan'

def test_tile_plan_does_not_invent_dimensions():
    result=build_project_plan('Install 6 by 24 ceramic tiles')
    assert result['title']=='Tile installation plan'
    assert '12x24' not in str(result)

def test_project_findings_can_select_relevant_plan():
    result=build_project_plan('Finish this room',{'findings':['Installing vinyl plank flooring']})
    assert result['title']=='Flooring installation plan'
