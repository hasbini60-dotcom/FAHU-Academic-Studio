import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from datetime import datetime
import csv, json, math
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.backends.backend_pdf import PdfPages
from matplotlib.patches import Rectangle, Circle, Polygon
from ashrae_engine import w_from_rh, calculate, RECOVERY_MAP
from calculation_audit import build_audit, audit_text, audit_pdf_flowables

BG='#0c1422'; PANEL='#142337'; INK='#e9f3fa'; MUTED='#a4b9ca'; CYAN='#52d6e8'; ORANGE='#f8ae66'; GREEN='#77dbb6'
FIELDS=[('Outdoor DB °C','t_oa','46'),('Outdoor RH %','rh_oa','20'),('Return DB °C','t_ra','22'),('Return RH %','rh_ra','50'),('Supply DB °C','t_sup','14.2'),('Supply RH %','rh_sup','95'),('Outdoor airflow L/s','v_oa','5600'),('Exhaust airflow L/s','v_exhaust','5600'),('Site pressure Pa','pressure_pa','101325'),('Sensible effectiveness %','eps_s','75'),('Latent effectiveness %','eps_l','55')]
STATES=[('Outdoor','OA'),('After recovery','RC'),('Return','RA'),('Supply','SUP'),('Exhaust','EX')]
class App:
 def __init__(self,root):
  self.root=root;root.title('FAHU Academic Studio v4.1 | Rami Hassbini');root.geometry('1450x900');root.minsize(1120,730);root.configure(bg=BG)
  self.entries={};self.result=None;self.last_input=None
  style=ttk.Style();style.theme_use('clam');style.configure('Treeview',background=PANEL,foreground=INK,fieldbackground=PANEL,rowheight=30,borderwidth=0);style.configure('Treeview.Heading',background='#233c53',foreground='white',font=('Segoe UI',10,'bold'));style.map('Treeview',background=[('selected','#245d78')]);style.configure('TNotebook',background=BG,borderwidth=0);style.configure('TNotebook.Tab',background='#23374b',foreground=INK,padding=(18,9));style.map('TNotebook.Tab',background=[('selected','#346b86')])
  head=tk.Frame(root,bg='#10263b',height=72);head.pack(fill='x');head.pack_propagate(False)
  tk.Label(head,text='◈  FAHU  /  ACADEMIC STUDIO',font=('Segoe UI',20,'bold'),bg='#10263b',fg=INK).pack(side='left',padx=24)
  tk.Label(head,text='HEAT RECOVERY  •  PSYCHROMETRICS  •  COIL DESIGN\nDeveloped by Rami Hassbini',font=('Segoe UI',10),justify='right',bg='#10263b',fg=CYAN).pack(side='right',padx=26)
  body=tk.Frame(root,bg=BG);body.pack(fill='both',expand=True,padx=14,pady=12)
  left=tk.Frame(body,bg=PANEL,width=310);left.pack(side='left',fill='y',padx=(0,12));left.pack_propagate(False)
  tk.Label(left,text='DESIGN CONDITIONS',bg=PANEL,fg=INK,font=('Segoe UI',13,'bold')).pack(anchor='w',padx=18,pady=(17,12))
  for i,(label,key,default) in enumerate(FIELDS):
   row=tk.Frame(left,bg=PANEL);row.pack(fill='x',padx=16,pady=5)
   tk.Label(row,text=label,bg=PANEL,fg=MUTED,font=('Segoe UI',9),anchor='w',width=23).pack(side='left')
   e=tk.Entry(row,bg='#20344a',fg=INK,insertbackground=INK,relief='flat',font=('Segoe UI',10),width=9,justify='center');e.insert(0,default);e.pack(side='right',ipady=5);self.entries[key]=e
  tk.Label(left,text='RECOVERY CONFIGURATION',bg=PANEL,fg=INK,font=('Segoe UI',10,'bold')).pack(anchor='w',padx=18,pady=(15,5))
  self.recovery=tk.StringVar(value='Thermal Wheel (total)');ttk.Combobox(left,textvariable=self.recovery,values=list(RECOVERY_MAP),state='readonly',width=31).pack(padx=16,pady=5)
  self.button(left,'◉  CALCULATE DESIGN',self.run,CYAN,'#07202a');self.button(left,'⇩  EXPORT ENGINEERING CSV',self.export_csv,'#244d67',INK);self.button(left,'▤  EXPORT PDF REPORT',self.export_pdf,'#244d67',INK);self.button(left,'↗  SAVE INPUT CASE (JSON)',self.save_case,'#244d67',INK);self.button(left,'↙  LOAD INPUT CASE',self.load_case,'#244d67',INK)
  tk.Label(left,text='Preliminary design only. Verify manufacturer\nperformance and project design criteria.',bg=PANEL,fg=MUTED,font=('Segoe UI',8),justify='left').pack(anchor='w',padx=17,pady=15)
  self.tabs=ttk.Notebook(body);self.tabs.pack(side='left',fill='both',expand=True)
  self.schem_tab=tk.Frame(self.tabs,bg=BG);self.table_tab=tk.Frame(self.tabs,bg=BG);self.notes_tab=tk.Frame(self.tabs,bg=BG)
  self.tabs.add(self.schem_tab,text='  SYSTEM SCHEMATIC  ');self.tabs.add(self.table_tab,text='  AIR STATES & LOADS  ');self.tabs.add(self.notes_tab,text='  ENGINEERING NOTES  ')
  self.chart_tab=tk.Frame(self.tabs,bg=BG);self.equipment_tab=tk.Frame(self.tabs,bg=BG)
  self.tabs.add(self.chart_tab,text='  PSYCHROMETRIC CHART  ');self.tabs.add(self.equipment_tab,text='  EQUIPMENT CUTAWAY  ')
  self.chart_fig=Figure(figsize=(9,6),dpi=100,facecolor='#ffffff');self.chart_canvas=FigureCanvasTkAgg(self.chart_fig,master=self.chart_tab);self.chart_canvas.get_tk_widget().pack(fill='both',expand=True)
  self.equip_fig=Figure(figsize=(9,6),dpi=100,facecolor='#ffffff');self.equip_canvas=FigureCanvasTkAgg(self.equip_fig,master=self.equipment_tab);self.equip_canvas.get_tk_widget().pack(fill='both',expand=True)
  self.pump_fields={};pump_box=tk.LabelFrame(self.notes_tab,text='RUN-AROUND PUMP INPUTS (water/glycol loop)',bg=PANEL,fg=CYAN)
  pump_box.pack(fill='x',padx=18,pady=8)
  for name,key,default in [('Loop delta T (K)','loop_dt','5'),('Fluid cp (kJ/kg K)','loop_cp','3.8'),('Fluid density (kg/m3)','loop_rho','1030'),('Loop pressure loss (kPa)','loop_dp','80'),('Pump efficiency (%)','pump_eta','55')]:
   row=tk.Frame(pump_box,bg=PANEL);row.pack(fill='x',padx=8,pady=2);tk.Label(row,text=name,bg=PANEL,fg=INK,width=31,anchor='w').pack(side='left');e=tk.Entry(row,width=12);e.insert(0,default);e.pack(side='left');self.pump_fields[key]=e
  self.canvas=tk.Canvas(self.schem_tab,bg='#101e30',highlightthickness=0);self.canvas.pack(fill='both',expand=True,padx=4,pady=4);self.canvas.bind('<Configure>',lambda e:self.draw())
  columns=('State','DB °C','WB °C','RH %','w g/kg','h kJ/kg');self.tree=ttk.Treeview(self.table_tab,columns=columns,show='headings',height=8)
  for c in columns:self.tree.heading(c,text=c);self.tree.column(c,width=140,anchor='center')
  self.tree.pack(fill='x',padx=18,pady=(24,14));self.summary=tk.Text(self.table_tab,bg=PANEL,fg=INK,insertbackground=INK,relief='flat',font=('Consolas',11),height=19,padx=18,pady=16);self.summary.pack(fill='both',expand=True,padx=18,pady=(0,18))
  self.notes=tk.Text(self.notes_tab,bg=PANEL,fg=INK,relief='flat',font=('Consolas',11),wrap='word',padx=20,pady=20);self.notes.pack(fill='both',expand=True,padx=18,pady=18)
  self.validation_tab=tk.Frame(self.tabs,bg=BG);self.tabs.add(self.validation_tab,text='  ASHRAE VALIDATION  ');self.validation=tk.Text(self.validation_tab,bg=PANEL,fg=INK,relief='flat',font=('Consolas',11),wrap='word',padx=20,pady=20);self.validation.pack(fill='both',expand=True,padx=18,pady=18)
  self.audit_tab=tk.Frame(self.tabs,bg=BG);self.tabs.add(self.audit_tab,text='  EQUATION CALCULATION SHEET  ')
  self.audit_view=tk.Text(self.audit_tab,bg=PANEL,fg=INK,relief='flat',font=('Consolas',10),wrap='word',padx=20,pady=20)
  self.audit_view.pack(fill='both',expand=True,padx=18,pady=18)
  self.run()
 def button(self,parent,label,command,bg,fg):tk.Button(parent,text=label,command=command,bg=bg,fg=fg,activebackground=CYAN,relief='flat',cursor='hand2',font=('Segoe UI',10,'bold'),pady=10).pack(fill='x',padx=16,pady=5)
 def read(self):
  inp={k:float(self.entries[k].get()) for _,k,_ in FIELDS}
  for k in ('rh_oa','rh_ra','rh_sup','eps_s','eps_l'):inp[k]/=100
  for k in ('rh_oa','rh_ra','rh_sup'):
   if not 0<=inp[k]<=1:raise ValueError(f'{k}: relative humidity must be >0 and <=100%.')
  for k in ('eps_s','eps_l'):
   if not 0<=inp[k]<=1:raise ValueError(f'{k}: effectiveness must be 0–100%.')
  if inp['v_oa']<=0 or inp['v_exhaust']<=0:raise ValueError('Both airflows must be positive.')
  if not all(-40<=inp[k]<=80 for k in ('t_oa','t_ra','t_sup')):raise ValueError('Temperatures must be between -40 and 80 °C.')
  inp['recovery']=self.recovery.get()
  for key,entry in self.pump_fields.items():
   val=float(entry.get())
   if not math.isfinite(val) or val<=0:raise ValueError(key+' must be positive')
   inp[key]=val
  if inp['pump_eta']>100:raise ValueError('Pump efficiency must be <=100%')
  return inp
 def run(self):
  try:
   inp=self.read();r=calculate(inp)
   if not all(math.isfinite(v) for v in r.values() if isinstance(v,(int,float))):raise ValueError('Nonfinite calculation result.')
  except (ValueError,OverflowError,ZeroDivisionError) as e:messagebox.showerror('Input / calculation error',str(e));return
  self.last_input=inp;self.result=r
  for i in self.tree.get_children():self.tree.delete(i)
  for label,pre in STATES:self.tree.insert('', 'end',values=(label,*(f'{r[pre+"_"+s]:.2f}' for s in ('DB','WB','RH','W','H'))))
  q=r['Q_coil_tot']; mode='Cooling / dehumidification' if q>=0 else 'Heating / humidification (signed duty)'
  txt=f'''AIRFLOW AND CAPACITY SUMMARY\n{'─'*63}\nOutdoor airflow                 {inp['v_oa']:>12,.1f} L/s\nCalculated dry-air mass flow   {r['mass_flow']:>12.3f} kg/s\nHeat-recovery type              {r['recovery_type']}\nRecovered enthalpy duty         {r['Q_rec']:>12.2f} kW\nCoil total signed duty          {q:>12.2f} kW\nCoil sensible duty              {r['Q_coil_sen']:>12.2f} kW\nCoil latent residual            {r['Q_coil_lat']:>12.2f} kW\nCoil mode                       {mode}\nIndicative water flow (ΔT=5 K) {r['CW_flow']:>12.2f} L/s\n\nNote: positive coil duty indicates cooling in the original model.\nNegative duty indicates heating; water flow is an indicative\nmagnitude only, not a validated heating/humidification design.'''
  if 'pump_power_kw' in r:
   txt+=f"\n\nRUN-AROUND LOOP / PUMP (preliminary)\nHeat transfer: {r['loop_duty_kw']:.2f} kW\nFluid mass flow: {r['loop_mass_kg_s']:.3f} kg/s\nFluid volume flow: {r['loop_flow_l_s']:.3f} L/s\nPump head: {r['pump_head_m']:.2f} m\nPump shaft/input estimate: {r['pump_power_kw']:.3f} kW\nPressure loss is user-assumed, NOT hydraulically calculated."
  self.summary.delete('1.0','end');self.summary.insert('1.0',txt)
  notes=f"""ASHRAE REFERENCE AND MODEL SCOPE

2020 ASHRAE Handbook—HVAC Systems and Equipment (SI), Chapter 26:
• Eq. (2a), p.26.2: gross sensible effectiveness.
• Eq. (2b), p.26.2: gross latent effectiveness.
• Eqs. (5a)-(5d), p.26.3: energy and moisture transfer.
• Eqs. (8)-(9), p.26.4: fan-power framework (not yet calculated).

Dry-air mass flow is calculated from moist-air specific volume
at user-selected site pressure (ideal gas approximation).
Unequal supply/exhaust flows are handled using minimum heat
capacity rate and minimum dry-air mass flow. Both outlets are
computed from sensible energy and moisture balances.

LIMITATIONS
• Entered effectiveness must come from rated or measured data.
• No cross-leakage, condensation/frost, motor heat, wheel carryover,
  or fan pressure losses; supersaturated recovery exits are rejected.
• Wet-bulb values are approximate enthalpy-matching estimates.
• Specified supply state is a target, not an equipment coil selection.
• Pump loss is a USER INPUT, not a piping-network computation.
• Heat transfer model is preliminary, not ASHRAE certified.

WARNINGS
""" + ('\n'.join('• '+w for w in r['warnings']) if r['warnings'] else 'No automatic warnings.')
  self.notes.delete('1.0','end');self.notes.insert('1.0',notes);self.validation.delete('1.0','end')
  vtxt=(f"ASHRAE CHAPTER 26  |  EQUATION AUDIT\n{'='*65}\n"
        f"Supply dry-air flow: {r['mass_flow']:.5f} kg_da/s\n"
        f"Exhaust dry-air flow: {r['exhaust_mass_flow']:.5f} kg_da/s\n"
        f"OA specific volume: {r['supply_specific_volume']:.5f} m³/kg_da\n"
        f"RA specific volume: {r['exhaust_specific_volume']:.5f} m³/kg_da\n\n"
        f"Eq. 2a/5a: sensible transfer = {r['Q_rec_sensible']:.4f} kW\n"
        f"Eq. 2b: latent effectiveness = {r['eps_latent']*100:.1f}%\n"
        f"Eq. 5d: supply enthalpy recovery = {r['Q_rec']:.4f} kW\n"
        f"Sensible balance residual = {r['sensible_balance_kw']:.8f} kW\n"
        f"Moisture balance residual = {r['moisture_balance_kg_s']:.10f} kg/s\n"
        f"Enthalpy balance discrepancy = {r['enthalpy_balance_kw']:.4f} kW\n\n"
        f"VALIDATION STATUS\n"
        f"{'PASS' if abs(r['sensible_balance_kw'])<1e-8 else 'FAIL'} — sensible transfer conservation\n"
        f"{'PASS' if abs(r['moisture_balance_kg_s'])<1e-9 else 'FAIL'} — moisture conservation\n"
        f"{'PASS' if abs(r['enthalpy_balance_kw'])<max(.05,.025*max(abs(r['Q_rec']),abs(r['Q_rec']-r['enthalpy_balance_kw']))) else 'REVIEW'} — approximate enthalpy closure (2.5% tolerance)\n\n"
        "AUTOMATED REFERENCE TESTS: run VALIDATE_ENGINE.bat\n"
        "This is implementation verification, NOT ASHRAE certification.\n")
  self.validation.insert('1.0',vtxt)
  self.audit_view.delete('1.0','end');self.audit_view.insert('1.0',audit_text(build_audit(inp,r)))
  self.draw();self.draw_chart();self.draw_equipment()
 def draw(self):
  c=self.canvas;c.delete('all');w=max(c.winfo_width(),700);h=max(c.winfo_height(),500);sx=w/950;sy=h/680
  def rect(x1,y1,x2,y2,fill,outline='#4b7791',width=2):c.create_rectangle(x1*sx,y1*sy,x2*sx,y2*sy,fill=fill,outline=outline,width=width)
  def line(*pts,color=CYAN,width=4,arrow=None):c.create_line(*[v*(sx if i%2==0 else sy) for i,v in enumerate(pts)],fill=color,width=width,arrow=arrow,smooth=False)
  def label(x,y,t,color=INK,size=11,bold=False):c.create_text(x*sx,y*sy,text=t,fill=color,font=('Segoe UI',size,'bold' if bold else 'normal'),justify='center')
  label(475,40,'FRESH AIR HANDLING UNIT  •  HEAT RECOVERY PROCESS',size=17,bold=True)
  rect(65,150,890,500,'#1b3045');rect(92,210,850,300,'#25425a');rect(92,355,850,445,'#25425a')
  line(100,255,835,255,color=CYAN,width=5,arrow='last');line(830,400,105,400,color=ORANGE,width=5,arrow='last')
  # Recovery component switches according to selection
  if self.recovery.get()=='Plate HX (sensible)':
   rect(320,210,455,445,'#23435c',outline=CYAN,width=4)
   for offset in range(0,110,13):line(326+offset,215,450-offset,440,color='#88cfe2',width=3)
  elif self.recovery.get()=='Run-Around Coil (sensible)':
   rect(335,210,435,300,'#23435c',outline=CYAN,width=4);rect(335,355,435,445,'#23435c',outline=ORANGE,width=4)
   for x in range(344,432,13):line(x,215,x,295,color=CYAN,width=2);line(x,360,x,440,color=ORANGE,width=2)
   line(435,255,485,255,485,400,435,400,color=GREEN,width=4)
   line(335,400,290,400,290,255,335,255,color=GREEN,width=4)
   c.create_oval(462*sx,315*sy,508*sx,360*sy,outline=GREEN,width=4)
   label(485,338,'P',GREEN,13,True)
  else:
   c.create_oval(320*sx,190*sy,455*sx,470*sy,fill='#233d55',outline=CYAN,width=5)
  if self.recovery.get()=='Thermal Wheel (total)':
   for a in range(0,360,30):
    x=387+60*math.cos(math.radians(a));y=330+130*math.sin(math.radians(a));line(387,330,x,y,color='#6096b4',width=2)
   c.create_oval(377*sx,320*sy,397*sx,340*sy,fill=CYAN,outline='')
  rect(515,205,590,305,'#356781',outline=CYAN)
  for x in range(526,586,12):line(x,210,x,300,color='#7ce3ec',width=2)
  rect(675,205,750,305,'#34586b',outline=CYAN)
  c.create_oval(686*sx,218*sy,739*sx,291*sy,outline=CYAN,width=3)
  for x1,y1,x2,y2 in [(712,254,711,224),(712,254,737,264),(712,254,692,274)]:line(x1,y1,x2,y2,color=CYAN,width=3)
  rect(160,350,225,450,'#6b493b',outline=ORANGE)
  c.create_oval(171*sx,365*sy,214*sx,433*sy,outline=ORANGE,width=3)
  for x1,y1,x2,y2 in [(192,400,192,372),(192,400,213,415),(192,400,172,414)]:line(x1,y1,x2,y2,color=ORANGE,width=3)
  label(387,495,{'Thermal Wheel (total)':'ROTARY RECOVERY WHEEL','Plate HX (sensible)':'CROSS-FLOW PLATE EXCHANGER','Run-Around Coil (sensible)':'RUN-AROUND COILS + PUMP'}[self.recovery.get()],CYAN,11,True);label(550,330,'COOLING / HEATING COIL',CYAN,10,True);label(712,330,'SUPPLY FAN',CYAN,10,True);label(192,475,'EXHAUST FAN',ORANGE,10,True)
  label(150,185,'OUTDOOR AIR',CYAN,12,True);label(795,185,'SUPPLY AIR',CYAN,12,True);label(785,470,'RETURN AIR',ORANGE,12,True);label(135,470,'EXHAUST AIR',ORANGE,12,True)
  if self.result:
   r=self.result
   for x,y,p in [(155,318,'OA'),(474,318,'RC'),(802,318,'SUP'),(780,375,'RA'),(100,375,'EX')]:
    label(x,y,f'{r[p+"_DB"]:.1f} °C  |  {r[p+"_RH"]:.0f}% RH',GREEN,10,True)
   label(475,565,f'Recovered: {r["Q_rec"]:.1f} kW     •     Coil: {r["Q_coil_tot"]:.1f} kW     •     Airflow: {self.last_input["v_oa"]:,.0f} L/s',INK,13,True)
   label(475,605,f'After recovery: w = {r["RC_W"]:.2f} g/kg  |  h = {r["RC_H"]:.2f} kJ/kg',MUTED,11)
  label(475,646,'Schematic is conceptual and not to scale. Components and airflow arrangement require project verification.',MUTED,9)

 def draw_chart(self):
  f=self.chart_fig;f.clear();ax=f.add_subplot(111);ax.set_facecolor('#f8fbff')
  temps=[t/2 for t in range(-40,141)]
  for rh in (0.1,0.2,0.3,0.4,0.5,0.6,0.7,0.8,0.9,1.0):
   ys=[]
   for t in temps:
    try:ys.append(w_from_rh(t,rh,self.result['pressure_pa'] if self.result else 101325)*1000)
    except (OverflowError,ZeroDivisionError):ys.append(float('nan'))
   ax.plot(temps,ys,color='#a9c3d4' if rh<1 else '#3977aa',lw=0.8 if rh<1 else 1.8)
   ax.text(39,w_from_rh(39,rh,self.result['pressure_pa'] if self.result else 101325)*1000,f'{rh*100:.0f}%',fontsize=7,color='#5d788d')
  if self.result:
   r=self.result;colors={'OA':'#e17834','RC':'#299b77','RA':'#b05ebc','SUP':'#2978d1','EX':'#c44554'}
   for name,p in STATES:
    x=r[p+'_DB'];y=r[p+'_W'];ax.scatter(x,y,color=colors[p],s=80,zorder=5,label=f'{p} — {name}');ax.annotate(p,(x,y),xytext=(5,6),textcoords='offset points',fontsize=10,weight='bold')
   for a,b in [('OA','RC'),('RC','SUP'),('RA','EX')]:ax.plot([r[a+'_DB'],r[b+'_DB']],[r[a+'_W'],r[b+'_W']],ls='--',color='#586b7b',lw=1.6)
  ax.set_xlim(-10,55);ax.set_ylim(0,35);ax.set_xlabel('Dry-bulb temperature (°C)');ax.set_ylabel('Humidity ratio (g/kg dry air)');ax.set_title(f"Psychrometric states at {self.result['pressure_pa']/1000:.3f} kPa" if self.result else 'Psychrometric states');ax.grid(alpha=.2);ax.legend(loc='upper left',fontsize=8);f.tight_layout();self.chart_canvas.draw_idle()
 def draw_equipment(self):
  f=self.equip_fig;f.clear();ax=f.add_subplot(111);ax.set_xlim(0,12);ax.set_ylim(0,7);ax.axis('off');ax.set_facecolor('#f7fafc')
  ax.add_patch(Rectangle((.7,1.2),10.6,4.6,facecolor='#dbe7ed',edgecolor='#455d6c',linewidth=3))
  ax.add_patch(Rectangle((.9,3.7),10.2,1.7,facecolor='#e8f5fc',edgecolor='#6d8da0'))
  ax.add_patch(Rectangle((.9,1.5),10.2,1.7,facecolor='#fff0e4',edgecolor='#6d8da0'))
  typ=self.recovery.get()
  if typ=='Thermal Wheel (total)':
   ax.add_patch(Circle((4,3.45),1.6,facecolor='#b3c8d3',edgecolor='#267ca2',linewidth=4))
   for i in range(12):
    a=i*math.pi/6;ax.plot([4,4+1.52*math.cos(a)],[3.45,3.45+1.52*math.sin(a)],color='#47798e',lw=2)
   desc='Rotating enthalpy wheel: sensible + latent transfer'
  elif typ=='Plate HX (sensible)':
   ax.add_patch(Rectangle((2.8,2.1),2.4,2.7,facecolor='#9bbbc9',edgecolor='#267ca2',linewidth=3))
   for i in range(12):ax.plot([2.85+i*.19,3.1+i*.19],[2.15,4.75],color='#356c84',lw=1.5)
   desc='Plate heat exchanger: sensible heat transfer, no moisture transfer'
  else:
   for y in (2.05,4.1):
    ax.add_patch(Rectangle((3,y),1.4,.9,facecolor='#8ebac8',edgecolor='#267ca2',linewidth=3))
    for i in range(7):ax.plot([3.1+i*.19]*2,[y+.1,y+.8],color='#256781',lw=2)
   ax.plot([4.4,5.6,5.6,4.4],[4.55,4.55,2.5,2.5],color='#2a947e',lw=4)
   ax.add_patch(Circle((5.6,3.45),.27,facecolor='#8fd1bb',edgecolor='#1d6959',linewidth=3))
   ax.text(5.6,3.45,'P',ha='center',va='center',weight='bold')
   desc='Two hydronic recovery coils with closed fluid loop and circulation pump'
  for x in (7.0,8.7):
   ax.add_patch(Rectangle((x,3.85),.6,1.3,facecolor='#9bbcc9',edgecolor='#396c82'))
   for i in range(5):ax.plot([x+.08+i*.1]*2,[3.9,5.1],color='#2a718e',lw=1)
  ax.add_patch(Circle((10,4.55),.52,facecolor='#7da2b4',edgecolor='#34627c',linewidth=3))
  for i in range(3):
   a=i*2*math.pi/3;ax.plot([10,10+.4*math.cos(a)],[4.55,4.55+.4*math.sin(a)],lw=4,color='#e8f5fc')
  ax.annotate('',xy=(11,4.55),xytext=(.95,4.55),arrowprops={'arrowstyle':'->','lw':2,'color':'#1684b5'})
  ax.annotate('',xy=(1,2.35),xytext=(11,2.35),arrowprops={'arrowstyle':'->','lw':2,'color':'#dd793e'})
  ax.text(6,6.4,typ,ha='center',fontsize=17,weight='bold',color='#233e51');ax.text(6,.6,desc,ha='center',fontsize=11,color='#344f5e')
  ax.text(8.1,5.45,'Coil',ha='center',fontsize=10);ax.text(10,5.45,'Supply fan',ha='center',fontsize=10)
  f.tight_layout();self.equip_canvas.draw_idle()
 def export_pdf(self):
  if not self.result:return
  path=filedialog.asksaveasfilename(defaultextension='.pdf',filetypes=[('PDF report','*.pdf')],initialfile='FAHU_Academic_V4_1_Report.pdf')
  if not path:return
  try:
   from reportlab.platypus import SimpleDocTemplate,Paragraph,Spacer,Table,TableStyle,Image,PageBreak,KeepTogether
   from reportlab.lib import colors
   from reportlab.lib.styles import getSampleStyleSheet
   from reportlab.lib.units import inch
   import io
   styles=getSampleStyleSheet();story=[];r=self.result;inp=self.last_input
   story += [Paragraph('FAHU ACADEMIC ENGINEERING DESIGN REPORT',styles['Title']),Paragraph('Developed by Rami Hassbini | '+datetime.now().strftime('%Y-%m-%d %H:%M'),styles['Normal']),Spacer(1,14)]
   story.append(Paragraph('1. Design inputs',styles['Heading2']))
   data=[['Parameter','Value']]+[[k,str(v)] for k,v in inp.items()]
   def add_table(data):
    t=Table(data,repeatRows=1,hAlign='LEFT',colWidths=[3.4*inch,2.7*inch]);t.setStyle(TableStyle([('BACKGROUND',(0,0),(-1,0),colors.HexColor('#173e59')),('TEXTCOLOR',(0,0),(-1,0),colors.white),('GRID',(0,0),(-1,-1),.35,colors.lightgrey),('ROWBACKGROUNDS',(0,1),(-1,-1),[colors.white,colors.HexColor('#f0f5f8')]),('FONTSIZE',(0,0),(-1,-1),8),('BOTTOMPADDING',(0,0),(-1,-1),6)]));return t
   story.append(add_table(data));story.append(Spacer(1,14));story.append(Paragraph('2. Calculated air states',styles['Heading2']))
   data=[['State','DB C','WB C','RH %','w g/kg','h kJ/kg']]+[[name]+[f'{r[p+"_"+k]:.2f}' for k in ('DB','WB','RH','W','H')] for name,p in STATES]
   t=Table(data,repeatRows=1);t.setStyle(TableStyle([('BACKGROUND',(0,0),(-1,0),colors.HexColor('#173e59')),('TEXTCOLOR',(0,0),(-1,0),colors.white),('GRID',(0,0),(-1,-1),.4,colors.lightgrey),('FONTSIZE',(0,0),(-1,-1),8)]));story.append(t)
   story.append(Spacer(1,12));story.append(Paragraph('3. Capacity and hydraulic estimates',styles['Heading2']))
   vals=[('Recovered duty (kW)','Q_rec'),('Coil total signed duty (kW)','Q_coil_tot'),('Coil sensible duty (kW)','Q_coil_sen'),('Coil latent residual (kW)','Q_coil_lat'),('Indicative coil water flow (L/s)','CW_flow')]
   if 'pump_power_kw' in r:vals += [('Run-around heat duty (kW)','loop_duty_kw'),('Loop mass flow (kg/s)','loop_mass_kg_s'),('Loop volume flow (L/s)','loop_flow_l_s'),('Pump head (m)','pump_head_m'),('Pump power estimate (kW)','pump_power_kw')]
   story.append(add_table([['Metric','Value']]+[[name,f'{r[key]:.3f}'] for name,key in vals]));story.append(PageBreak())
   for heading,fig in [('4. Equipment configuration',self.equip_fig),('5. Psychrometric chart',self.chart_fig)]:
    story.append(Paragraph(heading,styles['Heading2']));b=io.BytesIO();fig.savefig(b,format='png',dpi=130,bbox_inches='tight');b.seek(0);story.append(Image(b,width=6.8*inch,height=4.3*inch));story.append(Spacer(1,12))
   story.append(Paragraph('6. Model equations and limitations',styles['Heading2']))
   for line in ['h = 1.006 T + w (2501 + 1.86 T) [kJ/kg dry air]','Q recovery = m dry air x (h outdoor - h after recovery)','Q coil = m dry air x (h after recovery - h supply)','Run-around: m fluid = abs(Q sensible) / (cp fluid x delta T loop)','Pump head = delta p / (rho fluid x g)','Pump power = volume flow x delta p / pump efficiency','Dry-air mass flow is derived from moist-air specific volume at user pressure.','Effectiveness and hydronic properties are user inputs; pump loss is not calculated from piping.','Illustrations are technical concepts, not equipment manufacturing drawings.','2020 ASHRAE Handbook HVAC Systems and Equipment (SI), Ch.26, Eqs. 2a, 2b, 5a-5d; this is not ASHRAE certification.']:
    story.append(Paragraph(line,styles['BodyText']));story.append(Spacer(1,5))
   story.append(PageBreak())
   story.extend(audit_pdf_flowables(build_audit(inp,r),styles))
   story.append(Paragraph('7. Automated balance checks and warnings',styles['Heading2']))
   for line in [f"Sensible energy balance residual: {r['sensible_balance_kw']:.8f} kW",f"Moisture balance residual: {r['moisture_balance_kg_s']:.10f} kg/s",f"Enthalpy closure discrepancy: {r['enthalpy_balance_kw']:.4f} kW"]+r['warnings']:
    story.append(Paragraph(line,styles['BodyText']));story.append(Spacer(1,5))
   SimpleDocTemplate(path,pagesize=(595,842),leftMargin=42,rightMargin=42,topMargin=40,bottomMargin=40).build(story)
   messagebox.showinfo('PDF created',path)
  except Exception as exc:messagebox.showerror('PDF export error',str(exc))

 def export_csv(self):
  if not self.result:return
  path=filedialog.asksaveasfilename(defaultextension='.csv',filetypes=[('CSV','*.csv')],initialfile='FAHU_Engineering_Results.csv')
  if not path:return
  r=self.result
  with open(path,'w',newline='',encoding='utf-8-sig') as f:
   writer=csv.writer(f);writer.writerow(['FAHU Academic Studio v4.1 — Rami Hassbini']);writer.writerow(['Date',datetime.now().isoformat(timespec='minutes')]);writer.writerow(['State','DB °C','WB °C','RH %','Humidity g/kg','Enthalpy kJ/kg'])
   for name,p in STATES:writer.writerow([name,*[round(r[p+'_'+s],3) for s in ('DB','WB','RH','W','H')]])
   writer.writerow([])
   for k in ('recovery_type','mass_flow','Q_rec','Q_coil_tot','Q_coil_sen','Q_coil_lat','CW_flow','loop_duty_kw','loop_flow_l_s','pump_head_m','pump_power_kw'):
    if k in r:writer.writerow([k,r[k]])
  messagebox.showinfo('Exported',path)
 def export_txt(self):
  if not self.result:return
  path=filedialog.asksaveasfilename(defaultextension='.txt',filetypes=[('Text report','*.txt')],initialfile='FAHU_Academic_Report.txt')
  if not path:return
  with open(path,'w',encoding='utf-8') as f:
   f.write('FAHU ACADEMIC ENGINEERING REPORT\nDeveloped by Rami Hassbini\n'+datetime.now().isoformat(timespec='minutes')+'\n\nINPUTS\n')
   for k,v in self.last_input.items():f.write(f'{k}: {v}\n')
   f.write('\nAIR STATES\n')
   for name,p in STATES:f.write(f'{name}: '+', '.join(f'{s}={self.result[p+"_"+s]:.3f}' for s in ('DB','WB','RH','W','H'))+'\n')
   f.write('\n'+self.summary.get('1.0','end')+'\n'+self.notes.get('1.0','end'))
  messagebox.showinfo('Report exported',path)
 def save_case(self):
  try:inp=self.read()
  except ValueError as e:messagebox.showerror('Invalid inputs',str(e));return
  path=filedialog.asksaveasfilename(defaultextension='.json',filetypes=[('JSON','*.json')],initialfile='FAHU_Case.json')
  if path:
   with open(path,'w',encoding='utf-8') as f:json.dump(inp,f,indent=2)
 def load_case(self):
  path=filedialog.askopenfilename(filetypes=[('JSON','*.json')]);
  if not path:return
  try:
   with open(path,encoding='utf-8') as f:inp=json.load(f)
   for _,k,_ in FIELDS:
    val=inp[k]*100 if k in ('rh_oa','rh_ra','rh_sup','eps_s','eps_l') else inp[k]
    self.entries[k].delete(0,'end');self.entries[k].insert(0,str(val))
   self.recovery.set(inp['recovery'])
   for k,e in self.pump_fields.items():
    if k in inp:e.delete(0,'end');e.insert(0,str(inp[k]))
   self.run()
  except (OSError,KeyError,ValueError,TypeError) as e:messagebox.showerror('Cannot load case',str(e))
if __name__=='__main__':
 root=tk.Tk();App(root);root.mainloop()
