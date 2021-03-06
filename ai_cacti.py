# Copyright 2018 The AiGraph LLC, bin.bryandu@gmail.com. All Rights Reserved.
# 
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
# ==============================================================================

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import argparse
import sys
import tempfile
import os

from input_data import read_data_sets

import tensorflow as tf

FLAGS = None

def deepnn5(x , output_size):
  """deepnn builds the graph for a deep net for classifying digits.

  Args:
    x: an input tensor with the dimensions (N_examples, 288x288=82944), where 82,944 is the
    number of pixels in a standard MNIST image.

  Returns:
    A tuple (y, keep_prob). y is a tensor of shape (N_examples, 10), with values
    equal to the logits of classifying the digit into one of 10 classes (the
    digits 0-9). keep_prob is a scalar placeholder for the probability of
    dropout.
  """
  # Reshape to use within a convolutional neural net.
  # Last dimension is for "features" - there is only one here, since images are
  # grayscale -- it would be 3 for an RGB image, 4 for RGBA, etc.
  with tf.name_scope('reshape'):
    x_image = tf.reshape(x, [-1, 288, 288, 1])
    tf.summary.image('input', x_image, 3)

  # Added convolutional layer - maps one grayscale image to 64 feature maps.
  with tf.name_scope('conv0'):
    W_conv0 = weight_variable([5, 5, 1, 64])
    b_conv0 = bias_variable([64])
    h_conv0 = tf.nn.relu(conv2d(x_image, W_conv0) + b_conv0)
    tf.summary.histogram("weights", W_conv0)
    tf.summary.histogram("biases", b_conv0)
    tf.summary.histogram("activations", h_conv0)

  # Added Pooling layer - downsamples by 2X.
  with tf.name_scope('pool0'):
    h_pool0 = max_pool_2x2(h_conv0)

  # Add another convolutional layer - maps 96 feature maps.
  with tf.name_scope('conv00'):
    W_conv00 = weight_variable([3, 3, 64, 96])
    b_conv00 = bias_variable([96])
    h_conv00 = tf.nn.relu(conv2d(h_pool0, W_conv00) + b_conv00)

  # Pooling layer - downsamples by 2X.
  with tf.name_scope('pool00'):
    h_pool00 = max_pool_2x2(h_conv00)

  # Add another convolutional layer - maps 96 feature maps to 96.
  with tf.name_scope('conv000'):
    W_conv000 = weight_variable([3, 3, 96, 96])
    b_conv000 = bias_variable([96])
    h_conv000 = tf.nn.relu(conv2d(h_pool00, W_conv000) + b_conv000)

  # Pooling layer - downsamples by 2X.
  with tf.name_scope('pool000'):
    h_pool000 = max_pool_2x2(h_conv000)

  # First convolutional layer - maps 96 feature maps to 96.
  with tf.name_scope('conv1'):
    W_conv1 = weight_variable([3, 3, 96, 96])
    b_conv1 = bias_variable([96])
    h_conv1 = tf.nn.relu(conv2d(h_pool000, W_conv1) + b_conv1)

  # Pooling layer - downsamples by 2X.
  with tf.name_scope('pool1'):
    h_pool1 = max_pool_2x2(h_conv1)

  # Second convolutional layer -- maps 96 feature maps to 128.
  with tf.name_scope('conv2'):
    W_conv2 = weight_variable([3, 3, 96, 128])
    b_conv2 = bias_variable([128])
    h_conv2 = tf.nn.relu(conv2d(h_pool1, W_conv2) + b_conv2)

  # Second pooling layer.
  with tf.name_scope('pool2'):
    h_pool2 = max_pool_2x2(h_conv2)

  # Fully connected layer 1 -- after 5 round of downsampling, our 288x288 image
  # is down to 9x9x128 feature maps -- maps this to 1024 features.
  with tf.name_scope('fc1'):
    W_fc1 = weight_variable([9 * 9 * 128, 1024])
    b_fc1 = bias_variable([1024])

    h_pool2_flat = tf.reshape(h_pool2, [-1, 9*9*128])
    h_fc1 = tf.nn.relu(tf.matmul(h_pool2_flat, W_fc1) + b_fc1)

    tf.summary.histogram("weights", W_fc1)
    tf.summary.histogram("biases", b_fc1)
    tf.summary.histogram("activations", h_fc1)

  # Dropout - controls the complexity of the model, prevents co-adaptation of
  # features.
  with tf.name_scope('dropout'):
    keep_prob = tf.placeholder(tf.float32)
    h_fc1_drop = tf.nn.dropout(h_fc1, keep_prob)

  # Map the 1024 features to 3 classes, one for each digit
  with tf.name_scope('fc2'):
    W_fc2 = weight_variable([1024, output_size])
    b_fc2 = bias_variable([output_size])
    y_conv = tf.matmul(h_fc1_drop, W_fc2) + b_fc2

    tf.summary.histogram("weights", W_fc2)
    tf.summary.histogram("biases", b_fc2)
    tf.summary.histogram("activations", y_conv)

  return y_conv, keep_prob

def conv2d_2_nopad(x, W):
  """conv2d returns a 2d convolution layer with 5 stride and no pad. """
  return tf.nn.conv2d(x, W, strides=[1, 2, 2, 1], padding='VALID')

def conv2d_5_nopad(x, W):
  """conv2d returns a 2d convolution layer with 5 stride and no pad. """
  return tf.nn.conv2d(x, W, strides=[1, 5, 5, 1], padding='VALID')


def conv2d_1_nopad(x, W):
  """conv2d returns a 2d convolution layer with 1 stride and no pad. """
  return tf.nn.conv2d(x, W, strides=[1, 1, 1, 1], padding='VALID')

