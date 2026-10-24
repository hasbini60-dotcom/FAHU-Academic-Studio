"""Transparent substitution ledger. ASHRAE Chapter 26 is a method reference, not certification."""
from math import isfinite

def build_audit(i,r):
    ms=r['mass_flow']; me=r['exhaust_mass_flow']; w1=r['OA_W']/1000;w3=r['RA_W']/1000
    cs=ms*(1.006+1.86*w1);ce=me*(1.006+1.86*w3);cmin=min(cs,ce)
    qs=r['Q_rec_sensible']; moisture=ms*(r['OA_W']-r['RC_W'])/1000
    tol_s=1e-7;tol_w=1e-8;tol_h=max(.05,.025*max(abs(r['Q_rec']),abs(r['Q_rec']-r['enthalpy_balance_kw'])))
    lines=[]
    def add(title,formula,sub,value,unit,reference,notes=''):
        lines.append(dict(title=title,formula=formula,substitution=sub,value=value,unit=unit,reference=reference,notes=notes))
    add('OA specific volume','v = 287.042*(T+273.15)*(1+1.607858*w)/P',f'287.042*({i["t_oa"]:.3f}+273.15)*(1+1.607858*{w1:.7f})/{r["pressure_pa"]:.1f}',r['supply_specific_volume'],'m3/kg_da','Ideal-gas moist-air approximation; see ASHRAE Handbook Fundamentals, Psychrometrics')
    add('Supply dry-air mass flow','m_s = Vdot_s / v_oa',f'{i["v_oa"]:.2f}/1000 / {r["supply_specific_volume"]:.7f}',ms,'kg_da/s','Psychrometric mass balance')
    add('Exhaust dry-air mass flow','m_e = Vdot_e / v_ra',f'{i["v_exhaust"]:.2f}/1000 / {r["exhaust_specific_volume"]:.7f}',me,'kg_da/s','Psychrometric mass balance')
    add('Minimum heat-capacity rate','C_min = min(m_s*cp_s, m_e*cp_e)',f'min({ms:.6f}*{cs/ms:.6f}, {me:.6f}*{ce/me:.6f})',cmin,'kW/K','ASHRAE Ch.26 Eq. (2a) capacity-rate approach, p.26.2')
    add('Sensible recovery','q_s = eps_s*C_min*(T_oa-T_ra)',f'{r["eps_sensible"]:.5f}*{cmin:.6f}*({i["t_oa"]:.3f}-{i["t_ra"]:.3f})',qs,'kW','ASHRAE Ch.26 Eqs. (2a), (5a), pp.26.2-26.3')
    add('Supply recovery outlet temperature','T_2 = T_1 - q_s/C_s',f'{i["t_oa"]:.4f}-{qs:.6f}/{cs:.6f}',r['RC_DB'],'deg C','ASHRAE Ch.26 Eq. (4a), p.26.3; constant cp approximation')
    add('Exhaust recovery outlet temperature','T_4 = T_3 + q_s/C_e',f'{i["t_ra"]:.4f}+{qs:.6f}/{ce:.6f}',r['EX_DB'],'deg C','Energy conservation; ASHRAE Ch.26 Eq. (4b), p.26.3')
    add('Water vapor transfer','m_w = eps_L*min(m_s,m_e)*(w1-w3)',f'{r["eps_latent"]:.5f}*{min(ms,me):.6f}*({w1:.7f}-{w3:.7f})',moisture,'kg_w/s','ASHRAE Ch.26 Eqs. (2b), (5c), pp.26.2-26.3')
    add('Supply humidity ratio after recovery','w2 = w1 - m_w/m_s',f'{w1:.7f}-({moisture:.9f}/{ms:.6f})',r['RC_W']/1000,'kg_w/kg_da','ASHRAE Ch.26 Eq. (4c), p.26.3')
    add('Exhaust humidity ratio after recovery','w4 = w3 + m_w/m_e',f'{w3:.7f}+({moisture:.9f}/{me:.6f})',r['EX_W']/1000,'kg_w/kg_da','Moisture conservation; ASHRAE Ch.26 Eq. (4d), p.26.3')
    add('Total recovered energy','q_total = m_s*(h1-h2)',f'{ms:.6f}*({r["OA_H"]:.6f}-{r["RC_H"]:.6f})',r['Q_rec'],'kW','ASHRAE Ch.26 Eq. (5d), p.26.3')
    add('Coil target duty (signed)','q_coil = m_s*(h2-h_supply)',f'{ms:.6f}*({r["RC_H"]:.6f}-{r["SUP_H"]:.6f})',r['Q_coil_tot'],'kW','Steady-flow enthalpy balance; not a coil selection')
    if 'pump_power_kw' in r:
        cp=i['loop_cp'];dt=i['loop_dt'];rho=i['loop_rho'];dp=i['loop_dp'];eta=i['pump_eta']/100
        add('Loop fluid mass flow','m_f = abs(q_s)/(cp_f*dT_f)',f'{abs(qs):.6f}/({cp:.4f}*{dt:.4f})',r['loop_mass_kg_s'],'kg/s','Fluid energy balance; NOT an ASHRAE Ch.26 numbered equation')
        add('Pump head','H = dp/(rho*g)',f'{dp*1000:.2f}/({rho:.3f}*9.80665)',r['pump_head_m'],'m','Fluid mechanics; pressure drop is user-entered')
        add('Pump power','P = Vdot_f*dp/eta',f'({r["loop_flow_l_s"]:.6f}/1000)*({dp:.3f}*1000)/({eta:.4f}*1000)',r['pump_power_kw'],'kW','Fluid mechanics; hydraulic estimate, not manufacturer pump selection')
    checks=[('Sensible energy closure',r['sensible_balance_kw'],tol_s,'kW'),('Moisture conservation',r['moisture_balance_kg_s'],tol_w,'kg/s'),('Approximate total enthalpy closure',r['enthalpy_balance_kw'],tol_h,'kW')]
    return {'steps':lines,'checks':[{'name':name,'residual':value,'tolerance':tol,'unit':unit,'status':'PASS' if abs(value)<=tol else 'REVIEW'} for name,value,tol,unit in checks], 'warnings':r['warnings']}

