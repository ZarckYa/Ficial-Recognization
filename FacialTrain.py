#!/usr/bin/env python
# coding: utf-8

# In[2]:


import random
import tensorflow as tf
import numpy as np
from tensorflow import keras
from tensorflow.keras import backend as K
from tensorflow.keras.layers import Convolution2D, MaxPooling2D
from tensorflow.keras.layers import Dense, Dropout, Activation, Flatten
from tensorflow.keras.models import Sequential
from tensorflow.keras.models import load_model
from tensorflow.keras.optimizers import SGD
from tensorflow.keras.preprocessing.image import ImageDataGenerator
from tensorflow.keras import utils
from sklearn.model_selection import train_test_split
from LoadFaceData import load_dataset, resize_image, IMAGE_SIZE


# In[ ]:


class Dataset:
    def __init__(self, path_name):
        # 训练集
        self.train_images = None
        self.train_labels = None

        # 验证集
        self.valid_images = None
        self.valid_labels = None

        # 测试集
        self.test_images = None
        self.test_labels = None

        # 数据集加载路径
        self.path_name = path_name

        # 当前库采用的维度顺序
        self.input_shape = None

        self.nb_classes = None

    # 加载数据集并按照交叉验证的原则划分数据集并进行相关预处理工作
    def load(self, img_rows=IMAGE_SIZE, img_cols=IMAGE_SIZE,
             img_channels=3):
        # 加载数据集到内存
        image = []
        labels = []
        face_num = []
        images, labels, face_num = load_dataset(self.path_name)
        self.nb_classes = face_num
        
        train_images, valid_images, train_labels, valid_labels = train_test_split(images, labels, test_size=0.3,
                                                                                  random_state=random.randint(0, 100))
        _, test_images, _, test_labels = train_test_split(images, labels, test_size=0.5,
                                                          random_state=random.randint(0, 100))

        # 当前的维度顺序如果为'th'，则输入图片数据时的顺序为：channels,rows,cols，否则:rows,cols,channels
        # 这部分代码就是根据keras库要求的维度顺序重组训练数据集
        if K.image_data_format() == 'channels_first':
            train_images = train_images.reshape(train_images.shape[0], img_channels, img_rows, img_cols)
            valid_images = valid_images.reshape(valid_images.shape[0], img_channels, img_rows, img_cols)
            test_images = test_images.reshape(test_images.shape[0], img_channels, img_rows, img_cols)
            self.input_shape = (img_channels, img_rows, img_cols)
        else:
            train_images = train_images.reshape(train_images.shape[0], img_rows, img_cols, img_channels)
            valid_images = valid_images.reshape(valid_images.shape[0], img_rows, img_cols, img_channels)
            test_images = test_images.reshape(test_images.shape[0], img_rows, img_cols, img_channels)
            self.input_shape = (img_rows, img_cols, img_channels)

            # 输出训练集、验证集、测试集的数量
            print(train_images.shape[0], 'train samples')
            print(valid_images.shape[0], 'valid samples')
            print(test_images.shape[0], 'test samples')
            #print(dataset.input_shape)
            '''
            我们的模型使用categorical_crossentropy作为损失函数，因此需要根据类别数量nb_classes将
            类别标签进行one-hot编码使其向量化，在这里我们的类别只有两种，经过转化后标签数据变为二维
            '''
            train_labels = utils.to_categorical(train_labels, self.nb_classes)
            valid_labels = utils.to_categorical(valid_labels, self.nb_classes)
            test_labels = utils.to_categorical(test_labels, self.nb_classes)
            
            # 像素数据浮点化以便归一化
            train_images = train_images.astype('float32')
            valid_images = valid_images.astype('float32')
            test_images = test_images.astype('float32')

            # 将其归一化,图像的各像素值归一化到0~1区间
            train_images /= 255
            valid_images /= 255
            test_images /= 255

            self.train_images = train_images
            self.valid_images = valid_images
            self.test_images = test_images
            self.train_labels = train_labels
            self.valid_labels = valid_labels
            self.test_labels = test_labels


