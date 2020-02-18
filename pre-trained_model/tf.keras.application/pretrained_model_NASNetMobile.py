from __future__ import absolute_import, division, print_function, unicode_literals
import os
import tensorflow as tf
from tensorflow import keras
import time
import pandas as pd

import os
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '2'

# origin="http://www.image-net.org/image/tiny/tiny-imagenet-200.zip"

path = './tiny-imagenet-200/'

train_dir = os.path.join(path,'train')
batch_size = 100

train_datagen = keras.preprocessing.image.ImageDataGenerator(rescale=1./255)
train_generator = train_datagen.flow_from_directory(train_dir, target_size=(224, 224),
                                                     batch_size=batch_size, class_mode='categorical',
                                                     shuffle=True, seed=42)

# Create the base model from the pretrained convnets
IMG_SHAPE = (224, 224, 3)
# Create the base model from the pre-trained model MobileNet V2
base_model = tf.keras.applications.NASNetMobile(input_shape=IMG_SHAPE, include_top=False,
                                               weights='imagenet')

# Feature extraction
# freeze the convolutional base
base_model.trainable = False
# add a classification head
model = tf.keras.Sequential([base_model, keras.layers.GlobalAveragePooling2D(),
                             keras.layers.Dense(200, activation='softmax')])

# compile the model
model.compile(optimizer=tf.keras.optimizers.RMSprop(lr=0.0001), loss='categorical_crossentropy',
              metrics=['accuracy'])

time_df = pd.DataFrame(columns=["Batch_Size", "Training_Time"])
training_time = []
batch = []

for i in range(1000):
    count = 0
    images = iter(train_generator).next()[0]
    count += 1
    start_time = time.time()
    y_pred_keras = model.predict_classes(images)
    duration_time = time.time()-start_time
    print("Training Time : %8.4f (s)" % (duration_time))
    batch.append(batch_size)
    training_time.append(duration_time)

time_df = pd.DataFrame({"Batch_Size": batch, "Training_Time": training_time})

#time_df.to_csv('training time.csv')