def audit_text(a):
    out=['FAHU ACADEMIC STUDIO v4.1 — EQUATION CALCULATION SHEET', '2020 ASHRAE Handbook—HVAC Systems and Equipment (SI), Chapter 26', 'Preliminary calculation, not ASHRAE certification', '='*76]
    for n,x in enumerate(a['steps'],1):
        out += [f'\n{n:02d}. {x["title"]}',f'    Formula: {x["formula"]}',f'    Inputs:  {x["substitution"]}',f'    Result:  {x["value"]:.8f} {x["unit"]}',f'    Source:  {x["reference"]}']
        if x['notes']:out.append('    Note:    '+x['notes'])
    out += ['\nBALANCE CHECKS', '-'*76]
    for c in a['checks']:out.append(f'{c["status"]:6} | {c["name"]}: residual {c["residual"]:.9g} {c["unit"]}; tolerance +/-{c["tolerance"]:.9g} {c["unit"]}')
    out += ['\nMODEL LIMITATIONS', 'Ideal steady-state recovery; no cross-leakage, condensation/frost or fan motor heat.', 'Effectiveness and loop pressure loss are entered assumptions, not certified selections.', 'Wet-bulb and psychrometric properties use approximate correlations.', 'Balance checks are NOT proof of accuracy or ASHRAE certification.']
    out += ['\nWARNINGS'] + (a['warnings'] or ['None generated.'])
    return '\n'.join(out)

def audit_pdf_flowables(a,styles):
    from reportlab.platypus import Paragraph, Spacer, KeepTogether
    from reportlab.lib.styles import ParagraphStyle
    from xml.sax.saxutils import escape
    h=styles['Heading2'];body=ParagraphStyle('auditbody',parent=styles['BodyText'],fontSize=8.5,leading=12,spaceAfter=3)
    out=[Paragraph('6A. ASHRAE-referenced calculation sheet',h),Paragraph('Calculated substitutions are shown below. Engineering review required; not ASHRAE certification.',body),Spacer(1,10)]
    for j,x in enumerate(a['steps'],1):
        chunk=[Paragraph(f'<b>{j}. {escape(x["title"])}</b>',body)]
        for k in ('formula','substitution'):
            chunk.append(Paragraph(escape(x[k]),body))
        chunk.append(Paragraph(f'<b>Result:</b> {x["value"]:.8f} {escape(x["unit"])}',body))
        chunk.append(Paragraph(f'<b>Reference:</b> {escape(x["reference"])}',body))
        out.append(KeepTogether(chunk));out.append(Spacer(1,7))
    out.append(Paragraph('Balance checks (residual and absolute tolerance)',h))
    for c in a['checks']:
        out.append(Paragraph(escape(f'{c["status"]}: {c["name"]} — {c["residual"]:.8g} {c["unit"]} (limit +/-{c["tolerance"]:.8g})'),body))
    return out
