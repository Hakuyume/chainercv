import numpy as np
import unittest

import chainer
from chainer import testing

from chainercv.links import YOLOv3
from chainercv.testing import attr


@testing.parameterize(*testing.product({
    'n_fg_class': [1, 5, 20],
}))
class TestYOLOv3(unittest.TestCase):

    def setUp(self):
        self.link = YOLOv3(n_fg_class=self.n_fg_class)
        self.insize = 416
        self.n_bbox = (13 * 13 + 26 * 26 + 52 * 52) * 3

    def _check_call(self):
        x = self.link.xp.array(
            np.random.uniform(-1, 1, size=(1, 3, self.insize, self.insize)),
            dtype=np.float32)

        y = self.link(x)

        self.assertIsInstance(y, chainer.Variable)
        self.assertIsInstance(y.array, self.link.xp.ndarray)
        self.assertEqual(y.shape, (1, self.n_bbox, 4 + 1 + self.n_fg_class))

    @attr.slow
    def test_call_cpu(self):
        self._check_call()

    @attr.gpu
    @attr.slow
    def test_call_gpu(self):
        self.link.to_gpu()
        self._check_call()


class TestYOLOv3Pretrained(unittest.TestCase):

    @attr.disk
    @attr.slow
    def test_pretrained(self):
        YOLOv3(pretrained_model='voc0712')

    @attr.disk
    @attr.slow
    def test_pretrained_n_fg_class(self):
        YOLOv3(n_fg_class=20, pretrained_model='voc0712')

    def test_pretrained_wrong_n_fg_class(self):
        with self.assertRaises(ValueError):
            YOLOv3(n_fg_class=10, pretrained_model='voc0712')


testing.run_module(__name__, __file__)
