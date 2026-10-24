import unittest
from ashrae_engine import calculate
from calculation_audit import build_audit,audit_text
from test_engine import BASE
class TestAudit(unittest.TestCase):
    def test_audit_and_conservation(self):
        r=calculate(BASE);a=build_audit(BASE,r)
        self.assertGreaterEqual(len(a['steps']),11)
        self.assertTrue(all(c['status']=='PASS' for c in a['checks']))
        self.assertIn('ASHRAE',audit_text(a))
    def test_runaround_hydraulics(self):
        i=dict(BASE,recovery='Run-Around Coil (sensible)',loop_cp=3.8,loop_dt=5,loop_rho=1030,loop_dp=80,pump_eta=55)
        a=build_audit(i,calculate(i))
        self.assertTrue(any(s['title']=='Pump power' for s in a['steps']))
if __name__=='__main__':unittest.main()
