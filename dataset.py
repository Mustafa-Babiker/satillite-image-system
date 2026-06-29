import os
import numpy as np
import torch
import cv2
from torch.utils.data import Dataset


class AgricultureDataset(Dataset):

    def __init__(self, img_dir, mask_dir, size=256):
        self.img_dir = img_dir
        self.mask_dir = mask_dir
        self.files = sorted(os.listdir(img_dir))
        self.size = size   

    def __len__(self):
        return len(self.files)

    def __getitem__(self, idx):

        name = self.files[idx]

        img_path = os.path.join(self.img_dir, name)
        mask_path = os.path.join(self.mask_dir, name)

        img = np.load(img_path).astype(np.float32)
        mask = np.load(mask_path).astype(np.float32)

  
        # resize the image and mask to the specified size

        img = cv2.resize(img, (self.size, self.size), interpolation=cv2.INTER_LINEAR)
        mask = cv2.resize(mask, (self.size, self.size), interpolation=cv2.INTER_NEAREST)
        img = img * 0.0001
        img = np.transpose(img, (2, 0, 1))

        return (
            torch.from_numpy(img.copy()).float(),
            torch.from_numpy(mask.copy()).float().unsqueeze(0)
        )