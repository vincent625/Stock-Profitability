import math

from keymetrics.scoring import earnings_quality_score, valuation_score, scenario_score, integrated_fundamental_score
from keymetrics.sentiment import raw_sentiment, adjusted_sentiment, centered_overlay, opportunity_score
from keymetrics.guidance import GuidanceObservation, banded_accuracy_score, observation_score


def test_earnings_quality_known_point():
    cfg={
        'weights':{'revenue_growth':.35,'operating_margin':.35,'fcf_margin':.30},
        'revenue_score':{'intercept':50,'slope':200,'min':0,'max':100},
        'operating_margin_score':{'intercept':30,'slope':200,'min':0,'max':100},
        'fcf_margin_score':{'intercept':30,'slope':233.3333333333,'min':0,'max':100},
        'min_components':2,
    }
    s=earnings_quality_score(.10,.20,.15,cfg)
    expected=.35*70 + .35*70 + .30*(30+.15*233.3333333333)
    assert abs(s-expected)<1e-9


def test_valuation_reweights_missing_pe():
    cfg={'weights':{'pe':.4,'p_fcf':.35,'p_s':.25},'anchors':{'pe':[10,50],'p_fcf':[10,60],'p_s':[1,12]},'pe_exclude_above':100}
    s=valuation_score(150,35,6.5,cfg)
    # Both remaining components are exactly 50, so reweighting must still equal 50.
    assert abs(s-50)<1e-9


def test_scenario_score_boundaries():
    cfg={'weights':{'bear':.35,'base':.40,'bull':.25},'bear_range':[-.6,.2],'base_range':[-.2,.5],'bull_range':[0,1]}
    assert scenario_score(-.6,-.2,0,cfg)==0
    assert scenario_score(.2,.5,1,cfg)==100


def test_missing_guidance_reweights():
    cfg={'weights':{'eq':.30,'valuation':.30,'guidance':.15,'scenario':.25},'reweight_missing':True}
    score=integrated_fundamental_score(80,60,None,40,cfg)
    assert abs(score-(.3*80+.3*60+.25*40)/.85)<1e-12


def test_centered_sentiment_neutral_has_zero_effect():
    cfg={'window_weights':{'d7':.2,'d30':.5,'d90':.3},'confidence_factors':{'High':1.0,'Medium':.85,'Low':.65},'materiality_factors':{'Major':1,'Moderate':.7,'Minor':.3},'overlay_coefficient':.05,'overlay_cap_points':2.5,'neutral_score':50,'quadrant':{'fundamental_high':55,'fundamental_low':45,'sentiment_high':55,'sentiment_low':45}}
    raw=raw_sentiment(50,50,50,cfg); adj=adjusted_sentiment(raw,'High',cfg)
    total,overlay=opportunity_score(80,adj,'Major',cfg)
    assert overlay==0
    assert total==80


def test_sentiment_overlay_cap():
    cfg={'materiality_factors':{'Major':1},'overlay_coefficient':.20,'overlay_cap_points':2.5,'neutral_score':50}
    assert centered_overlay(100,'Major',cfg)==2.5
    assert centered_overlay(0,'Major',cfg)==-2.5


def test_guidance_range_score():
    o=GuidanceObservation('X','FY','EPS','absolute',9.5,10.5,10,10.2)
    assert banded_accuracy_score(.02,'absolute')==90
    assert observation_score(o,'banded',.20)==92  # 80%*90 + 20%*100
