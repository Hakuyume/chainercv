import argparse
import numpy as np

import chainer
from chainer.links import Convolution2D
from chainer import serializers

from chainercv.links import Conv2DBNActiv
from chainercv.links import YOLOv2
from chainercv.links import YOLOv3


def load_param(file, param):
    if isinstance(param, chainer.Variable):
        param = param.array
    data = np.fromfile(file, dtype=np.float32, count=param.size)
    if data.size == param.size:
        param[:] = data.reshape(param.shape)
    else:
        raise IOError


def load_link(file, link):
    if isinstance(link, Convolution2D):
        load_param(file, link.b)
        load_param(file, link.W)
    elif isinstance(link, Conv2DBNActiv):
        load_param(file, link.bn.beta)
        load_param(file, link.bn.gamma)
        load_param(file, link.bn.avg_mean)
        load_param(file, link.bn.avg_var)
        load_param(file, link.conv.W)
    elif isinstance(link, chainer.ChainList):
        for l in link:
            load_link(file, l)


def reorder_loc(conv, n_fg_class):
    # xy -> yx
    for data in (conv.W.array, conv.b.array):
        data = data.reshape(
            (-1, 4 + 1 + n_fg_class) + data.shape[1:])
        data[:, [1, 0, 3, 2]] = data[:, :4].copy()


def load_and_save_yolo_v2(file, serializer, model):
    try:
        for i, link in enumerate(model.extractor):
            load_link(file, link)
            link.serialize(serializer['extractor']['{}'.format(i)])
        load_link(file, model.subnet)
        reorder_loc(model.subnet, model.n_fg_class)
        link.serialize(serializer['subnet'])
    except IOError:
        pass


def load_and_save_yolo_v3(file, serializer, model):
    try:
        for i, link in enumerate(model.extractor):
            load_link(file, link)
            link.serialize(serializer['extractor']['{}'.format(i)])
            if i in {33, 39, 45}:
                j = (i - 33) // 6
                subnet = model.subnet[j]
                load_link(file, subnet)
                reorder_loc(subnet[-1], model.n_fg_class)
                link.serialize(serializer['subnet']['{}'.format(j)])
    except IOError:
        pass


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        '--model', choices=('yolo_v2', 'yolo_v3'),
        default='yolo_v2')
    parser.add_argument('--n_fg_class', type=int, default=80)
    parser.add_argument('darknetmodel')
    parser.add_argument('output')
    args = parser.parse_args()

    if args.model == 'yolo_v2':
        model = YOLOv2(n_fg_class=args.n_fg_class)
    elif args.model == 'yolo_v3':
        model = YOLOv3(n_fg_class=args.n_fg_class)

    with chainer.using_config('train', False):
        model(np.empty((1, 3, model.insize, model.insize), dtype=np.float32))

    with open(args.darknetmodel, mode='rb') as f:
        major = np.fromfile(f, dtype=np.int32, count=1)
        minor = np.fromfile(f, dtype=np.int32, count=1)
        np.fromfile(f, dtype=np.int32, count=1)  # revision
        assert(major * 10 + minor >= 2 and major < 1000 and minor < 1000)
        np.fromfile(f, dtype=np.int64, count=1)  # seen

        serializer = serializers.DictionarySerializer()
        if args.model == 'yolo_v2':
            load_and_save_yolo_v2(f, serializer, model)
        elif args.model == 'yolo_v3':
            load_and_save_yolo_v3(f, serializer, model)

    with open(args.output, mode='wb') as f:
        np.savez_compressed(f, **serializer.target)


if __name__ == '__main__':
    main()
