#!/usr/bin/env python3
"""Heuristic bot-like vs human-like session scoring; not proof of identity."""
from __future__ import annotations
import json, math, re, sys
from collections import Counter
from dataclasses import dataclass, field
from typing import Any, Sequence

@dataclass(slots=True)
class Turn:
    text: str
    gap_seconds: float | None = None
    role: str = "user"

@dataclass
class Score:
    points: int = 0
    signals: list[str] = field(default_factory=list)
    def add(self, pts: int, name: str) -> None:
        self.points += pts
        self.signals.append(f"+{pts} {name}")

def _timing_variance(turns: Sequence[Turn]) -> tuple[int, str]:
    gaps = [t.gap_seconds for t in turns if t.gap_seconds is not None and math.isfinite(t.gap_seconds) and t.gap_seconds > 0]
    if len(gaps) < 3: return 0, ""
    mean = sum(gaps) / len(gaps)
    cv = math.sqrt(sum((g-mean)**2 for g in gaps)/len(gaps)) / mean if mean else 0
    return (2, f"timing_variance cv={cv:.2f} (metronomic)") if cv < .25 else (0, "")

def _length_variance(turns: Sequence[Turn]) -> tuple[int, str]:
    lens = [len(t.text.strip()) for t in turns if isinstance(t.text, str) and t.text.strip()]
    if len(lens) < 4: return 0, ""
    mean = sum(lens)/len(lens)
    cv = math.sqrt(sum((n-mean)**2 for n in lens)/len(lens))/mean if mean else 0
    return (2, f"length_variance cv={cv:.2f} (uniform)") if cv < .30 else (0, "")

def _repetition_ratio(turns: Sequence[Turn]) -> tuple[int, str]:
    texts = [re.sub(r"\s+", " ", t.text.strip().lower()) for t in turns if isinstance(t.text,str) and t.text.strip()]
    if len(texts) < 4: return 0, ""
    counts = Counter(texts)
    ratio = sum(c-1 for c in counts.values() if c > 1)/len(texts)
    if ratio > .30: return 2, f"repetition_ratio={ratio:.2f}"
    tokens = [set(x.split()) for x in texts]
    near = sum(1 for i in range(len(tokens)) for j in range(i+2,len(tokens))
               if tokens[i] | tokens[j] and len(tokens[i]&tokens[j])/len(tokens[i]|tokens[j]) > .85)
    return (2, f"near_duplicate_pairs={near}") if near >= 2 else (0, "")

def _mid_thought_corrections(turns: Sequence[Turn]) -> tuple[int, str]:
    p = re.compile(r"\b(wait|actually|no i mean|scratch that|i meant|oops|hold on)\b|--\s|\.\.\.\s|\?\s+", re.I)
    hits = sum(1 for t in turns if isinstance(t.text,str) and p.search(t.text))
    return (1, "zero_self_corrections") if hits == 0 and len(turns) >= 5 else (0, "")

def _context_reuse(turns: Sequence[Turn]) -> tuple[int, str]:
    users = [t for t in turns if t.role == "user"]
    assistants = [t for t in turns if t.role == "assistant"]
    if len(users)<2 or len(assistants)<2: return 0, ""
    reuse = 0
    for u in users:
        ut = set(u.text.lower().split())
        if ut and any(len(ut & set(a.text.lower().split()))/len(ut) > .60 for a in assistants): reuse += 1
    return (2, f"context_reuse_turns={reuse}") if reuse >= 2 else (0, "")

def coerce_turns(data: Any) -> list[Turn]:
    if not isinstance(data,list): raise ValueError("Input must be a JSON array.")
    out=[]
    for i,item in enumerate(data):
        if not isinstance(item,dict) or not isinstance(item.get("text"),str):
            raise ValueError(f"Turn {i} requires a string text field.")
        role=item.get("role","user")
        if not isinstance(role,str) or role not in {"user","assistant"}:
            raise ValueError(f"Turn {i} role must be user or assistant.")
        gap=item.get("gap_seconds")
        if gap is not None:
            if isinstance(gap,bool) or not isinstance(gap,(int,float)): raise ValueError(f"Turn {i} gap_seconds must be numeric.")
            gap=float(gap)
            if not math.isfinite(gap) or gap<0: raise ValueError(f"Turn {i} gap_seconds must be finite and non-negative.")
        out.append(Turn(item["text"],gap,role))
    return out

def score_session(turns: Sequence[Turn]) -> dict[str, Any]:
    if len(turns)<4: return {"classification":"INSUFFICIENT_DATA","points":0,"signals":[],"turns":len(turns)}
    s=Score()
    for fn in (_timing_variance,_length_variance,_repetition_ratio,_mid_thought_corrections,_context_reuse):
        pts,name=fn(turns)
        if pts: s.add(pts,name)
    label="BOT" if s.points>=6 else "SUSPICIOUS" if s.points>=1 else "HUMAN"
    return {"classification":label,"points":s.points,"signals":s.signals,"turns":len(turns)}

def main() -> int:
    try:
        print(json.dumps(score_session(coerce_turns(json.load(sys.stdin))),indent=2))
        return 0
    except (json.JSONDecodeError,ValueError) as exc:
        print(json.dumps({"error":str(exc)}),file=sys.stderr)
        return 2

if __name__ == "__main__":
    raise SystemExit(main())
