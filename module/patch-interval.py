# Keeps the ecoNET app's periodic threads (checkSysParamsThread, the watchdog) alive across clock jumps.
# settings.Interval.run sleeps "period - time the job took". When NTP moves the clock forward during
# the job (the module boots at 2019-11-20) or the job takes longer than the period, that is negative,
# Python 2.7 raises IOError 22 outside the try and the thread dies for good; a backward jump would make
# it sleep that much longer. 3.2.3879 skips negative sleeps; this also caps them at the period.
# Safe to run again.
import re
import sys
p = sys.argv[1] if len(sys.argv) > 1 else '/www/econet/settings.py'
s = open(p).read()
old = re.compile(r"^( +)time\.sleep\(leftTime\)$", re.M)
if "time.sleep(min(max(leftTime,0),self.seconds))" in s:
    print("already patched")
elif len(old.findall(s)) != 1:
    print("time.sleep(leftTime) not found exactly once; not changed")
else:
    open(p, "w").write(old.sub(r"\1time.sleep(min(max(leftTime,0),self.seconds))", s))
    print("patched")
