import glob
import os

import numpy as np
import torch
import torch.nn as nn
import torchvision.models as models
import torch.nn.functional


class Model(nn.Module):
    CHECKPOINT_FILENAME_PATTERN = 'model-{}.pth'

    def __init__(self):
        super().__init__()
        pretrained_net = models.vgg16_bn(pretrained=True)

        self._feature = pretrained_net.features

        fc1 = [it for i, it in enumerate(pretrained_net.classifier.children()) if i < 3]
        self._fc1 = nn.Sequential(*fc1)

        self._fc2 = nn.Sequential(
            nn.Linear(8192, 4096),
            nn.ReLU(True),
            nn.Dropout(),
        )

        self._fa_logits = nn.Linear(4096, 2)
        self._ges_logits = nn.Linear(4096, 13)
        self._obj_logits = nn.Linear(4096, 24)

    def forward(self, hand_images, head_images):
        hand_features = self._feature(hand_images)
        head_features = self._feature(head_images)

        hand_features = hand_features.view(-1, 512 * 7 * 7)
        head_features = head_features.view(-1, 512 * 7 * 7)

        hand_fc1 = self._fc1(hand_features)
        head_fc1 = self._fc1(head_features)

        features = torch.cat([hand_fc1, head_fc1], dim=1)

        features = self._fc2(features)

        fa_logits = self._fa_logits(features)
        ges_logits = self._ges_logits(features)
        obj_logits = self._obj_logits(features)

        return fa_logits, ges_logits, obj_logits

    @staticmethod
    def loss(fa_logits, ges_logits, obj_logits, fa_labels, ges_labels, obj_labels, obj_weight):
        fa_cross_entropy = torch.nn.functional.cross_entropy(input=fa_logits, target=fa_labels)
        ges_cross_entropy = torch.nn.functional.cross_entropy(input=ges_logits, target=ges_labels)
        obj_cross_entropy = torch.nn.functional.cross_entropy(input=obj_logits, target=obj_labels, weight=obj_weight)
        return fa_cross_entropy, ges_cross_entropy, obj_cross_entropy

    def save(self, path_to_dir, step, optimizer, maximum=10):
        path_to_models = glob.glob(os.path.join(path_to_dir, Model.CHECKPOINT_FILENAME_PATTERN.format('*')))
        if len(path_to_models) == maximum:
            min_step = min([int(path_to_model.split('/')[-1][6:-4]) for path_to_model in path_to_models])
            path_to_min_step_model = os.path.join(path_to_dir, Model.CHECKPOINT_FILENAME_PATTERN.format(min_step))
            os.remove(path_to_min_step_model)

        checkpoint_filename = os.path.join(path_to_dir, Model.CHECKPOINT_FILENAME_PATTERN.format(step))
        torch.save({
            'step': step,
            'state_dict': self.state_dict(),
            'optimizer': optimizer.state_dict()
        }, checkpoint_filename)

        return checkpoint_filename

    def load(self, checkpoint_filename, optimizer=None):
        checkpoint = torch.load(checkpoint_filename)
        step = checkpoint['step']
        self.load_state_dict(checkpoint['state_dict'])
        if optimizer is not None:
            optimizer.load_state_dict(checkpoint['optimizer'])
        return step


if __name__ == '__main__':
    def main():
        model = Model()

    main()
