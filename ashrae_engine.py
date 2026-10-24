"""FAHU Academic v4: transparent preliminary ASHRAE Ch.26 effectiveness model.

Reference: 2020 ASHRAE Handbook HVAC Systems and Equipment, SI, Ch.26,
pp. 26.2-26.4, Eqs. (1)-(5), (8)-(9). This software is NOT ASHRAE certified.
Simplifications: steady state, no leakage/frost/condensation in recovery device,
user-entered effectiveness; coil target is a specified state, not coil sizing.
"""
from dataclasses import dataclass
import math

P_ATM = 101325.0
RECOVERY_MAP = {"Thermal Wheel (total)": "wheel", "Plate HX (sensible)": "plate", "Run-Around Coil (sensible)": "runaround"}


def p_ws(t):
    if t >= 0:
        return 611.21 * math.exp((18.678-t/234.5)*(t/(257.14+t)))
    return 611.15 * math.exp((23.036-t/333.7)*(t/(279.82+t)))


def w_from_rh(t, rh, pressure=P_ATM):
    if not 0 <= rh <= 1: raise ValueError('Relative humidity must be 0–100%.')
    pw = rh*p_ws(t)
    if pw >= pressure: raise ValueError('Vapor pressure exceeds atmospheric pressure.')
    return 0.621945*pw/(pressure-pw)


def rh_from_w(t, w, pressure=P_ATM):
    return (pressure*w/(0.621945+w))/p_ws(t)


def enthalpy(t,w):
    return 1.006*t+w*(2501+1.86*t)


def specific_volume(t,w,pressure=P_ATM):
    # m3/kg dry air; ideal-gas moist-air relation
    return 287.042*(t+273.15)*(1+1.607858*w)/pressure


def wetbulb(t,w,pressure=P_ATM):
    # Approximate thermodynamic wet-bulb by saturated enthalpy matching.
    # Displayed as approximate; not an exact adiabatic saturation solution.
    target=enthalpy(t,w); lo=-70.0;hi=t
    for _ in range(85):
        mid=(lo+hi)/2
        if enthalpy(mid,w_from_rh(mid,1,pressure)) < target:lo=mid
        else:hi=mid
    return (lo+hi)/2


def state(t,w,pressure=P_ATM):
    rh=rh_from_w(t,w,pressure)
    if rh > 1.000001: raise ValueError(f'Recovery outlet supersaturated ({rh*100:.1f}% RH). Condensation model required; calculation stopped.')
    return {'DB':t,'RH':rh*100,'W':w*1000,'H':enthalpy(t,w),'WB':wetbulb(t,w,pressure),'V':specific_volume(t,w,pressure)}


