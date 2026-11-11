import unittest
from engagement.engagement_bot_finder import Turn, coerce_turns, score_session
from engagement.reward_qualification import VerifiedOutcome, qualify_rewards

class BotFinderTests(unittest.TestCase):
    def test_insufficient_data(self):
        self.assertEqual(score_session([Turn("a"),Turn("b"),Turn("c")])["classification"],"INSUFFICIENT_DATA")
    def test_invalid_role_rejected(self):
        with self.assertRaises(ValueError): coerce_turns([{"text":"x","role":[]}])

class RewardTests(unittest.TestCase):
    def setUp(self):
        self.event=VerifiedOutcome("code","task_completion",1.0,"scar:sha3:abc123","2026-11-11T00:00:00Z")
    def test_verifier_required(self):
        with self.assertRaises(ValueError): qualify_rewards("HUMAN",[self.event],None)
    def test_verified_depth_weighted_reward(self):
        r=qualify_rewards("HUMAN",[self.event],lambda e:True)
        self.assertEqual(r.status,"QUALIFIED"); self.assertEqual(r.earned_units,30.0)
    def test_unverified_rejected(self):
        r=qualify_rewards("HUMAN",[self.event],lambda e:False)
        self.assertEqual(r.earned_units,0.0); self.assertEqual(r.rejected_outcomes,1)
    def test_duplicate_ref_counted_once(self):
        r=qualify_rewards("HUMAN",[self.event,self.event],lambda e:True)
        self.assertEqual(r.verified_outcomes,1); self.assertEqual(r.rejected_outcomes,1)
    def test_malformed_evidence_fails_closed(self):
        bad=VerifiedOutcome([], "task_completion",1.0,123,None)
        r=qualify_rewards("HUMAN",[bad],lambda e:True)
        self.assertEqual(r.earned_units,0.0); self.assertEqual(r.rejected_outcomes,1)
    def test_bot_suspicious_denied(self):
        for label in ("BOT","SUSPICIOUS"):
            r=qualify_rewards(label,[self.event],lambda e:True)
            self.assertEqual(r.status,"DENIED"); self.assertEqual(r.earned_units,0.0)
    def test_insufficient_data_pending(self):
        r=qualify_rewards("INSUFFICIENT_DATA",[self.event],lambda e:True)
        self.assertEqual(r.status,"PENDING_REVIEW"); self.assertEqual(r.earned_units,0.0)
    def test_streak_bonus(self):
        r=qualify_rewards("HUMAN",[self.event],lambda e:True,streak_days=7)
        self.assertEqual(r.earned_units,37.5)

if __name__=="__main__": unittest.main()
