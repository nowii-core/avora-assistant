import unittest

try:
    import torch
    from clara_core.model import ModelConfig, ClaraGPT, VOCAB_SIZE
    HAS_TORCH = True
except ImportError:
    HAS_TORCH = False

@unittest.skipUnless(HAS_TORCH, "PyTorch non installato: test del modello saltato")
class ModelTests(unittest.TestCase):
    def test_forward_shape_and_loss(self):
        config = ModelConfig(block_size=16, n_embd=32, n_head=4, n_layer=2, dropout=0.0)
        model = ClaraGPT(config)
        x = torch.randint(0, VOCAB_SIZE, (2, 12))
        logits, loss = model(x, x)
        self.assertEqual(tuple(logits.shape), (2, 12, VOCAB_SIZE))
        self.assertIsNotNone(loss)
        self.assertTrue(torch.isfinite(loss).item())


    def test_dynamic_bpe_vocabulary_shape(self):
        config = ModelConfig(vocab_size=512, block_size=16, n_embd=32, n_head=4, n_layer=1, dropout=0.0)
        model = ClaraGPT(config)
        x = torch.randint(0, 512, (2, 12))
        logits, loss = model(x, x)
        self.assertEqual(tuple(logits.shape), (2, 12, 512))
        self.assertTrue(torch.isfinite(loss).item())

    def test_config_rejects_non_divisible_dimensions(self):
        config = ModelConfig(n_embd=30, n_head=4)
        with self.assertRaises(ValueError):
            config.validate()

if __name__ == "__main__":
    unittest.main()
