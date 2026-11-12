"""Generate the assignment report draft; distinguish user-confirmed storage from pending walking trials."""
from pathlib import Path
from reportlab.pdfgen import canvas
from reportlab.lib.colors import HexColor, white
from reportlab.lib.styles import ParagraphStyle
from reportlab.platypus import Paragraph
from reportlab.lib.enums import TA_LEFT

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT.parent / 'submission' / '01_Report_DRAFT.pdf'
OUT.parent.mkdir(exist_ok=True)
W,H = 595.28,841.89
c = canvas.Canvas(str(OUT), pagesize=(W,H))
c.setTitle('CommuteWalk - Assignment 2 - Verification pending')
blue = HexColor('#164E63'); ink = HexColor('#18313C'); muted = HexColor('#526975')
style = ParagraphStyle('body',fontName='Helvetica',fontSize=10,leading=14,textColor=ink)
y = 0

def header(page, subtitle):
 global y
 c.setFillColor(blue); c.rect(0,H-94,W,94,fill=1,stroke=0)
 c.setFillColor(white); c.setFont('Helvetica-Bold',21); c.drawString(40,H-39,'CommuteWalk')
 c.setFont('Helvetica',11); c.drawString(40,H-61,subtitle)
 c.setFont('Helvetica-Bold',9); c.drawString(40,H-80,'DRAFT - LIVE SENSOR UPLOAD CONFIRMED; WEATHER UPDATE PENDING')
 c.setFillColor(muted); c.setFont('Helvetica',8)
 c.drawString(40,25,'Urban Computing | Assignment 2 | 6 November 2026')
 c.drawRightString(W-40,25,f'{page} / 3')
 y=H-117

def text(s, gap=9):
 global y
 p=Paragraph(s,style); _,h=p.wrap(W-80,1000); p.drawOn(c,40,y-h); y-=h+gap

def title(s):
 global y
 y-=8
 c.setFillColor(blue); c.setFont('Helvetica-Bold',12); c.drawString(40,y,s); y-=20

def box(x,y,w,h,lines, fill='#EAF3F5'):
 c.setFillColor(HexColor(fill)); c.setStrokeColor(HexColor('#90B1BC')); c.roundRect(x,y,w,h,5,fill=1,stroke=1)
 c.setFillColor(ink)
 for i,line in enumerate(lines):
  c.setFont('Helvetica-Bold' if i==0 else 'Helvetica',9 if i==0 else 8.5)
  c.drawCentredString(x+w/2,y+h-17-i*13,line)

def arrow(x1,y1,x2,y2):
 import math
 c.setStrokeColor(blue); c.setFillColor(blue); c.setLineWidth(1.2); c.line(x1,y1,x2,y2)
 a=math.atan2(y2-y1,x2-x1)
 p=c.beginPath(); p.moveTo(x2,y2)
 p.lineTo(x2-7*math.cos(a-.4),y2-7*math.sin(a-.4)); p.lineTo(x2-7*math.cos(a+.4),y2-7*math.sin(a+.4)); p.close()
 c.drawPath(p,fill=1,stroke=0)

header(1,'Task 1 - My walking data to Firebase')
title('Purpose and platform')
text('Extend the original SwiftUI accelerometer logger into a walking commute collector. Store my own movement and GPS data in Firebase Realtime Database as JSON, retaining SQLite on the iPhone for offline recording and upload retry. Project: <b>urban-computing-a2</b>; database region: <b>europe-west1 (Belgium)</b>.')
title('Architecture: own data')
base=y-158
box(40,base,238,145,['PHYSICAL IPHONE - FOREGROUND','Core Motion: one sample every 5 s','GPS: location callbacks','Start / Arrived / End early','SQLite + durable upload queue','HTTPS PUT: ~1-second chunks'])
box(321,base+77,234,68,['FIREBASE AUTHENTICATION','Email/password sign-in','ID token; refresh token in Keychain'])
box(321,base-2,234,67,['FIREBASE REALTIME DATABASE','JSON in Belgium / europe-west1','Rules: auth.uid matches users/<uid>'])
arrow(278,base+38,321,base+30); arrow(438,base+77,438,base+65)
y=base-22
text('<b>Cloud path:</b> users/&lt;uid&gt;/journeys/&lt;session&gt;/metadata and chunks/&lt;chunk&gt;. Metadata records direction, start/end, completion, distance and station. Chunks contain motion and GPS arrays. Firebase server <b>uploadedAt</b> records receipt time.')
text('<b>Reliability:</b> outbox entries are removed only after a successful server response. Retries reuse the same path. Network failures retain queued data and trigger backoff. Original local accelerometer sessions remain available for CSV export.')
text('<b>Units:</b> X/Y/Z in g including gravity; GPS in WGS84 degrees; distance/accuracy in meters. Journey metadata times and server receipt times are Unix milliseconds; individual sample times, uptime and chunk capturedAt are seconds.')
title('Demonstration status')
text('<b>Cloud storage: USER-CONFIRMED, 6 NOVEMBER 2026.</b><br/><b>Real-time own-data upload: USER-CONFIRMED.</b><br/>After publishing the rules, the user reported zero queued records and the journeys branch present in Firebase. They then confirmed sample-containing chunks appear during recording, before Arrived. This demonstrates live own-data upload. Measured latency, a full walking-route trial and offline replay on the phone remain pending.')
c.showPage()

