from __future__ import annotations

from pathlib import Path
from typing import Iterable, Mapping, Any

from .io import write_csv


def export_core_csvs(output_dir: str | Path, fundamental_rows: list[dict[str,Any]], opportunity_rows: list[dict[str,Any]]) -> None:
    out=Path(output_dir); out.mkdir(parents=True,exist_ok=True)
    write_csv(out/"fundamental_model.csv",fundamental_rows)
    write_csv(out/"opportunity_ranking.csv",opportunity_rows)


def make_charts(output_dir: str | Path, opportunity_rows: list[dict[str,Any]]) -> None:
    """Create two portable PNG charts. Matplotlib is only imported when requested."""
    import matplotlib.pyplot as plt
    out=Path(output_dir); out.mkdir(parents=True,exist_ok=True)
    top=opportunity_rows[:15]
    labels=[r["Ticker"] for r in top][::-1]
    vals=[r["Opportunity Score"] for r in top][::-1]
    fig,ax=plt.subplots(figsize=(10,7))
    ax.barh(labels,vals)
    ax.set_xlabel("Opportunity Score")
    ax.set_title("Top 15 Opportunity Scores")
    fig.tight_layout(); fig.savefig(out/"top15_opportunity.png",dpi=160); plt.close(fig)

    qqq=[r for r in opportunity_rows if r["Universe"]=="QQQ"]
    hc=[r for r in opportunity_rows if r["Universe"]=="Healthcare"]
    fig,ax=plt.subplots(figsize=(9,7))
    ax.scatter([r["Fundamental Integrated Score"] for r in qqq],[r["Adjusted News Sentiment"] for r in qqq],label="QQQ")
    ax.scatter([r["Fundamental Integrated Score"] for r in hc],[r["Adjusted News Sentiment"] for r in hc],label="Healthcare")
    ax.axhline(50,linewidth=1); ax.axvline(55,linewidth=1)
    ax.set_xlabel("Fundamental Integrated Score"); ax.set_ylabel("Adjusted News Sentiment")
    ax.set_title("Fundamentals vs News Sentiment"); ax.legend(); fig.tight_layout()
    fig.savefig(out/"fundamental_vs_sentiment.png",dpi=160); plt.close(fig)


def export_xlsx(output_path: str | Path, fundamental_rows: list[dict[str,Any]], sentiment_rows: list[dict[str,Any]], opportunity_rows: list[dict[str,Any]]) -> None:
    """Optional portable Excel export using XlsxWriter (`pip install .[excel]`)."""
    try:
        import xlsxwriter
    except ImportError as e:
        raise RuntimeError("Excel export requires the optional 'excel' extra: pip install .[excel]") from e
    output_path=Path(output_path); output_path.parent.mkdir(parents=True,exist_ok=True)
    wb=xlsxwriter.Workbook(output_path)
    header=wb.add_format({'bold':True,'font_color':'white','bg_color':'#244B3A','text_wrap':True})
    title=wb.add_format({'bold':True,'font_color':'white','bg_color':'#244B3A','font_size':15})
    pct=wb.add_format({'num_format':'0.0%;[Red](0.0%);-'})
    num=wb.add_format({'num_format':'0.0;[Red](0.0);-'})
    def add_sheet(name,rows):
        ws=wb.add_worksheet(name[:31]); ws.hide_gridlines(2)
        if not rows:return
        fields=list(rows[0].keys())
        ws.merge_range(0,0,0,len(fields)-1,name,title)
        for c,h in enumerate(fields): ws.write(2,c,h,header)
        for r_idx,row in enumerate(rows,3):
            for c,h in enumerate(fields):
                v=row.get(h)
                fmt=pct if 'Return' in h or h.endswith('%') else num if isinstance(v,float) else None
                ws.write(r_idx,c,v,fmt)
        ws.freeze_panes(3,4); ws.autofilter(2,0,2+len(rows),len(fields)-1)
        for c,h in enumerate(fields): ws.set_column(c,c,min(max(len(h)+2,11),34))
    add_sheet('Opportunity_Ranking',opportunity_rows)
    add_sheet('Fundamental_Model',fundamental_rows)
    add_sheet('News_Sentiment',sentiment_rows)
    wb.close()
