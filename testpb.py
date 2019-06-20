#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed Jun 12 11:54:54 2019

@author: jushi
"""
from forward import ForwardModel
import cv2
import numpy as np
#import skimage
is_coco=True
def get_config1():
    if is_coco:
        import coco
        class InferenceConfig(coco.CocoConfig):
            GPU_COUNT = 1
            IMAGES_PER_GPU = 1

        config = InferenceConfig()

    else:
#        config = mask_config(NUMBER_OF_CLASSES)
        pass

    return config
my_config=get_config1()

forward_model = ForwardModel('./frozen_model/mask_frozen_graph.pb', my_config)
#forward_model = ForwardModel('./serving_model/1/saved_model.pb', my_config)
list_of_image_arrays=cv2.imread("./zptest.jpg")
list_of_image_arrays=np.expand_dims(list_of_image_arrays,axis=0)
#skimage.transform.rescale(list_of_image_arrays, (4,4))
#if list_of_image_arrays.ndim != 3:
#    list_of_image_arrays = skimage.color.gray2rgb(list_of_image_arrays)
#        # If has an alpha channel, remove it for consistency
#if list_of_image_arrays.shape[-1] == 4:
#    list_of_image_arrays = list_of_image_arrays[..., :3]


results = forward_model(list_of_image_arrays)
print(results)

