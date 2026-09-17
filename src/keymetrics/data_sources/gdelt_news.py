from __future__ import annotations

from datetime import datetime, timezone, timedelta
from typing import Any
import requests

GDELT_DOC='https://api.gdeltproject.org/api/v2/doc/doc'


def fetch_articles(company: str, days: int = 90, max_records: int = 250) -> list[dict[str,Any]]:
    """Fetch recent English articles from the public GDELT DOC API."""
    end=datetime.now(timezone.utc); start=end-timedelta(days=days)
    params={'query':f'"{company}"','mode':'ArtList','maxrecords':max_records,'format':'json','sort':'HybridRel','startdatetime':start.strftime('%Y%m%d%H%M%S'),'enddatetime':end.strftime('%Y%m%d%H%M%S')}
    r=requests.get(GDELT_DOC,params=params,timeout=30); r.raise_for_status()
    data=r.json()
    return data.get('articles',[])


def finbert_title_scores(articles: list[dict[str,Any]], model_name: str='ProsusAI/finbert') -> list[dict[str,Any]]:
    """Optional finance-specific NLP. Install with `pip install .[nlp]`."""
    try:
        from transformers import pipeline
    except ImportError as e:
        raise RuntimeError("Install NLP extras with: pip install .[nlp]") from e
    clf=pipeline('text-classification',model=model_name,top_k=None)
    titles=[a.get('title','') for a in articles if a.get('title')]
    results=clf(titles,batch_size=16,truncation=True)
    out=[]
    for a,res in zip([x for x in articles if x.get('title')],results):
        probs={x['label'].lower():float(x['score']) for x in res}
        score=50.0+50.0*(probs.get('positive',0.0)-probs.get('negative',0.0))
        out.append({**a,'sentiment_score':max(0.0,min(100.0,score)),'finbert_probs':probs})
    return out
