"""kiosk.py: the Brannock compliance kiosk, a fictional page on a PC from 2013.

    python demo/blackout/kiosk.py build --scene DIR --to FILE.html

DIR is what scene.py wrote. FILE.html is one self-contained page, no network and
no install, that reads nothing but scene.json (each box's sealed answers, what it
sent and received, what the stack found, and what Audit saw). It never reads a
box, a key or a pile.

It is made to look like what it pretends to run on, a shop-floor office PC bought
in 2013: a Windows 7 desktop at 1024 by 768, a blue title bar, grey buttons, a
taskbar whose clock reads 2:10 AM on 10/18/2026, the minute a furnace went to HOLD
that no one acknowledged. The script is ES5 and the layout is tables and floats,
because nothing on that machine is newer than that machine (a test holds it:
no arrow functions, no let or const, no template strings, no flexbox).

- **Log on** as any of the eight; you see that person's papers and no one else's.
  Asking for another person's papers is a dialog: access denied, nothing on record
  for this logon.
- **Papers**: what the person sealed, what they sent, what arrived.
- **SEC check**: what the stack the Legal and Compliance signed found in that box.
- **Audit desk**: Audit's alone: what `kept-clash` set side by side, the join of the
  plan log to the seniority list, and the witness. Anyone else is refused.
- **Print**: a narrow receipt of the page you are on, as the office printer would.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

PAGE = r"""<!DOCTYPE html>
<html><head><meta charset="utf-8">
<meta http-equiv="X-UA-Compatible" content="IE=edge">
<title>Brannock Steel Works - Compliance Kiosk</title>
<style type="text/css">
body{margin:0;background:#3a6ea5;font-family:Tahoma,"Segoe UI",Arial,sans-serif;font-size:12px;color:#000}
#screen{width:1024px;height:768px;margin:0 auto;position:relative;background:#3a6ea5;overflow:hidden}
#win{position:absolute;left:28px;top:20px;width:966px;height:672px;background:#f0f0f0;border:1px solid #1c3a63;
 -webkit-box-shadow:4px 6px 14px #1c2f4a;box-shadow:4px 6px 14px #1c2f4a}
#title{height:28px;line-height:28px;background:#4a86c8;color:#fff;font-weight:bold;padding-left:10px;border-bottom:1px solid #1c3a63}
#title span.x{float:right;width:34px;height:18px;margin:4px 6px 0 0;background:#c8452e;border:1px solid #6b1d10;text-align:center;line-height:18px;color:#fff}
#bar{height:30px;background:#e8eef6;border-bottom:1px solid #a8b4c4;padding:4px 8px}
#bar select,#bar button,.btn{font-family:Tahoma,Arial,sans-serif;font-size:12px;background:#e1e1e1;border:1px solid #707070;padding:2px 10px;margin-right:4px}
#side{position:absolute;left:0;top:64px;width:178px;bottom:0;background:#fff;border-right:1px solid #a8b4c4;padding:8px}
#side div{padding:3px 4px;cursor:default}
#side div.on{background:#cde4f9;border:1px solid #7aa7d9;padding:2px 3px}
#main{position:absolute;left:190px;top:64px;right:0;bottom:0;overflow:auto;padding:10px 14px;background:#fff}
h2{font-size:15px;margin:2px 0 8px;color:#1c3a63}
table.t{border-collapse:collapse;width:100%;margin:6px 0 12px}
table.t td,table.t th{border:1px solid #b5b5b5;padding:3px 6px;text-align:left;vertical-align:top}
table.t th{background:#e8eef6}
.note{color:#555}.bad{color:#a02020}.ok{color:#1d6b2b}
pre{font-family:"Courier New",monospace;font-size:12px;margin:4px 0}
#crt{background:#000;color:#43ff6a;padding:8px;border:2px inset #888}
#tray{position:absolute;left:0;bottom:0;width:1024px;height:40px;background:#2a4f7c;border-top:1px solid #0e2440}
#orb{position:absolute;left:6px;top:4px;width:30px;height:30px;border-radius:15px;background:#3f9a45;border:2px solid #cfe9d0}
#clock{position:absolute;right:10px;top:4px;color:#fff;text-align:right;line-height:15px}
#dlg{display:none;position:absolute;left:300px;top:240px;width:400px;background:#f0f0f0;border:1px solid #1c3a63;z-index:9;
 -webkit-box-shadow:3px 5px 10px #000;box-shadow:3px 5px 10px #000}
#dlg .tb{background:#4a86c8;color:#fff;font-weight:bold;padding:4px 8px}
#dlg .bd{padding:14px}
#receipt{display:none}
@media print{
 #screen{display:none}
 #receipt{display:block;width:3in;font-family:"Courier New",monospace;font-size:10pt}
}
</style></head><body>
<div id="screen">
 <div id="win">
  <div id="title"><span class="x">X</span>Brannock Steel Works - Compliance Kiosk</div>
  <div id="bar">Log on as:
   <select id="who"></select>
   <button id="bpap">Papers</button><button id="bsec">SEC check</button><button id="baud">Audit desk</button>
   <button id="bother">Open someone else's papers...</button><button id="bprint">Print</button>
  </div>
  <div id="side"></div>
  <div id="main"></div>
 </div>
 <div id="dlg"><div class="tb">Windows Security</div>
  <div class="bd"><p id="dlgtext"></p><p style="text-align:right"><button id="dlgok" class="btn">OK</button></p></div></div>
 <div id="tray"><div id="orb"></div>
  <div id="clock">2:10 AM<br>10/18/2026</div></div>
</div>
<div id="receipt"></div>
<script id="data" type="application/json">__DATA__</script>
<script>
var D = JSON.parse(document.getElementById('data').firstChild.nodeValue);
var NAMES = ['trainee','compliance','legal','ir','floor','plan','steward','audit'];
var LABEL = {trainee:'Marco Villanueva',compliance:'Ruth Haldane',legal:'Priya Raman',ir:'Gil Anselm',
 floor:'Del Pruitt',plan:'Corinne Tate',steward:'Gus Wendt',audit:'Mavis Odom'};
var ROLE = {trainee:'Maintenance electrician',compliance:'Compliance Officer',legal:'Outside counsel',
 ir:'Investor relations',floor:'Melt shop foreman',plan:'Stock plan administrator',
 steward:'Local president',audit:'Audit committee chair'};
var who = 'trainee', tab = 'pap';
function $(id){return document.getElementById(id);}
function esc(s){return String(s).replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;');}
function pad(s,n){s=String(s);while(s.length<n){s+=' ';}return s;}
function each(a,f){for(var i=0;i<a.length;i++){f(a[i],i);}}
function dialog(text){$('dlgtext').innerHTML=text;$('dlg').style.display='block';}
function papers(b){
 var h='<h2>'+esc(LABEL[who])+' - '+esc(ROLE[who])+'</h2>';
 h+='<p class="note">Papers on record for this logon. Nothing here is anyone else\'s.</p>';
 h+='<table class="t"><tr><th>Sealed, in their own words</th><th>Where it comes from</th></tr>';
 if(!b.said.length){h+='<tr><td colspan="2" class="note">Nothing sealed. A box can hold papers and have nothing it may hand out.</td></tr>';}
 each(b.said,function(a){h+='<tr><td>'+esc(a.data)+'</td><td>'+esc(a.cite)+'<br><span class="note">'+esc(a.claim)+'</span></td></tr>';});
 h+='</table><table class="t"><tr><th>Sent</th><th>To</th><th>When</th></tr>';
 each(b.sent,function(s){h+='<tr><td>'+esc(s.package)+'...</td><td>'+esc(LABEL[s.to]||s.to)+'</td><td>'+esc(s.ts)+'</td></tr>';});
 if(!b.sent.length){h+='<tr><td colspan="3" class="note">Nothing sent.</td></tr>';}
 h+='</table><table class="t"><tr><th>Received</th><th>From</th><th>Result</th></tr>';
 each(b.received,function(r){h+='<tr><td>'+esc(r.package)+'...</td><td>'+esc(LABEL[r.from]||r.from)+'</td><td class="'+(r.verdict==='good'?'ok':'bad')+'">'+esc(r.verdict)+'</td></tr>';});
 if(!b.received.length){h+='<tr><td colspan="3" class="note">Nothing received.</td></tr>';}
 return h+'</table>';
}
function sec(){
 var r=D.ran[who], h='<h2>SEC check - '+esc(LABEL[who])+'</h2>';
 h+='<p class="note">The stack Legal sealed and Compliance signed, run over this person\'s own papers.</p>';
 if(!r||!r.taken){return h+'<p>Declined. An auditor runs no one\'s tools.</p>';}
 h+='<table class="t"><tr><th>Step</th><th>What it said</th></tr>';
 var fl=r.flagged.length?esc(r.flagged.join('; ')):'nothing changed with no edit of theirs';
 h+='<tr><td>fixity</td><td class="'+(r.flagged.length?'bad':'ok')+'">'+fl+'</td></tr>';
 h+='<tr><td>contradictions</td><td class="ok">nothing: two figures written on different days are left alone</td></tr>';
 h+='<tr><td>first-mention of the shipments figure</td><td>'+esc(r.first||'nowhere')+'</td></tr></table>';
 return h+'<p class="note">It can say a file was edited. It cannot say why.</p>';
}
function audit(){
 var f=D.found, h='<h2>Audit desk - Mavis Odom</h2>';
 h+='<p class="note">What Audit kept, set side by side. Neither side is picked.</p>';
 h+='<table class="t"><tr><th>Kind</th><th>One says</th><th>Another says</th></tr>';
 each(f.clash,function(c){h+='<tr><td>'+esc(c.kind)+'</td><td>'+esc(LABEL[c.senders[0]])+': '+esc(c.values[0])+'</td><td>'+esc(LABEL[c.senders[1]])+': '+esc(c.values[1])+'</td></tr>';});
 h+='</table><table class="t"><tr><th>Plan sales by employee number, joined to the seniority list</th><th>People</th></tr>';
 for(var k in f.join){if(f.join.hasOwnProperty(k)){h+='<tr><td>'+esc(k)+'</td><td>'+esc(f.join[k])+'</td></tr>';}}
 h+='</table><p class="note">The join is the scene\'s own: it says who sold when, and nothing about who knew anything.</p>';
 h+='<table class="t"><tr><th>Chain</th><th>Held to what Audit kept</th></tr>';
 each(NAMES,function(n){if(f.witness[n]){h+='<tr><td>'+esc(LABEL[n])+'</td><td class="ok">'+esc(f.witness[n])+'</td></tr>';}});
 return h+'</table><p>The report is due before the next filing. What it says is outside every chain.</p>';
}
function furnace(b){
 var h='';
 each(b.said,function(a){if(a.cite.indexOf('historian')===0){
  h='<div id="crt"><pre>'+esc(pad('EAF2',6)+'02:10  MODE HOLD (SCHED)\nOPERATOR ACK  none\n\n'+a.data)+'</pre></div>';}});
 return h;
}
function render(){
 var b=D.boxes[who], h='';
 var s='';each(NAMES,function(n){s+='<div'+(n===who?' class="on"':'')+'>'+esc(LABEL[n])+'</div>';});
 $('side').innerHTML='<b>Users on this PC</b><br><br>'+s;
 if(tab==='pap'){h=papers(b)+furnace(b);}else if(tab==='sec'){h=sec();}else{h=who==='audit'?audit():'';}
 $('main').innerHTML=h;
 $('receipt').innerHTML='<pre>'+esc(text(b))+'</pre>';
}
function text(b){
 var t='BRANNOCK STEEL WORKS\nCOMPLIANCE KIOSK\n'+LABEL[who]+'\n--------------------------\n';
 if(tab==='pap'){each(b.said,function(a){t+=a.data+'\n['+a.cite+']\n\n';});}
 else if(tab==='sec'){var r=D.ran[who];t+=(!r||!r.taken)?'Declined.\n':'fixity: '+(r.flagged.join('; ')||'nothing')+'\nfirst seen: '+r.first+'\n';}
 else{each(D.found.clash,function(c){t+=c.values[0]+' / '+c.values[1]+'\n';});}
 return t+'--------------------------\nPrinted 10/18/2026 2:10 AM\n';
}
function fill(){var h='';each(NAMES,function(n){h+='<option value="'+n+'">'+esc(LABEL[n])+'</option>';});$('who').innerHTML=h;$('who').value=who;}
$('who').onchange=function(){who=$('who').value;tab='pap';render();};
$('bpap').onclick=function(){tab='pap';render();};
$('bsec').onclick=function(){tab='sec';render();};
$('baud').onclick=function(){
 if(who!=='audit'){dialog('Windows cannot open the Audit desk.<br><br>Nothing on record for this logon. (exit 42)');return;}
 tab='aud';render();};
$('bother').onclick=function(){dialog('Windows cannot open another user\'s papers.<br><br>Access is denied. Nothing on record for this logon. (exit 42)');};
$('bprint').onclick=function(){if(window.print){window.print();}};
$('dlgok').onclick=function(){$('dlg').style.display='none';};
fill();render();
</script></body></html>
"""


def build(scene: Path, to: Path) -> None:
    doc = json.loads((scene / "scene.json").read_text(encoding="utf-8"))
    keep = {
        "boxes": {
            b: {k: v[k] for k in ("said", "sent", "received", "seals")}
            for b, v in doc["boxes"].items()
        },
        "ran": doc["ran"],
        "found": doc["found"],
    }
    data = json.dumps(keep, ensure_ascii=False).replace("</", "<\\/")
    to.write_text(PAGE.replace("__DATA__", data), encoding="utf-8")
    print(f"wrote {to} ({to.stat().st_size} bytes), {len(keep['boxes'])} users")


if __name__ == "__main__":
    a = sys.argv[1:]
    if len(a) != 5 or a[0] != "build" or a[1] != "--scene" or a[3] != "--to":
        print(__doc__.split("\n\n")[0], file=sys.stderr)
        raise SystemExit(2)
    build(Path(a[2]), Path(a[4]))
