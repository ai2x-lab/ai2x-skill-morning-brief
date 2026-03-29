#!/usr/bin/env python3
import json
import subprocess
from datetime import datetime, timedelta


def run(cmd):
    return subprocess.check_output(cmd, shell=True, text=True)


def parse_json(s):
    return json.loads(s)


def main():
    today = datetime.now().date()
    end = today + timedelta(days=7)

    try:
        t = parse_json(run("twcal today --json"))
        r = parse_json(run(f"twcal range --start {today.isoformat()} --end {end.isoformat()} --json"))
    except Exception:
        print("民俗行事曆素材：讀取失敗")
        return

    record = ((t.get("data") or {}).get("record") or {})
    lunar_text = f"{record.get('lunar_month_name','?')}月{record.get('lunar_day_name','?')}"
    lunar_code = f"{int(record.get('lunar_month',0)):02d}-{int(record.get('lunar_day',0)):02d}" if record.get('lunar_month') else ""

    festivals_today = [f.get("name_zh") for f in (record.get("festivals") or []) if f.get("name_zh")]

    items = ((r.get("data") or {}).get("items") or [])
    next7 = []
    for it in items:
        date = it.get("solar_date")
        for f in it.get("festivals") or []:
            name = f.get("name_zh")
            if name and date:
                next7.append((date, name))

    # de-dup
    seen = set()
    uniq = []
    for d, n in sorted(next7):
        k = (d, n)
        if k in seen:
            continue
        seen.add(k)
        uniq.append((d, n))

    print(f"農曆：{lunar_text} ({lunar_code})")
    if festivals_today:
        print("今日民俗重點：" + "；".join(f"今天是{x}" for x in festivals_today))
    if uniq:
        print("七日內節慶：" + "、".join(f"{d} {n}" for d, n in uniq))
    else:
        print("七日內節慶：無")


if __name__ == "__main__":
    main()
