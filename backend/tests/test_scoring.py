from datetime import date, datetime, timedelta
from app.database import Base
from app.models import Meeting, Race, Runner, HorseHistory
from app.scoring import score_race


def h(runner_id, days, pos, dq=False, chrono=None):
    return HorseHistory(runner_id=runner_id,race_date=date.today()-timedelta(days=days),position=pos,disqualified=dq,chrono_km_seconds=chrono,discipline="Trot attelé",distance_m=2100,class_name="Course D")


def test_fault_penalizes_placed_more_than_performance():
    m=Meeting(id=1,race_date=date.today(),code="R1",track="Vincennes")
    race=Race(id=1,meeting=m,meeting_id=1,code="R1C1",name="x",scheduled_at=datetime.now(),discipline="Trot attelé",distance_m=2100,class_name="Course D",start_type="Autostart")
    a=Runner(id=1,race_id=1,number=1,horse_name="A",start_position=3,record_km_seconds=73.0)
    a.history=[h(1,10,None,True),h(1,30,2,False,73.2),h(1,50,1,False,73.4),h(1,70,3,False,73.6)]
    b=Runner(id=2,race_id=1,number=2,horse_name="B",start_position=4,record_km_seconds=74.0)
    b.history=[h(2,10,4,False,74.0),h(2,30,4,False,74.1),h(2,50,4,False,74.2),h(2,70,4,False,74.0)]
    cards=score_race(race,[a,b])
    assert cards[1].performance > cards[1].placed - 5  # value remains alive despite DQ
    assert cards[1].breakdown["dq_risk"] > cards[2].breakdown["dq_risk"]


def test_indirect_lines_never_dominate():
    m=Meeting(id=1,race_date=date.today(),code="R1",track="X")
    race=Race(id=1,meeting=m,meeting_id=1,code="R1C1",name="x",scheduled_at=datetime.now(),discipline="Plat",distance_m=2400,class_name="Handicap")
    a=Runner(id=1,race_id=1,number=1,horse_name="A",weight_kg=58,draw=3)
    a.history=[HorseHistory(runner_id=1,race_date=date.today()-timedelta(days=10),position=8,opponents=[{"later_wins":3,"later_places":3}])]
    b=Runner(id=2,race_id=1,number=2,horse_name="B",weight_kg=58,draw=4)
    b.history=[HorseHistory(runner_id=2,race_date=date.today()-timedelta(days=10),position=2,opponents=[])]
    cards=score_race(race,[a,b])
    assert cards[2].performance > cards[1].performance
