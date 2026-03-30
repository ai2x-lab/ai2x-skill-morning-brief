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
    # T-3 / T-1 / today only
    target_offsets = {0: "今天", 1: "明天", 3: "三天後"}
    reminders = []

    for it in items:
        date_str = it.get("solar_date")
        if not date_str:
            continue
        try:
            d = datetime.strptime(date_str, "%Y-%m-%d").date()
        except Exception:
            continue

        delta = (d - today).days
        if delta not in target_offsets:
            continue

        for f in it.get("festivals") or []:
            name = f.get("name_zh")
            if name:
                reminders.append((delta, date_str, name))

    # de-dup and stable sort
    seen = set()
    uniq = []
    for delta, d, n in sorted(reminders, key=lambda x: (x[0], x[1], x[2])):
        k = (delta, d, n)
        if k in seen:
            continue
        seen.add(k)
        uniq.append((delta, d, n))

    print(f"農曆：{lunar_text} ({lunar_code})")
    if festivals_today:
        print("今日民俗重點：" + "；".join(f"今天是{x}" for x in festivals_today))

    if uniq:
        msg = []
        for delta, d, n in uniq:
            msg.append(f"{target_offsets.get(delta, str(delta)+'天後')}（{d}）{n}")
        print("節慶提醒（T-3/T-1/當天）：" + "、".join(msg))
    else:
        print("節慶提醒（T-3/T-1/當天）：無")


if __name__ == "__main__":
    main()
