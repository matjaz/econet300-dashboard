# Adds the burner's output flags to regParams.curr, decoded as in ecoNET 3.2.3879 (and PyPlumIO),
# and the controller's whole outputs word as "outputs", for the outputs no firmware names
# (e.g. 0x10 and 0x100 turn a Pellas X REVO's rotating hearth). Safe to run again: it only adds missing lines.
import sys
p = sys.argv[1] if len(sys.argv) > 1 else '/www/econet/ecomax.py'
s = open(p).read()
anchor = "   self.data.contactGZCActive=bool(outputs&0x2000)\n"
lines = ["   self.data.fanWorks=bool(outputs&0x01)\n",
         "   self.data.feederWorks=bool(outputs&0x02)\n",
         "   self.data.lighterWorks=bool(outputs&0x20)\n",
         "   self.data.feederOuterWorks=bool(outputs&0x400)\n",
         "   self.data.outputs=outputs\n"]
missing = [line for line in lines if line not in s]
if not missing:
    print("already patched")
elif s.count(anchor) != 1:
    print("anchor not found exactly once; not changed")
else:
    open(p, "w").write(s.replace(anchor, anchor + "".join(missing)))
    print("patched: added %d line(s)" % len(missing))