header(2,'Task 2 - Open weather data to Firebase')
title('Source and collection cadence')
text('Source: Met Eireann, <b>Today\'s weather Dublin Airport</b> [1]. The catalogue describes hourly observations in local Irish time, not quality controlled. The iPhone checks the HTTPS JSON endpoint every <b>60 seconds while the app is open</b>. No paid cloud scheduler or separate backend is required.')
title('Architecture: open data')
base=y-190
box(40,base+111,515,56,['MET EIREANN - EXTERNAL PROVIDER','prodapi.met.ie/observations/dublin/today | hourly source updates'])
box(40,base+28,238,60,['IPHONE - FOREGROUND COLLECTOR','Fetch every minute; parse and timestamp','Deduplicate; commit to SQLite outbox'])
box(321,base+28,234,60,['FIREBASE - BELGIUM CLOUD','Authenticated HTTPS PUT','Private JSON under users/<uid>/weather'])
arrow(158,base+111,158,base+88); arrow(278,base+58,321,base+58)
y=base+5
text('<b>Cloud path:</b> users/&lt;uid&gt;/weather/dublin-airport/observations/&lt;observation-unix-ms&gt;. Each record retains raw fields, temperatureC, rainfallMM, windSpeedKnots, description, source URL and CC BY 4.0 attribution.')
text('<b>Three different timestamps:</b> observedAt is the source measurement time; fetchedAt is phone collection time; uploadedAt is server receipt time. Persistent deduplication and observation-time IDs avoid creating duplicate measurements when the hourly feed is unchanged.')
text('The parser retains missing values as null, converts unambiguous Europe/Dublin local times to UTC, and skips ambiguous/nonexistent daylight-saving hours. The interface marks observations over two hours old as stale. Station data provides Dublin context, not street-level conditions or a forecast.')
title('Combining with my journeys')
text('Journey metadata and weather share <b>station = dublin-airport</b>. Their UTC timestamps enable a join to the latest station observation at or before journey start, with a freshness check. Weather-dependent arrival prediction is reserved for Assignment 3.')
title('Demonstration status')
text('<b>Open-data storage: USER-CONFIRMED, 6 NOVEMBER 2026.</b><br/><b>Automatic collection across a new observation: TEST PENDING.</b><br/>The user confirmed the weather branch exists in Firebase after the upload queue drained. To verify ongoing ingestion, leave the app open across a genuine provider update and record a new observation ID appearing automatically. Rechecking an unchanged snapshot is not a new weather measurement.')
c.showPage()

header(3,'Validation, limitations and submission')
title('Requirement-to-evidence checklist')
rows=[('Task 1: technical diagram (1 mark)','Included on page 1'),('Task 1: own data in cloud (2 marks)','Journeys branch and empty queue: user-confirmed'),('Task 1: real-time uploads (2 marks)','Sample chunks arrive during recording: user-confirmed'),('Task 2: technical diagram (1 mark)','Included on page 2'),('Task 2: open data in cloud (2 marks)','Weather branch: user-confirmed'),('Task 2: live collection (2 marks)','Pending automatic source-update evidence')]
for label,status in rows:
 text(f'<b>{label}</b><br/>{status}',gap=5)
title('Validation completed locally')
text('Xcode build passed. Isolated tests passed for SQLite outbox persistence, stable retry paths, interrupted-session recovery, CSV exports and account/project binding. The actual Swift weather parser passed checks for units, missing readings, sorting, Irish timezone/DST handling and deduplication across relaunch. The user confirmed successful authenticated storage on the physical phone. Live sensor behavior and cross-user rule checks remain pending.')
title('Limits and security')
text('Foreground only: backgrounding ends capture as incomplete. Abrupt termination can leave roughly the last second of GPS/cloud chunks unsaved, while individually persisted raw motion remains local. Interrupted journey recovery uses relaunch time and is excluded from arrival estimates. GPS distance and actual sample rate vary. A local database is bound to one Firebase account/project; histories are not merged across phones.')
text('The API key is entered on the phone, not embedded in source. Passwords are not stored; refresh tokens use Keychain. Per-UID rules protect precise routes. Git ignore rules exclude credentials, local databases and personal exports. Rules were published before the successful upload. Access isolation still requires a separate test.')
title('Submission and references')
text('Submit separately on Blackboard: <b>(1) finalized short report PDF/Word; (2) source ZIP with README run instructions.</b> Complete the pending walking/live-ingestion checks in docs/DEMONSTRATION.md and keep demonstrable cloud data available.')
small=ParagraphStyle('refs',parent=style,fontSize=8,leading=10)
refs='[1] data.gov.ie/dataset/todays-weather-dublin-airport<br/>[2] firebase.google.com/docs/database/rest/save-data<br/>[3] firebase.google.com/docs/reference/rest/auth<br/>[4] firebase.google.com/docs/projects/api-keys<br/><br/>Copyright Met Eireann. Source www.met.ie. CC BY 4.0 (creativecommons.org/licenses/by/4.0/). Met Eireann does not accept liability for errors, omissions, availability or loss arising from use. Modified: numeric parsing and conversion of unambiguous local timestamps to UTC; raw fields retained.'
p=Paragraph(refs,small); _,h=p.wrap(W-80,1000); p.drawOn(c,40,y-h)
if y-h < 42: raise RuntimeError('Report overflow; reduce content or add a page')
c.save()
print(OUT)
