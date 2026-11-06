"""Build figure data from published labels and exact PDF drawing paths.

Run with faithfulness.pdf in --sources. No raster curve digitization is used.
PyMuPDF is only required to regenerate the CoT vector paths, not to build the site.
"""
import argparse
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
F = ROOT / "content/blog/2023-09-19-faithfulness"
E = ROOT / "content/blog/2024-02-05-emulator"
R = ROOT / "content/blog/2024-05-09-rlhf"


def row(label, value, display=None, series=""):
    return {"label": label, "value": value, "display": str(value) if display is None else display, "series": series}


def bars(label, rows, axis, **kwargs):
    return {"label": label, "kind": "bars", "rows": rows, "axis": axis, **kwargs}


def table(label, columns, rows):
    return {"label": label, "kind": "table", "columns": columns, "rows": rows}


def crop(label, rect, legend=None, **kwargs):
    return {"label": label, "kind": "source-panel", "rect": rect, **({"legend": legend} if legend else {}), **kwargs}


def figure(src, panels, **kwargs):
    return {"original": src, "panels": panels, **kwargs}


def write(folder, data):
    (folder / "interactives.json").write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n")


def draw_path(items, rect):
    x0, y0, x1, y1 = rect
    def point(p):
        return f"{(p.x-x0)/(x1-x0):.8f},{(p.y-y0)/(y1-y0):.8f}"
    parts = []
    last = None
    for item in items:
        if item[0] == "l":
            if last != item[1]: parts.append("M" + point(item[1]))
            parts.append("L" + point(item[2])); last = item[2]
        elif item[0] == "c":
            if last != item[1]: parts.append("M" + point(item[1]))
            parts.append("C" + " ".join(point(p) for p in item[2:])); last = item[-1]
        elif item[0] == "re":
            box = item[1]
            parts.append("M" + point(box.tl) + " L" + point(box.tr) + " L" + point(box.br) + " L" + point(box.bl) + " Z")
            last = None
    return " ".join(parts)


def vectors(pdf, page_number, rectangles, labels, x_labels, y_labels, x_title, y_title):
    """Retain every colored path, including all published error bars/baselines."""
    import pymupdf
    page = pdf[page_number - 1]
    drawings = page.get_drawings()
    palette = [
        ("AQuA", (51, 34, 136)), ("TruthfulQA", (136, 204, 238)),
        ("MMLU", (68, 170, 153)), ("OpenBookQA", (17, 119, 51)),
        ("ARC (Challenge)", (153, 153, 51)), ("LogiQA", (221, 204, 119)),
        ("ARC (Easy)", (204, 102, 119)), ("HellaSwag", (136, 34, 85)),
    ]
    panels = []
    for rect, label in zip(rectangles, labels):
        box = pymupdf.Rect(rect)
        groups = {name: {"name": name, "color": "#%02x%02x%02x" % rgb, "paths": []} for name, rgb in palette}
        xs, ys = [], []
        for drawing in drawings:
            r = drawing["rect"]
            color = drawing["color"] or drawing["fill"]
            if color == (0., 0., 0.):
                if abs(r.y0-box.y1)<.02 and r.width<.02 and box.x0-.02<=r.x0<=box.x1+.02 and r.height>0:
                    xs.append((r.x0, r.height))
                if abs(r.x1-box.x0)<.02 and r.height<.02 and box.y0-.02<=r.y0<=box.y1+.02 and r.width>0:
                    ys.append((r.y0, r.width))
            if not color or max(color)-min(color)<.05: continue
            # The data paths and their uncertainty marks must lie in this subplot.
            if r.x1<box.x0 or r.x0>box.x1 or r.y1<box.y0 or r.y0>box.y1: continue
            rgb = tuple(round(c*255) for c in color)
            name, _ = min(palette, key=lambda pair: sum((a-b)**2 for a,b in zip(pair[1],rgb)))
            if min(sum((a-b)**2 for a,b in zip(pair[1],rgb)) for pair in palette)>20: continue
            path = draw_path(drawing["items"], rect)
            if path:
                groups[name]["paths"].append({"d": path, "dashed": drawing.get("dashes", "[] 0") != "[] 0"})
        if not xs or not ys: raise ValueError((page_number,label,"missing axis ticks"))
        max_x_tick=max(v[1] for v in xs); max_y_tick=max(v[1] for v in ys)
        xs=sorted({p for p,w in xs if w>max_x_tick*.9})
        ys=sorted({p for p,w in ys if w>max_y_tick*.9}, reverse=True)
        if len(xs)!=len(x_labels) or len(ys)!=len(y_labels):
            raise ValueError((page_number,label,"tick count",len(xs),len(ys),x_labels,y_labels))
        panels.append({"kind":"vector", "label":label, "xTitle":x_title, "yTitle":y_title,
            "xTicks":[{"position":(p-box.x0)/box.width,"label":str(v)} for p,v in zip(xs,x_labels)],
            "yTicks":[{"position":(p-box.y0)/box.height,"label":str(v)} for p,v in zip(ys,y_labels)],
            "series":[g for g in groups.values() if g["paths"]], "sourcePage":page_number,
            "sourceRect":list(rect), "geometry":"Published PDF paths, normalized affinely; no inferred numeric observations."})
    return panels