# CNN网络模型类
class Model:
    def __init__(self):
        self.model = None

        # 建立模型

    def build_model(self, dataset, nb_classes):
       # 构建一个空的网络模型，它是一个线性堆叠模型，各神经网络层会被顺序添加，专业名称为序贯模型或线性堆叠模型

        Conv_layers = [
        
        Convolution2D(filters=32, kernel_size = [3,3], padding = 'same', input_shape = dataset.input_shape, activation = tf.nn.relu),
        MaxPooling2D(pool_size=[2,2]),
        
        Convolution2D(filters=64, kernel_size = [3,3], padding = 'same', input_shape = dataset.input_shape, activation = tf.nn.relu),
        MaxPooling2D(pool_size=[2,2]),
        
        Convolution2D(filters=128, kernel_size = [3,3], padding = 'same', input_shape = dataset.input_shape, activation = tf.nn.relu),
        MaxPooling2D(pool_size=[2,2]),
        
        Flatten(),
        Dense(512, activation = tf.nn.relu),
        Dropout(0.25),
        Dense(nb_classes, activation = tf.nn.softmax)
        
        ]
        
        self.model = Sequential(Conv_layers)
        
        self.model.summary()
        
        
        
        
    # 训练模型
    def train(self, dataset, batch_size=20, nb_epoch=2, data_augmentation=True):
        sgd = SGD(learning_rate=0.0007, decay=1e-6,
                  momentum=0.9, nesterov=True)  # 采用SGD+momentum的优化器进行训练，首先生成一个优化器对象
        self.model.compile(optimizer=sgd, loss='categorical_crossentropy', metrics=['accuracy'])  # 完成实际的模型配置工作

        # 不使用数据提升，所谓的提升就是从我们提供的训练数据中利用旋转、翻转、加噪声等方法创造新的
        # 训练数据，有意识的提升训练数据规模，增加模型训练量
        if not data_augmentation:
            self.model.fit(dataset.train_images,
                           dataset.train_labels,
                           batch_size=batch_size,
                           nb_epoch=nb_epoch,
                           validation_data=(dataset.valid_images, dataset.valid_labels),
                           shuffle=True)
        # 使用实时数据提升
        else:
            # 定义数据生成器用于数据提升，其返回一个生成器对象datagen，datagen每被调用一
            # 次其生成一组数据（顺序生成），节省内存，其实就是python的数据生成器
            datagen = ImageDataGenerator(
                featurewise_center=False,  # 是否使输入数据去中心化（均值为0），
                samplewise_center=False,  # 是否使输入数据的每个样本均值为0
                featurewise_std_normalization=False,  # 是否数据标准化（输入数据除以数据集的标准差）
                samplewise_std_normalization=False,  # 是否将每个样本数据除以自身的标准差
                zca_whitening=False,  # 是否对输入数据施以ZCA白化
                rotation_range=20,  # 数据提升时图片随机转动的角度(范围为0～180)
                width_shift_range=0.2,  # 数据提升时图片水平偏移的幅度（单位为图片宽度的占比，0~1之间的浮点数）
                height_shift_range=0.2,  # 同上，只不过这里是垂直
                horizontal_flip=True,  # 是否进行随机水平翻转
                vertical_flip=False)  # 是否进行随机垂直翻转

            # 计算整个训练样本集的数量以用于特征值归一化、ZCA白化等处理
            datagen.fit(dataset.train_images)

            # 利用生成器开始训练模型
            self.model.fit_generator(datagen.flow(dataset.train_images, dataset.train_labels,
                                                  batch_size=batch_size),
                                     validation_data=(dataset.valid_images, dataset.valid_labels),
                                     steps_per_epoch=dataset.train_images.shape[0],
                                     epochs=nb_epoch)
            '''self.model.fit(datagen.flow(dataset.train_images, dataset.train_labels,
                                                  batch_size=batch_size),
                                     validation_data=(dataset.valid_images, dataset.valid_labels),
                                     steps_per_epoch=len(dataset.train_images)/20,
                                     epochs=nb_epoch)'''
    MODEL_PATH = './model'

    def save_model(self, file_path=MODEL_PATH):
        self.model.save(file_path)

    def load_model(self, file_path=MODEL_PATH):
        self.model = load_model(file_path)

    def evaluate(self, dataset):
        score = self.model.evaluate(dataset.test_images, dataset.test_labels, verbose=1)
        print("%s: %.2f%%" % (self.model.metrics_names[1], score[1] * 100))
    
    # 识别人脸
    def face_predict(self, image):
        '''# 依然是根据后端系统确定维度顺序
        if K.image_data_format() == 'channels_first' and image.shape != (1, 3, IMAGE_SIZE, IMAGE_SIZE):
            image = resize_image(image)  # 尺寸必须与训练集一致都应该是IMAGE_SIZE x IMAGE_SIZE
            image = image.reshape((1, 3, IMAGE_SIZE, IMAGE_SIZE))  # 与模型训练不同，这次只是针对1张图片进行预测
        elif K.image_data_format() == 'channels_first' and image.shape != (1, IMAGE_SIZE, IMAGE_SIZE, 3):
            image = resize_image(image)
            image = image.reshape((1, IMAGE_SIZE, IMAGE_SIZE, 3))'''
        
        # 依然是根据后端系统确定维度顺序
        if K.image_data_format() == 'channels_first':
            image = resize_image(image)  # 尺寸必须与训练集一致都应该是IMAGE_SIZE x IMAGE_SIZE
            image = image.reshape((1, 3, IMAGE_SIZE, IMAGE_SIZE))  # 与模型训练不同，这次只是针对1张图片进行预测
        else:
            image = resize_image(image)
            image = image.reshape((1, IMAGE_SIZE, IMAGE_SIZE, 3))
            
            
            
        # 浮点并归一化
        image = image.astype('float32')
        image /= 255
        #print(image.shape)
        
        # 给出输入属于各个类别的概率
        result_probability = self.model.predict(image)
        print('result:', result_probability, max(result_probability[0]))

        # 给出类别预测：0-9
        result = self.model.predict(image)
        result = np.argmax(result, axis=-1)

        # 返回类别预测结果
        return max(result_probability[0]),result[0]
        
        '''# 给出类别预测：0-9
        result = self.model.predict(image)
        resuit = np.argmax(resuit, axis=-1)
        # 返回类别预测结果
        return result[0]'''


if __name__ == '__main__':
    dataset = Dataset('./Facial data')
    dataset.load()
    model = Model()
    model.build_model(dataset, dataset.nb_classes)
    model.train(dataset)
    model.save_model(file_path='./model')
    #model.save_model(file_path='./model-python36')
    model.evaluate(dataset)


# In[ ]:



