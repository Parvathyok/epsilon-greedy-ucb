import unittest
import numpy as np
from backend.simulate import choose,update,ci,experiment,WIDE

class StudyTests(unittest.TestCase):
    def test_sample_mean_matches_hand_calculation(self):
        q=np.zeros((1,2));n=np.zeros((1,2),dtype=int)
        for r in [1.,0.,1.,1.]: update(q,n,np.array([1]),np.array([r]))
        self.assertEqual(q[0,1],.75);self.assertEqual(n[0,1],4)
        self.assertEqual(q[0,0],0.)
    def test_ucb_selects_uncertain_arm(self):
        a=choose(np.array([[.8,.5]]),np.array([[100,1]]),102,{'kind':'ucb','c':np.sqrt(2)},np.random.default_rng(1))
        self.assertEqual(int(a[0]),1)
    def test_initialization_samples_every_arm(self):
        q=np.zeros((2,10));n=np.zeros((2,10),dtype=int)
        for t in range(1,11):
            a=choose(q,n,t,{'kind':'ucb','c':np.sqrt(2)},np.random.default_rng(1))
            update(q,n,a,np.zeros(2))
        self.assertTrue(np.all(n==1))
    def test_epsilon_zero_is_greedy(self):
        q=np.tile([.1,.9,.3],(2000,1));n=np.ones_like(q)
        a=choose(q,n,4,{'kind':'epsilon','epsilon':0},np.random.default_rng(5))
        self.assertTrue(np.all(a==1))
    def test_epsilon_one_is_uniform(self):
        q=np.tile([.1,.9,.3],(30000,1));n=np.ones_like(q)
        a=choose(q,n,4,{'kind':'epsilon','epsilon':1},np.random.default_rng(8))
        self.assertTrue(np.all(abs(np.bincount(a)/30000-1/3)<.015))
    def test_ties_are_not_first_arm_biased(self):
        q=np.ones((30000,3));n=np.ones_like(q)
        a=choose(q,n,4,{'kind':'epsilon','epsilon':0},np.random.default_rng(9))
        self.assertTrue(np.all(abs(np.bincount(a)/30000-1/3)<.015))
    def test_constant_step_update(self):
        q=np.array([[.5]]);n=np.array([[100]])
        update(q,n,np.array([0]),np.array([1.]),.1)
        self.assertAlmostEqual(q[0,0],.55)
    def test_regret_zero_when_all_means_equal(self):
        out=experiment(np.ones(3)*.4,[{'name':'u','kind':'ucb','c':np.sqrt(2)}],20,200,7)
        self.assertEqual(out['u']['regret']['mean'],0.)
    def test_seed_reproducibility(self):
        p=[{'name':'e','kind':'epsilon','epsilon':.1}]
        self.assertEqual(experiment(WIDE,p,20,200,11),experiment(WIDE,p,20,200,11))
    def test_confidence_interval_against_hand_value(self):
        stats=ci(np.array([1.,2.,3.,4.]));self.assertEqual(stats['mean'],2.5)
        self.assertAlmostEqual(stats['half95'],1.96*np.sqrt(5/3)/2)
    def test_dynamic_regret_uses_current_best(self):
        # Forced actions 0 then 1 both coincide with the best action across the change.
        out=experiment(np.array([1.,0.]),[{'name':'e','kind':'epsilon','epsilon':0}],5,2,3,True)
        self.assertEqual(out['e']['regret']['mean'],0.)

if __name__=='__main__': unittest.main(verbosity=2)
