import glob
import os
from collections import defaultdict
from enum import Enum

import numpy as np
import re
from torch.utils.data import dataset
from torchvision import transforms


class Dataset(dataset.Dataset):

    def __init__(self, path_to_data, mode):
        super().__init__()

        assert isinstance(mode, Dataset.Mode)

        self._mode = mode
        self._path_to_images = glob.glob('{:s}/frames/{:s}/*/*/*[Rhand|Lhand]/*.png'.format(path_to_data, mode.value))
        self._labels = defaultdict(str)

        for environment in ['house', 'lab', 'office']:
            for side in ['left', 'right']:
                for num in ['1', '2', '3'] if mode == Dataset.Mode.TRAIN else ['4', '5', '6']:
                    self._labels['{:s}/obj/{:s}/{:s}'.format(environment, side, num)] = np.load(
                        os.path.join(path_to_data, 'labels', environment, 'obj_{:s}{:s}.npy'.format(side, num)))

    def __len__(self):
        return len(self._path_to_images)

    def __getitem__(self, index):
        path_to_image = self._path_to_images[index]
        image = transforms.Image.open(path_to_image)

        transform = transforms.Compose([
            transforms.ToTensor()
        ])
        image = transform(image)

        path_to_image_components = path_to_image.split('/')
        environment = path_to_image_components[-4]
        num = int(path_to_image_components[-3])
        if self._mode == Dataset.Mode.TEST:
            num += 3
        side = 'left' if path_to_image_components[-2] == 'Lhand' else 'right'
        image_index = int(re.match('.*?(\d+)\.png', path_to_image_components[-1]).group(1))

        label = self._labels['{:s}/obj/{:s}/{:d}'.format(environment, side, num)][image_index]
        label = int(label)

        return image, label

    class Mode(Enum):
        TRAIN = 'train'
        VAL = 'val'
        TEST = 'test'

        @staticmethod
        def from_string(s):
            if s == Dataset.Mode.TRAIN.value:
                return Dataset.Mode.TRAIN
            elif s == Dataset.Mode.VAL.value:
                return Dataset.Mode.VAL
            elif s == Dataset.Mode.TEST.value:
                return Dataset.Mode.TEST
            else:
                raise ValueError()

if __name__ == '__main__':
    def main():
        import matplotlib.pyplot as plt

        dataset = Dataset('./data', Dataset.Mode.TEST)
        indices = np.random.choice(len(dataset), 6, replace=False)

        plt.figure()
        for i, index in enumerate(indices):
            image, label = dataset[index]
            plt.subplot(3, 2, i + 1)
            plt.imshow(image.permute(1, 2, 0).cpu().numpy())
            print('label = {:d}'.format(label))
        plt.show()

    main()