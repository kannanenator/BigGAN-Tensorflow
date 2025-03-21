import scipy.misc
import numpy as np
import os
import pickle
from glob import glob

import tensorflow as tf
import tensorflow.contrib.slim as slim
from keras.datasets import cifar10, mnist

from tensorflow.keras.utils import to_categorical
from tensorflow.keras.preprocessing.text import Tokenizer

class ImageData:

    def __init__(self, load_size, channels, custom_dataset):
        self.load_size = load_size
        self.channels = channels
        self.custom_dataset = custom_dataset

    def image_processing(self, filename):

        if not self.custom_dataset :
            x_decode = filename
        else :
            x = tf.read_file(filename)
            x_decode = tf.image.decode_jpeg(x, channels=self.channels)

        img = tf.image.resize_images(x_decode, [self.load_size, self.load_size])
        img = tf.cast(img, tf.float32) / 127.5 - 1

        return img


def load_mnist():
    (train_data, train_labels), (test_data, test_labels) = mnist.load_data()
    x = np.concatenate((train_data, test_data), axis=0)
    x = np.expand_dims(x, axis=-1)

    return x

def load_cifar10() :
    (train_data, train_labels), (test_data, test_labels) = cifar10.load_data()
    x = np.concatenate((train_data, test_data), axis=0)

    return x

def load_proteins():
    """
    Loads tuple of dcalpha matrices, ss arrays, and pssms into numpy nd arrays
    Output dcalpha ndarray of shape (num_examples, frag_size, frag_size, 1)
    """
    
    frag_size = 128
    n_folds = 106
    dcalphas = np.array([])
    seqs = np.array([]) # nx1
    pssms = np.array([]) # nx21
    secondary = np.array([]) #nx1
    m_frags = []
    s_frags = []
    p_frags = []
    ss_frags = []
    all_pdbs = []
    for fold in range(1, n_folds):
        path = 'train/training_100_{}.pkl'.format(fold)
        data = pickle.load(open(path, 'rb'))
        pdbs = list(data.keys())
        all_pdbs += pdbs
    
        for p in pdbs:
            full_matrix = np.array(data[p]['dcalpha'])
            full_seq = np.array(data[p]['aa']) # amino acid sequence
            full_pssm = np.array(data[p]['pssm']) # pssm
            full_ss = np.array(data[p]['ss']) # secondary structure
        
            num_bonds = full_matrix.shape[0]
        
            # get non-overlapping fragments of frag_size length
            if (full_matrix.shape[0] >= frag_size): 
                idx = 0
                for i in range(frag_size, num_bonds, frag_size):
                    matrix_frag = full_matrix[idx:i, idx:i]
                    seq_frag = full_seq[()][idx:i]
                    pssm_frag = full_pssm[:, idx:i]
                    ss_frag = full_ss[()][idx:i]
                    
                    idx = i # update start index
                    m_frags.append(matrix_frag)
                    s_frags.append(seq_frag)
                    p_frags.append(pssm_frag)
                    ss_frags.append(ss_frag)
    
    
        num_loaded = len(m_frags)
        print("fold {} complete, so far loaded {} pairwise matrices of size {}"
            .format(fold, num_loaded, frag_size))
    
    dcalphas = np.stack(m_frags)
    
    # one hot encode the sequences
    tokenizer = Tokenizer(char_level=True)
    tokenizer.fit_on_texts(s_frags)
    int_seq = tokenizer.texts_to_sequences(s_frags)
    s_frags = to_categorical(int_seq)
    
    # one hot encode the sequences
    tokenizer2 = Tokenizer(char_level=True)
    tokenizer2.fit_on_texts(ss_frags)
    int_seq = tokenizer2.texts_to_sequences(ss_frags)
    ss_frags = to_categorical(int_seq)
    
    seqs = np.stack(s_frags)
    pssms = np.stack(p_frags)
    secondary = np.stack(ss_frags)
    
    dcalphas = dcalphas.reshape(dcalphas.shape[0], frag_size, frag_size, 1).astype('float32')
    pssms = pssms.reshape(pssms.shape[0], 128, 21).astype('float32')
    
    cond = np.array([])
    cond = np.concatenate((seqs,pssms,secondary), axis=2) # thing we are conditioning on nx51
    cond = cond.reshape(cond.shape[0], 128, 51, 1).astype('float32')
    print(dcalphas.shape)
    print(cond.shape)
    
    return dcalphas, cond

