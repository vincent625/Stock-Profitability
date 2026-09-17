from __future__ import annotations

from datetime import timedelta
from typing import Any


def _row(frame, names: list[str]):
    for n in names:
        if n in frame.index:
            return frame.loc[n]
    return None


def fetch_quarterly_panel(ticker: str, quarters: int = 20) -> list[dict[str, Any]]:
    """Best-effort public-data adapter using yfinance.

    Produces normalized quarterly operating metrics and trailing valuation ratios.
    Historical forward-P/E is intentionally NOT fabricated; provide a vendor/curated
    `forward_pe_history.csv` for the exact market-multiple model.
    """
    try:
        import yfinance as yf
    except ImportError as e:
        raise RuntimeError("Install live-data dependencies with: pip install .[live]") from e
    t=yf.Ticker(ticker)
    inc=t.quarterly_income_stmt
    cf=t.quarterly_cashflow
    if inc is None or inc.empty:
        raise RuntimeError(f"No quarterly income statement returned for {ticker}")
    revenue=_row(inc,["Total Revenue","Operating Revenue"])
    op_income=_row(inc,["Operating Income"])
    net_income=_row(inc,["Net Income","Net Income Common Stockholders"])
    cfo=_row(cf,["Operating Cash Flow","Total Cash From Operating Activities"]) if cf is not None else None
    capex=_row(cf,["Capital Expenditure","Capital Expenditures"]) if cf is not None else None
    dates=sorted(list(inc.columns))[-quarters:]
    if not dates:return []
    hist=t.history(start=(min(dates)-timedelta(days=10)).date(),end=(max(dates)+timedelta(days=10)).date(),auto_adjust=False)
    try:
        shares=t.get_shares_full(start=(min(dates)-timedelta(days=30)).date(),end=(max(dates)+timedelta(days=30)).date())
    except Exception:
        shares=None
    rows=[]
    rev_vals={d: float(revenue[d]) if revenue is not None and d in revenue and revenue[d]==revenue[d] else None for d in dates}
    for i,d in enumerate(dates):
        rev=rev_vals[d]
        op=float(op_income[d]) if op_income is not None and d in op_income and op_income[d]==op_income[d] else None
        ni=float(net_income[d]) if net_income is not None and d in net_income and net_income[d]==net_income[d] else None
        cfo_v=float(cfo[d]) if cfo is not None and d in cfo and cfo[d]==cfo[d] else None
        capex_v=float(capex[d]) if capex is not None and d in capex and capex[d]==capex[d] else None
        # yfinance reports capex as negative cash outflow on most tickers.
        fcf=(cfo_v + capex_v) if cfo_v is not None and capex_v is not None else None
        prev=rev_vals.get(dates[i-4]) if i>=4 else None
        rg=(rev/prev-1.0) if rev is not None and prev not in (None,0) else None
        om=(op/rev) if op is not None and rev not in (None,0) else None
        fm=(fcf/rev) if fcf is not None and rev not in (None,0) else None
        # Closest available close at/before statement date.
        px=None
        if hist is not None and not hist.empty:
            eligible=hist.loc[:d]
            if not eligible.empty: px=float(eligible['Close'].iloc[-1])
        sh=None
        if shares is not None and len(shares):
            eligible=shares.loc[:d]
            if len(eligible): sh=float(eligible.iloc[-1])
        market_cap=px*sh if px is not None and sh is not None else None
        # TTM ratios from the last four fiscal quarters.
        window=dates[max(0,i-3):i+1]
        rev_window=[rev_vals[x] for x in window if rev_vals[x] is not None]
        ttm_rev=sum(rev_window) if len(rev_window)==4 else None
        ni_window=[float(net_income[x]) for x in window if net_income is not None and x in net_income and net_income[x]==net_income[x]]
        ttm_ni=sum(ni_window) if len(ni_window)==4 else None
        ttm_fcf=None
        if cfo is not None and capex is not None and len(window)==4:
            vals=[]
            for x in window:
                if x in cfo and x in capex and cfo[x]==cfo[x] and capex[x]==capex[x]: vals.append(float(cfo[x])+float(capex[x]))
            if len(vals)==4: ttm_fcf=sum(vals)
        ps=(market_cap/ttm_rev) if market_cap and ttm_rev and ttm_rev>0 else None
        pe=(market_cap/ttm_ni) if market_cap and ttm_ni and ttm_ni>0 else None
        pfcf=(market_cap/ttm_fcf) if market_cap and ttm_fcf and ttm_fcf>0 else None
        rows.append({'ticker':ticker,'period':str(d.date()),'revenue_growth':rg,'operating_margin':om,'fcf_margin':fm,'pe':pe,'p_fcf':pfcf,'p_s':ps,'price':px})
    return rows


def current_quote(ticker: str) -> dict[str, Any]:
    import yfinance as yf
    t=yf.Ticker(ticker)
    info=t.info
    return {'ticker':ticker,'price':info.get('currentPrice') or info.get('regularMarketPrice'),'forward_pe':info.get('forwardPE'),'market_cap':info.get('marketCap')}