def calculate(inp):
    for k in ('t_oa','rh_oa','t_ra','rh_ra','t_sup','rh_sup','v_oa','eps_s','eps_l'):
        if k not in inp or not math.isfinite(float(inp[k])): raise ValueError(f'Invalid input: {k}')
    p=float(inp.get('pressure_pa',P_ATM))
    if not 50000 <= p <= 110000:raise ValueError('Atmospheric pressure must be 50–110 kPa.')
    v_s=inp['v_oa']/1000
    v_e=inp.get('v_exhaust',inp['v_oa'])/1000
    if min(v_s,v_e)<=0:raise ValueError('Both airflows must be positive.')
    for key in ('rh_oa','rh_ra','rh_sup','eps_s','eps_l'):
        if not 0 <= inp[key] <= 1:raise ValueError(f'{key} must be between 0 and 1.')
    if inp['recovery'] not in RECOVERY_MAP:raise ValueError('Unknown recovery device.')
    w1=w_from_rh(inp['t_oa'],inp['rh_oa'],p); w3=w_from_rh(inp['t_ra'],inp['rh_ra'],p)
    ws=w_from_rh(inp['t_sup'],inp['rh_sup'],p)
    m_s=v_s/specific_volume(inp['t_oa'],w1,p)
    m_e=v_e/specific_volume(inp['t_ra'],w3,p)
    cp_s=1.006+1.86*w1;cp_e=1.006+1.86*w3
    C_s=m_s*cp_s;C_e=m_e*cp_e;C_min=min(C_s,C_e)
    eps_s=inp['eps_s'];eps_l=inp['eps_l'] if RECOVERY_MAP[inp['recovery']]=='wheel' else 0.0
    # ASHRAE Ch.26 Eq. (2a)/(5a): capacity-rate-limited sensible transfer.
    q_s=eps_s*C_min*(inp['t_oa']-inp['t_ra'])
    t2=inp['t_oa']-q_s/C_s;t4=inp['t_ra']+q_s/C_e
    # Eq. (2b): minimum dry-air mass flow limits moisture transfer.
    moisture=eps_l*min(m_s,m_e)*(w1-w3)
    w2=w1-moisture/m_s;w4=w3+moisture/m_e
    s1=state(inp['t_oa'],w1,p);s2=state(t2,w2,p);s3=state(inp['t_ra'],w3,p);s4=state(t4,w4,p);ss=state(inp['t_sup'],ws,p)
    q_rec=m_s*(s1['H']-s2['H']);q_ex=m_e*(s4['H']-s3['H'])
    q_coil=m_s*(s2['H']-ss['H'])
    # Sensible/latent decomposition using average moist-air cp.
    cp_coil=1.006+1.86*(w2+ws)/2
    q_coil_s=m_s*cp_coil*(t2-inp['t_sup'])
    q_coil_l=q_coil-q_coil_s
    warnings=[]
    if abs(q_rec-q_ex)>max(0.05,0.025*max(abs(q_rec),abs(q_ex))):
        warnings.append('Enthalpy balance discrepancy exceeds 2.5%; simplified sensible/latent cp treatment. Review before design use.')
    if ws>w2+1e-7:warnings.append('Target supply humidity ratio exceeds recovery outlet: humidification required; not provided by cooling coil.')
    if q_coil<0:warnings.append('Signed coil duty is heating; chilled-water flow not applicable.')
    if inp['recovery']=='Run-Around Coil (sensible)':warnings.append('Run-around effectiveness is user-entered; coil UA/flow interaction not modeled.')
    if abs(inp['t_oa']-inp['t_ra'])<0.01:warnings.append('Small temperature driving force: sensible effectiveness comparison is poorly conditioned.')
    result={}
    for prefix,s in [('OA',s1),('RC',s2),('RA',s3),('SUP',ss),('EX',s4)]:
        for k,val in s.items():result[f'{prefix}_{k}']=val
    result.update(Q_rec=q_rec,Q_rec_sensible=q_s,Q_rec_latent=q_rec-q_s,Q_coil_tot=q_coil,Q_coil_sen=q_coil_s,Q_coil_lat=q_coil_l,
                  CW_flow=max(0,q_coil)/(4.186*5),mass_flow=m_s,exhaust_mass_flow=m_e,
                  supply_specific_volume=s1['V'],exhaust_specific_volume=s3['V'],
                  sensible_balance_kw=q_s-C_e*(t4-inp['t_ra']),
                  moisture_balance_kg_s=m_s*(w1-w2)-m_e*(w4-w3),
                  enthalpy_balance_kw=q_rec-q_ex,
                  recovery_type=inp['recovery'],warnings=warnings,pressure_pa=p,
                  eps_sensible=eps_s,eps_latent=eps_l,
                  equation_reference='2020 ASHRAE Handbook HVAC Systems and Equipment (SI), Chapter 26, Eqs. (2a), (2b), (5a)-(5d), pp. 26.2-26.4')
    if inp['recovery']=='Run-Around Coil (sensible)':
        cp=float(inp.get('loop_cp',3.8));dt=float(inp.get('loop_dt',5));rho=float(inp.get('loop_rho',1030));dp=float(inp.get('loop_dp',80));eta=float(inp.get('pump_eta',55))/100
        if min(cp,dt,rho,eta)<=0 or dp<0:raise ValueError('Invalid hydronic inputs.')
        duty=abs(q_s);mf=duty/(cp*dt);vf=mf/rho
        result.update(loop_duty_kw=duty,loop_mass_kg_s=mf,loop_flow_l_s=vf*1000,
                      pump_head_m=dp*1000/(rho*9.80665),pump_power_kw=vf*dp/eta,
                      net_recovery_after_pump_kw=abs(q_rec)-vf*dp/eta)
    return result