def load_data(dataset_name) :
    if dataset_name == 'mnist' :
        x = load_mnist()
    elif dataset_name == 'cifar10' :
        x = load_cifar10()
    else :

        x = glob(os.path.join("./dataset", dataset_name, '*.*'))

    return x


def preprocessing(x, size):
    x = scipy.misc.imread(x, mode='RGB')
    x = scipy.misc.imresize(x, [size, size])
    x = normalize(x)
    return x

def normalize(x) :
    return x/127.5 - 1

def downscale(x, factor):
    return x/factor

def save_images(images, size, image_path):
    return imsave(inverse_transform(images), size, image_path)

def merge(images, size):
    h, w = images.shape[1], images.shape[2]
    if (images.shape[3] in (3,4)):
        c = images.shape[3]
        img = np.zeros((h * size[0], w * size[1], c))
        for idx, image in enumerate(images):
            i = idx % size[1]
            j = idx // size[1]
            img[j * h:j * h + h, i * w:i * w + w, :] = image
        return img
    elif images.shape[3]==1:
        img = np.zeros((h * size[0], w * size[1]))
        for idx, image in enumerate(images):
            i = idx % size[1]
            j = idx // size[1]
            img[j * h:j * h + h, i * w:i * w + w] = image[:,:,0]
        return img
    else:
        raise ValueError('in merge(images,size) images parameter ''must have dimensions: HxW or HxWx3 or HxWx4')

def imsave(images, size, path):
    # image = np.squeeze(merge(images, size)) # 채널이 1인거 제거 ?
    return scipy.misc.imsave(path, merge(images, size))


def inverse_transform(images):
    return (images+1.)/2.


def check_folder(log_dir):
    if not os.path.exists(log_dir):
        os.makedirs(log_dir)
    return log_dir

def show_all_variables():
    model_vars = tf.trainable_variables()
    slim.model_analyzer.analyze_vars(model_vars, print_info=True)

def str2bool(x):
    return x.lower() in ('true')

##################################################################################
# Regularization
##################################################################################

def orthogonal_regularizer(scale) :
    """ Defining the Orthogonal regularizer and return the function at last to be used in Conv layer as kernel regularizer"""

    def ortho_reg(w) :
        """ Reshaping the matrxi in to 2D tensor for enforcing orthogonality"""
        _, _, _, c = w.get_shape().as_list()

        w = tf.reshape(w, [-1, c])

        """ Declaring a Identity Tensor of appropriate size"""
        identity = tf.eye(c)

        """ Regularizer Wt*W - I """
        w_transpose = tf.transpose(w)
        w_mul = tf.matmul(w_transpose, w)
        reg = tf.subtract(w_mul, identity)

        """Calculating the Loss Obtained"""
        ortho_loss = tf.nn.l2_loss(reg)

        return scale * ortho_loss

    return ortho_reg

def orthogonal_regularizer_fully(scale) :
    """ Defining the Orthogonal regularizer and return the function at last to be used in Fully Connected Layer """

    def ortho_reg_fully(w) :
        """ Reshaping the matrix in to 2D tensor for enforcing orthogonality"""
        _, c = w.get_shape().as_list()

        """Declaring a Identity Tensor of appropriate size"""
        identity = tf.eye(c)
        w_transpose = tf.transpose(w)
        w_mul = tf.matmul(w_transpose, w)
        reg = tf.subtract(w_mul, identity)

        """ Calculating the Loss """
        ortho_loss = tf.nn.l2_loss(reg)

        return scale * ortho_loss

    return ortho_reg_fully