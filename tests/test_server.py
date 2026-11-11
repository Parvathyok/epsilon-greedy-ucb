import unittest
from backend.server import validate,custom_run,render,STUDY
import math

class DashboardTests(unittest.TestCase):
    def test_invalid_coefficient_is_rejected(self):
        with self.assertRaises(ValueError):validate({'c':['nan']})
    def test_invalid_budget_is_rejected(self):
        with self.assertRaises(ValueError):validate({'runs':['100000']})
    def test_unknown_scenario_is_rejected(self):
        with self.assertRaises(ValueError):validate({'scenario':['unknown']})
    def test_completed_custom_run(self):
        cfg=validate({'runs':['20'],'horizon':['100'],'epsilon':['0.2'],'c':['0.5']})
        result=custom_run(cfg)
        self.assertEqual(len(result),4)
        self.assertIn('UCB c=0.5',result)
        self.assertTrue(all(sum(v['pulls'])>99.999 for v in result.values()))
    def test_page_escapes_errors_and_contains_results(self):
        cfg=dict(scenario='wide',runs=500,horizon=10000,seed=20261111,epsilon=.1,c=math.sqrt(2))
        page=render(STUDY['wide'],cfg,error='<script>bad</script>').decode()
        self.assertNotIn('<script>',page)
        self.assertIn('359.4',page)
        self.assertIn('role="img"',page)

if __name__=='__main__':unittest.main()
