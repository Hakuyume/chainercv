import unittest

import numpy as np

from chainer import testing
from chainer import Variable

from chainercv.links import ResNet101
from chainercv.links import ResNet152
from chainercv.links import ResNet50
from chainercv.testing import attr


@testing.parameterize(*(
    testing.product_dict(
        [
            {'pick': 'prob', 'shapes': (1, 200), 'n_class': 200},
            {'pick': 'res5',
             'shapes': (1, 2048, 7, 7), 'n_class': None},
            {'pick': ['res2', 'conv1'],
             'shapes': ((1, 256, 56, 56), (1, 64, 112, 112)), 'n_class': None},
        ],
        [
            {'model_class': ResNet50},
            {'model_class': ResNet101},
            {'model_class': ResNet152},
        ],
        [
            {'arch': 'fb'},
            {'arch': 'he'}
        ]
    )
))
class TestResNetCall(unittest.TestCase):

    def setUp(self):
        self.link = self.model_class(
            n_class=self.n_class, pretrained_model=None, arch=self.arch)
        self.link.pick = self.pick

    def check_call(self):
        xp = self.link.xp

        x = Variable(xp.asarray(np.random.uniform(
            -1, 1, (1, 3, 224, 224)).astype(np.float32)))
        features = self.link(x)
        if isinstance(features, tuple):
            for activation, shape in zip(features, self.shapes):
                self.assertEqual(activation.shape, shape)
        else:
            self.assertEqual(features.shape, self.shapes)
            self.assertEqual(features.dtype, np.float32)

    @attr.slow
    def test_call_cpu(self):
        self.check_call()

    @attr.gpu
    @attr.slow
    def test_call_gpu(self):
        self.link.to_gpu()
        self.check_call()


@testing.parameterize(
    {'model_class': ResNet50},
    {'model_class': ResNet101},
    {'model_class': ResNet152},
)
class TestResNetPretrained(unittest.TestCase):

    @attr.disk
    @attr.slow
    def test_pretrained(self):
        self.model_class(pretrained_model='imagenet', arch='he')

    @attr.disk
    @attr.slow
    def test_pretrained_n_class(self):
        self.model_class(n_class=1000, pretrained_model='imagenet', arch='he')

    def test_pretrained_wrong_n_fg_class(self):
        with self.assertRaises(ValueError):
            self.model_class(n_class=500, pretrained_model='imagenet')


testing.run_module(__name__, __file__)
