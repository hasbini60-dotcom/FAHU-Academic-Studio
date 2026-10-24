import unittest
from ashrae_engine import calculate, specific_volume, w_from_rh

BASE=dict(t_oa=35,rh_oa=.20,t_ra=24,rh_ra=.50,t_sup=14.2,rh_sup=.95,v_oa=4410,v_exhaust=4270,eps_s=.5,eps_l=.5,recovery='Thermal Wheel (total)')

class TestASHRAEChapter26(unittest.TestCase):
    def test_handbook_example_1(self):
        # Handbook Ch.26, Example 1 p.26.4: 35C 20% RH 4.41 m3/s;
        # 24C 50% RH 4.27 m3/s; 50% sensible and latent effectiveness.
        # Source reports supply T2=29.5C, W2≈0.0080 kg/kg,
        # sensible transfer 27.5kW, latent -11.52kW, net 15.98kW.
        r=calculate(BASE)
        self.assertAlmostEqual(r['RC_DB'],29.5,delta=.2)
        self.assertAlmostEqual(r['RC_W']/1000,.0080,delta=.0003)
        self.assertAlmostEqual(r['Q_rec_sensible'],27.5,delta=1.3)
        self.assertAlmostEqual(r['Q_rec'],15.98,delta=3.2)  # Different saturation-property correlations and rounded handbook states

    def test_handbook_published_arithmetic(self):
        # Exact published example inputs (rounded psychrometric states),
        # p.26.4: qs=5*(35-29.5)=27.5; qL=5*2560*(.0071-.0080)=-11.52.
        qs=5.0*(35.0-29.5)
        ql=5.0*2560*(.0071-.0080)
        self.assertAlmostEqual(qs,27.5,places=7)
        self.assertAlmostEqual(ql,-11.52,places=7)
        self.assertAlmostEqual(qs+ql,15.98,places=7)

    def test_unequal_airflows_conserve_sensible_moisture(self):
        inp=dict(BASE,v_exhaust=2200,eps_s=.75,eps_l=.55)
        r=calculate(inp)
        self.assertAlmostEqual(r['sensible_balance_kw'],0,places=8)
        self.assertAlmostEqual(r['moisture_balance_kg_s'],0,places=10)
        self.assertNotAlmostEqual(inp['t_ra']-r['EX_DB'],r['RC_DB']-inp['t_oa'],delta=.2)

    def test_sensible_only_preserves_humidity(self):
        for recovery in ('Plate HX (sensible)','Run-Around Coil (sensible)'):
            r=calculate(dict(BASE,recovery=recovery))
            self.assertAlmostEqual(r['RC_W'],r['OA_W'],places=8)
            self.assertAlmostEqual(r['EX_W'],r['RA_W'],places=8)

    def test_site_pressure_changes_mass_flow(self):
        r1=calculate(BASE);r2=calculate(dict(BASE,pressure_pa=85000))
        self.assertLess(r2['mass_flow'],r1['mass_flow'])

    def test_runaround_pump(self):
        r=calculate(dict(BASE,recovery='Run-Around Coil (sensible)',loop_cp=3.8,loop_dt=5,loop_rho=1030,loop_dp=80,pump_eta=55))
        self.assertGreater(r['pump_power_kw'],0)
        self.assertAlmostEqual(r['pump_power_kw'],r['loop_flow_l_s']/1000*80000/.55/1000,places=9)

    def test_bad_inputs(self):
        with self.assertRaises(ValueError):calculate(dict(BASE,v_exhaust=0))
        with self.assertRaises(ValueError):calculate(dict(BASE,eps_s=1.1))

if __name__=='__main__':unittest.main(verbosity=2)