def conv2d(x, W):
  """conv2d returns a 2d convolution layer with full stride."""
  return tf.nn.conv2d(x, W, strides=[1, 1, 1, 1], padding='SAME')


def max_pool_2x2(x):
  """max_pool_2x2 downsamples a feature map by 2X."""
  return tf.nn.max_pool(x, ksize=[1, 2, 2, 1],
                        strides=[1, 2, 2, 1], padding='SAME')


def weight_variable(shape):
  """weight_variable generates a weight variable of a given shape."""
  initial = tf.truncated_normal(shape, stddev=0.1)
  return tf.Variable(initial)


def bias_variable(shape):
  """bias_variable generates a bias variable of a given shape."""
  initial = tf.constant(0.1, shape=shape)
  return tf.Variable(initial)


def main(_):

  # Import data
  mnist, num_of_trains, test_files = read_data_sets(FLAGS.t, one_hot=True, reshape=True, validation_size=100, image_size=288, output_size=3, train_dir=FLAGS.d)

  # Create the model
  x = tf.placeholder(tf.float32, [None, 82944])

  # Define loss and optimizer
  y_ = tf.placeholder(tf.float32, [None, 3])

  # Build the graph for the deep net
  if ( FLAGS.n == '5'):
    y_conv, keep_prob = deepnn5(x, output_size=3)
  else:
    y_conv, keep_prob = deepnn(x, output_size=3)

  with tf.name_scope('loss'):
    cross_entropy = tf.nn.softmax_cross_entropy_with_logits(labels=y_,
                                                            logits=y_conv)
  cross_entropy = tf.reduce_mean(cross_entropy)
  tf.summary.scalar("loss", cross_entropy)

  with tf.name_scope('adam_optimizer'):
    train_step = tf.train.AdamOptimizer(1e-5).minimize(cross_entropy)

  with tf.name_scope('accuracy'):
    correct_prediction = tf.equal(tf.argmax(y_conv, 1), tf.argmax(y_, 1))
    correct_prediction = tf.cast(correct_prediction, tf.float32)
  accuracy = tf.reduce_mean(correct_prediction)
  tf.summary.scalar("accuracy", accuracy)

  prediction = tf.argmax(y_conv, 1)

  # Setup Tensorboard
  graph_location = tempfile.mkdtemp()
  print('Saving graph to: %s' % graph_location)
  train_writer = tf.summary.FileWriter(graph_location)
  if ( FLAGS.v == None ):
    train_writer.add_graph(tf.get_default_graph())

  summ = tf.summary.merge_all()
  saver = tf.train.Saver()

  #bryan add to disable GPU because of memory overflow
  if ( FLAGS.n != '13'):
    config = tf.ConfigProto(device_count = {'GPU': 0})
  else:
    config = tf.ConfigProto()
    config.gpu_options.allow_growth = True

  with tf.Session(config=config) as sess:
    sess.run(tf.global_variables_initializer())
    if ( FLAGS.v != None ):
      # Restore variables from disk.
      print("Variables restored using",FLAGS.v)
      # Get activation function from the saved collection
      saver.restore(sess, FLAGS.v)

    num_of_batch = int(num_of_trains / 50)
    print("num of training:",num_of_trains,", batches:", num_of_batch)

    for i in range(num_of_batch):
      batch = mnist.train.next_batch(50)
      if i % 5 == 0:
        [train_accuracy, s] = sess.run([accuracy, summ], feed_dict={x: batch[0], y_: batch[1], keep_prob: 1.0})
        train_writer.add_summary(s, i)
        print('Run %d times, untraining accuracy :%.5f' % (i*50, train_accuracy))   
      train_step.run(feed_dict={x: batch[0], y_: batch[1], keep_prob: 0.5})

    [train_accuracy, s] = sess.run([accuracy, summ], feed_dict={x: mnist.validation.images, y_: mnist.validation.labels, keep_prob: 1.0})
    train_writer.add_summary(s, i)
    print('Run %d times, validation images accuracy :%.5f' % (num_of_trains, train_accuracy))  
    print( "Final verification result", prediction.eval(feed_dict={x: mnist.validation.images, y_: mnist.validation.labels, keep_prob: 1.0}, session=sess))

    map = {0:'Normal', 1:'*Outage', 2:'#Plateau'}
    result = prediction.eval(feed_dict={x: mnist.test.images, y_: mnist.test.labels, keep_prob: 1.0}, session=sess)
    for  i in range(len(test_files) ) :
      print(map[result[i]], '    \t', test_files[i]);
    print( "Test y_conv\n", y_conv.eval(feed_dict={x: mnist.test.images, y_: mnist.test.labels, keep_prob: 1.0}, session=sess))

    # Save the variables to disk.
    msg = 'Do you want to save the trained variables to ./pm_graph_variables'+ FLAGS.n +'.ckpt?'
    shall = input("%s (y/N) " % msg).lower() == 'y'
    if (shall) :
      save_path = saver.save(sess, ('./pm_graph_variables'+ FLAGS.n +'.ckpt'))
      print("Variables saved in file: %s" % save_path)

if __name__ == '__main__':
  parser = argparse.ArgumentParser()
  parser.add_argument('--v', type=str,
                      default= None,
                      help='filename for loading saved variables')
  parser.add_argument('--t', type=str,
                      default= None,
                      help='filename for loading training data')
  parser.add_argument('--d', type=str,
                      default= None,
                      help='directory for loading training data')
  parser.add_argument('--n', type=str,
                      default='5',
                      help='use 5 for cnn5x5, 13 for cnn13x13')
  FLAGS, unparsed = parser.parse_known_args()
  tf.app.run(main=main, argv=[sys.argv[0]] + unparsed)
