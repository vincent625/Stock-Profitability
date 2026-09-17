from __future__ import annotations

from collections import Counter
from datetime import datetime, timezone
from statistics import mean
from typing import Any
from urllib.parse import urlparse

MAJOR_TERMS = (
    'fda approv','fda reject','phase 3','phase iii','trial fail','clinical hold','acquisition','merger',
    'antitrust','lawsuit','settlement','guidance cut','guidance raise','bankruptcy','recall','approval','rejected'
)
MODERATE_TERMS = (
    'earnings','revenue','eps','partnership','contract','product launch','buyback','dividend','upgrade','downgrade',
    'phase 2','phase ii','investor day','ceo','cfo','restructur'
)
RISK_TERMS = ('fda','phase 3','phase iii','trial','antitrust','lawsuit','settlement','court','regulatory','approval','rejected','recall')


def parse_gdelt_date(value: str) -> datetime | None:
    if not value:return None
    for fmt in ('%Y%m%dT%H%M%SZ','%Y%m%d%H%M%S'):
        try:return datetime.strptime(value,fmt).replace(tzinfo=timezone.utc)
        except ValueError:pass
    return None


def article_materiality(title: str) -> str:
    x=title.lower()
    if any(k in x for k in MAJOR_TERMS): return 'Major'
    if any(k in x for k in MODERATE_TERMS): return 'Moderate'
    return 'Minor'


def article_risk(title: str) -> int:
    x=title.lower()
    if any(k in x for k in RISK_TERMS): return 80
    if any(k in x for k in MODERATE_TERMS): return 50
    return 25


def aggregate_news(scored_articles: list[dict[str,Any]], now: datetime | None = None) -> dict[str,Any]:
    now=now or datetime.now(timezone.utc)
    parsed=[]
    for a in scored_articles:
        dt=parse_gdelt_date(a.get('seendate',''))
        if dt is None: continue
        age=(now-dt).total_seconds()/86400
        score=float(a.get('sentiment_score',50.0))
        title=a.get('title','')
        parsed.append({**a,'_age':age,'_score':score,'_mat':article_materiality(title),'_risk':article_risk(title)})
    def avg(days):
        vals=[a['_score'] for a in parsed if a['_age']<=days]
        return mean(vals) if vals else 50.0
    d7,d30,d90=avg(7),avg(30),avg(90)
    domains={urlparse(a.get('url','')).netloc for a in parsed if a.get('url')}
    n=len(parsed)
    confidence='High' if n>=20 and len(domains)>=5 else 'Medium' if n>=8 and len(domains)>=3 else 'Low'
    mats=Counter(a['_mat'] for a in parsed if a['_age']<=30)
    materiality='Major' if mats['Major']>=1 else 'Moderate' if mats['Moderate']>=2 else 'Minor'
    risk=max([a['_risk'] for a in parsed if a['_age']<=30] or [25])
    # Most material, then most extreme sentiment, then most recent.
    order={'Major':3,'Moderate':2,'Minor':1}
    ranked=sorted(parsed,key=lambda a:(order[a['_mat']],abs(a['_score']-50),-a['_age']),reverse=True)
    key=ranked[0] if ranked else {}
    return {'7D Sentiment':d7,'30D Sentiment':d30,'90D Sentiment':d90,'News Confidence':confidence,'Materiality':materiality,'Catalyst Risk':risk,
        'Key News':key.get('title',''),'Primary Source':key.get('url',''),'Article Count':n,'Source Count':len(domains)}