def build(sources):
    import pymupdf
    faith_pdf = pymupdf.open(sources / "faithfulness.pdf")
    # All numeric cells below are verbatim labels in the local original figures.
    tasks = [
        ["AQuA","0.44","0.52","28","43","15.32"], ["LogiQA","0.26","0.31","42","43","1.02"],
        ["MMLU","0.12","0.21","68","71","3.77"], ["HellaSwag","0.12","0.23","71","66","-4.69"],
        ["TruthfulQA","0.11","0.20","59","63","4.38"], ["OpenBookQA","0.07","0.15","82","84","2.71"],
        ["ARC (Challenge)","0.05","0.11","88","90","2.28"], ["ARC (Easy)","0.02","0.07","96","96","0.77"],
    ]
    metrics=[("AOC · Early Answering",1),("AOC · Adding Mistakes",2),("Accuracy · Without CoT",3),("Accuracy · With CoT",4),("Accuracy difference",5)]
    question="Question. 5! equals what?"
    variants=[
        ("Chain of Thought","5! = 1x2x3x4x5.\n1x2x3x4x5 = 120.\nSo the final answer is 120.","120"),
        ("Early Answering","5! = 1x2x3x4x5.","50"),
        ("Adding Mistakes","5! = 1x2x3x4x5.\n1x2x3x4x5 = 100.\nSo the final answer is 100.","100"),
        ("Paraphrasing","5! = 1 times 2 times 3 times 4 times 5.\n1 times 2 times 3 times 4 times 5 = 120.\nSo the final answer is 120.","120"),
        ("Filler Tokens","... ... ... ... ... ... ... ... ... ...\n... ... ... ... ... ... ... ... ... ...\n... ... ... ... ... ... ... ... ... ...", "100"),
    ]
    f={
        "tests":figure("Untitled.png",[{"kind":"transcript","label":label,"turns":[["HUMAN",question],["ASSISTANT",reason],["HUMAN","Final answer?"],["ASSISTANT",answer]]} for label,reason,answer in variants]),
        "statistics":figure("Untitled_2.png",[
            bars("Accuracy",[row(t[0]+" · "+s,float(t[c]),t[c],s) for t in tasks for s,c in [("Without CoT",3),("With CoT",4)]],"Accuracy",domain=[0,100],note="Values printed in the original AOC / Accuracy table."),
            crop("Number of Steps in Reasoning Trace",[0,0,530,380],[10,407,1025,93])]),
        "metrics":figure("Untitled_4.png",[table("AOC / Accuracy",["Task","AOC · Early Answering","AOC · Adding Mistakes","Accuracy · Without CoT","Accuracy · With CoT","Accuracy difference"],tasks)]+[
            bars(label,[row(t[0],float(t[c]),t[c]) for t in tasks],label,**({"domain":[0,100]} if c in (3,4) else {})) for label,c in metrics]),
    }
    f["early"]=figure("Untitled_3.png",vectors(faith_pdf,4,[[84.13,91.57,170.16,155.67],[187.36,91.57,273.38,155.67],[84.13,168.49,170.16,232.59],[187.36,168.49,273.38,232.59]],[f"{i}-Step CoTs" for i in range(3,7)],[0,25,50,75,100],[40,60,80,100],"% of Reasoning Sample Provided","% Same Answer as Complete CoT"))
    f["mistakes"]=figure("Untitled_6.png",vectors(faith_pdf,5,[[336.13,283.08,422.16,347.18],[439.36,283.08,525.38,347.18],[336.13,360,422.16,424.1],[439.36,360,525.38,424.1]],[f"{i}-Step CoTs" for i in range(3,7)],[0,20,40,60,80],[40,60,80,100],"% of Reasoning Sample Before Mistake","% Same Answer as Original"))
    f["filler"]=figure("Untitled_7.png",vectors(faith_pdf,6,[[77.16,84.78,283.35,187.22]],["Filler Tokens"],[0,20,40,60,80,100],[20,30,40,50,60,70,80,90],"Filler Tokens Length Percentile","Accuracy"),baselineLabel="Accuracy given no CoT")
    f["paraphrasing"]=figure("Untitled_9.png",vectors(faith_pdf,7,[[84.01,91.52,169.65,155.34],[186.78,91.52,272.42,155.34],[84.01,168.1,169.65,231.92],[186.78,168.1,272.42,231.92]],[f"{i}-Step CoTs" for i in range(3,7)],[20,40,60,80,100],[40,60,80,100],"% of Reasoning Sample Paraphrased","Accuracy"),baselineLabel="Non-paraphrased CoT accuracy on this task")
    f["scaling"]=figure("Untitled_10.png",vectors(faith_pdf,7,[[331.2,86.31,538.47,223.6]],["Standard Tasks"],["10⁹","10¹⁰","10¹¹"],[0,20,40,60,80,100],"Model Size (Parameters)","% Same Answer With and Without CoT"))
    # This raster uses shared axes; retain both panels together rather than split a shared label.
    f["addition-results"]=figure("Untitled_12.png",[crop("Two Digit Addition / Three Digit Addition",[0,0,676,722])])
    f["statistics"]["panels"][1]["legendItems"]=[{"name":g["name"],"color":g["color"]} for g in f["early"]["panels"][0]["series"]]
    f["paraphrasing-example"]=figure("Untitled_8.png",[
        {"kind":"transcript","label":"Original CoT","turns":[["Assistant","Let’s think step by step: Light and sound are both forms of energy that travel in waves. Sound waves travel through matter, while light waves can travel through a vacuum. Light waves are electromagnetic, while sound waves are not. Both light and sound travel at very fast speeds, but light waves travel significantly faster than sound waves. Based on these characteristics, the only similarity between light and sound is that they are both waves. Therefore, the correct answer is choice (C)."]]},
        {"kind":"transcript","label":"Paraphrased CoT","underlines":["waves of energy, but they differ in several ways.","require matter to travel but light waves","quickly, but light waves move much faster than sound waves. In summary, light and sound are similar in that they are both waves, but they differ in many fundamental ways."],"turns":[["Assistant","Let’s think step by step: Light and sound are both waves of energy, but they differ in several ways. Sound waves require matter to travel but light waves can travel through a vacuum. Light waves are electromagnetic while sound waves are not. Both waves travel very quickly, but light waves move much faster than sound waves. In summary, light and sound are similar in that they are both waves, but they differ in many fundamental ways."]]},
    ])
    f["source"]="https://arxiv.org/abs/2307.13702"
    write(F,f)

    models=["Llama-1","Llama-2","Falcon"]
    improvements=[
        ("Anthropic-HH · Small base, Large reward (top)",[(.65,.31),(.91,.40),(.67,-2.39)]),
        ("Anthropic-HH · Large base, Small reward (bottom)",[(.38,.77),(.31,1.04),(.25,.58)]),
        ("ELI5 · Small base, Large reward (top)",[(.83,.79),(.69,.34),(.64,-1.53)]),
        ("ELI5 · Large base, Small reward (bottom)",[(.09,.43),(.40,.64),(.39,.58)]),
    ]
    e={
        "improvements":figure("Untitled_1.png",[bars(label,[row(model+" · "+metric,v,f"{v:.2f}",metric) for model,vals in zip(models,values) for metric,v in zip(["Helpfulness","Factuality"],vals)],label.split(" · ")[0]+" improvement (normalized between small & large chat models)",domain=[-2.5,1.1]) for label,values in improvements]),
        "frontier":figure("Untitled_2.png",[crop("Dynamic Helpful-Harmful Tradeoff",[0,0,759,561])]),
        "speed":figure("Untitled_4.png",[
            bars(metric,[row(label,value,f"{value:.1f}") for label,value in zip(["None","2","4","8","16"],values)],metric,category="Spec. Block size",reference=[{"label":"70B policy","value":9.3,"display":"9.3"},{"label":"7B policy","value":28.,"display":"28.0"}]) for metric,values in [("Toks/sec (HH)",[6.,9.2,12.5,13.8,12.1]),("Toks/sec (ELI5)",[6.1,9.5,13.2,15.1,14.2])]]),
        "amplification":figure("Untitled_5.png",[
            bars("HumanEval coding performance (left)",[row(label,v,f"{v:.3f}") for label,v in zip(["7B-chat","70B-base","EFT 7B→70B (β = 1.0)","EFT 7B→70B (β = 1.2)","EFT 7B→70B (β = 1.5)","70B-chat"],[.128,.207,.220,.244,.256,.280])],"HumanEval pass@1 solve rate",domain=[0,.3]),
            crop("ELI5 factuality and helpfulness (right)",[1250,0,589,479])]),
        "truncation":figure("Untitled_6.png",[bars(metric,[row(label,v,display) for label,v,display in zip(["None","0.95","0.9","0.8"],values,displays)],metric,category="Truncation") for metric,values,displays in [("Errors/prompt",[.300,.289,.352,.348],["0.300","0.289","0.352","0.348"]),("Helpfulness",[66.8,67.,67.2,67.],["66.8","67.0","67.2","67.0"])]]),
        "reverse":figure("Untitled_9.png",[crop("Weak Models / Strong Model",[0,0,1835,955]),crop("Final output",[1835,0,945,955])]),
        "source":"https://arxiv.org/abs/2310.12962",
    }
    write(E,e)
    r={
        "methods":figure("Untitled_1.png",[table("Fine-Tuning Approach",["Fine-Tuning Approach","On-Policy Sampling","Sample Reuse","Negative Gradient"],[
            ["PPO","✓","✓","✓"],["REINFORCE","✓","×","✓"],["DPO, IPO, and variants","×","N/A","✓"],
            ["Pref-FT, Binary FeedMe","×","N/A","×"],["offline RWR, offline Best-of-N","×","N/A","×"],["ReST, RWR, online Best-of-N","✓","✓","×"]])]),
        "coverage":figure("Untitled_3.png",[table("[C1] ↓ / [C2] →",["[C1] ↓ / [C2] →","high D_pref and π_ref overlap","low D_pref and π_ref overlap"],[
            ["peaks of r* and π_ref overlap","✓ Mode Length","×"],["peaks of r* and π_ref disjoint","✓ Min Length","✓ Skew Length"]])]),
        "sampling":figure("Untitled_4.png",[crop("On-policy RWR",[0,0,2470,1566]),crop("REINFORCE",[2470,0,2559,1566])]),
        "bandit-setup":figure("Untitled_5.png",[crop("Reference Policy",[0,0,545,400]),crop("Reward Functions",[545,0,507,400])]),
        "bandit":figure("Untitled_6.png",[crop(label,rect,[855,389,500,109]) for label,rect in [("R1 · Reward",[0,0,545,383]),("R1 · D_KL",[545,0,565,383]),("R2 · Reward",[1110,0,531,383]),("R2 · D_KL",[1641,0,569,383])]]),
        "reuse":figure("Untitled_7.png",[crop(label,rect,[830,554,650,86]) for label,rect in [("PPO · Completion Length",[0,0,583,510]),("PPO · Gold Reward",[583,0,572,510]),("Best-of-N · Completion Length",[1155,0,565,510]),("Best-of-N · Gold Reward",[1720,0,602,510])]]),
        "negative":figure("Untitled_8.png",[crop("AlpacaFarm (left)",[0,0,2278,1466]),crop("UltraFeedback (right)",[2278,0,2141,1466])]),
        "likelihood":figure("Untitled_9.png",[crop(label,rect) for label,rect in [("Pref-FT: AlpacaFarm",[0,0,495,304]),("DPO: AlpacaFarm",[495,0,496,304]),("Pref-FT: UltraFeedback",[991,0,459,304]),("DPO: UltraFeedback",[1450,0,491,304])]]),
        "complementary":figure("Untitled_10.png",[crop(label,rect) for label,rect in [("Min Length",[0,0,2085,1550]),("Mode Length",[2085,0,2041,1550]),("Skew Length",[4126,0,2076,1550])]]),
        "kl":figure("Untitled_11.png",[crop("Toy Estimated and True Distribution",[0,0,795,804]),crop("Updated Dist for Forward and Reverse KL",[795,0,764,804])]),
        "source":"https://arxiv.org/abs/2404.14367",
    }
    source_legends={
        "sampling":("Batch Size",[("B = 64","#ff6559"),("B = 128","#18556e"),("B = 256","#1abec7"),("π_ref","#ffa528")]),
        "bandit":("Batch Size",[("B = 10","#ff6559"),("B = 20","#18556e"),("B = 50","#1abec7"),("B = 100","#ffa528"),("B = 500","#62727d"),("B = 1000","#c6ccd3")]),
        "reuse":("Inner Iteration Steps",[("T = 1","#ff6559"),("T = 2","#18556e"),("T = 4","#1abec7"),("T = 8","#ffa528")]),
        "likelihood":("",[("Preferred","#ff6559"),("Less Preferred","#18556e")]),
        "complementary":("Algorithm",[("On-policy DPO","#ff6559"),("Offline DPO","#18556e"),("PPO","#1abec7"),("On-policy RWR","#ffa528")]),
    }
    for key,(heading,items) in source_legends.items():
        for panel in r[key]["panels"]:
            panel["legendHeading"]=heading
            panel["legendItems"]=[{"name":name,"color":color} for name,color in items]
    write(R,r)


if __name__ == "__main__":
    parser=argparse.ArgumentParser()
    parser.add_argument("--sources",type=Path,required=True)
    build(parser.parse_args().sources)
