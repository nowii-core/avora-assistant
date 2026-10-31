import unittest
from clara_core.runtime import bootstrap_reply

class RuntimeTransparencyTests(unittest.TestCase):
    def test_untrained_runtime_does_not_fake_a_conversation(self):
        reply = bootstrap_reply('Ciao, puoi aiutarmi?')
        self.assertIn('non è ancora stato addestrato', reply)
        self.assertIn('non è disponibile', reply)
        self.assertIn('data/corpus/', reply)
        self.assertIn('finetune.py', reply)

if __name__ == '__main__': unittest.main()
