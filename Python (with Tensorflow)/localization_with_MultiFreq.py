# source localization using nn
# written by Haiqiang Niu 01/20/2017
# ==============================================================================
# written by Dr. Haiqiang Niu, Fall 2016

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import tensorflow as tf
import numpy as np
import load_data_nhq_si
import matplotlib.pyplot as plt
from os import listdir
from os.path import isfile, join

Data_set = 'DataSet01'  ## test data 1 or 2
flags = tf.app.flags
FLAGS = flags.FLAGS
flags.DEFINE_boolean('fake_data', False, 'If true, uses fake data '
                     'for unit testing.')
#flags.DEFINE_boolean('train', True, 'If true, training')
flags.DEFINE_integer('max_steps', 2000, 'Number of steps to run trainer.')
flags.DEFINE_float('learning_rate', 0.01, 'Initial learning rate.')
flags.DEFINE_float('dropout', 0.5, 'Keep probability for training dropout.')
flags.DEFINE_string('data_dir', '../data/'+Data_set, 'Directory for storing data')

def train_and_prediction(FileName):
  # Import data
  source_data = load_data_nhq_si.read_data_sets(FLAGS.data_dir, FileName, fake_data=FLAGS.fake_data)
  n_input = 7200  # 30 frequencies
  # n_input = 240  # single frequency (for 15 elements)
  n_output = 149
  n_hidden = 1024
  n_mini_batch = 128
  sess = tf.InteractiveSession()

  # Create a multilayer model.

  # Input placeholders
  with tf.name_scope('input'):
    x = tf.placeholder(tf.float32, [None, n_input], name='x-input')
    y_ = tf.placeholder(tf.float32, [None, n_output], name='y-input')
    keep_prob = tf.placeholder(tf.float32)

  # We can't initialize these variables to 0 - the network will get stuck.
  def weight_variable(shape):
    """Create a weight variable with appropriate initialization."""
    initial = tf.truncated_normal(shape, stddev=0.02)
    return tf.Variable(initial)

  def bias_variable(shape):
    """Create a bias variable with appropriate initialization."""
    initial = tf.constant(0.005, shape=shape)
    return tf.Variable(initial)

  def init_weights(shape):
    return tf.Variable(tf.random_normal(shape, stddev=0.01))
        
  def nn_layer(input_tensor, input_dim, output_dim, layer_name, act=tf.nn.relu):
    """Reusable code for making a simple neural net layer.

    It does a matrix multiply, bias add, and then uses relu to nonlinearize.
    It also sets up name scoping so that the resultant graph is easy to read, and
    adds a number of summary ops.
    """
    # Adding a name scope ensures logical grouping of the layers in the graph.
    with tf.name_scope(layer_name):
      # This Variable will hold the state of the weights for the layer
      with tf.name_scope('weights'):
        weights = weight_variable([input_dim, output_dim])
      with tf.name_scope('biases'):
        biases = bias_variable([output_dim])
      with tf.name_scope('Wx_plus_b'):
        preactivate = tf.matmul(input_tensor, weights) + biases
      if act:
        activations = act(preactivate, 'activation')
      else:
        activations = preactivate
      return activations

  hidden1 = nn_layer(x, n_input, n_hidden, 'layer1', act=tf.nn.sigmoid)
  dropped = tf.nn.dropout(hidden1, keep_prob)
  y = nn_layer(dropped, n_hidden, n_output, 'layer2', act=False)

  with tf.name_scope('cross_entropy'):
    with tf.name_scope('total'):
      cross_entropy = tf.reduce_mean(tf.nn.softmax_cross_entropy_with_logits(logits=y, labels=y_))

  with tf.name_scope('train'):
    train_step = tf.train.AdamOptimizer(
        FLAGS.learning_rate).minimize(cross_entropy)

  with tf.name_scope('accuracy'):
    with tf.name_scope('correct_prediction'):
      correct_prediction = tf.equal(tf.argmax(y, 1), tf.argmax(y_, 1))
    with tf.name_scope('accuracy'):
      accuracy = tf.reduce_mean(tf.cast(correct_prediction, tf.float32))

  tf.initialize_all_variables().run()

  def feed_dict(train):
    """Make a TensorFlow feed_dict: maps data onto Tensor placeholders."""
    if train or FLAGS.fake_data:
      xs, ys = source_data.train.next_batch(n_mini_batch, fake_data=FLAGS.fake_data)
      k = FLAGS.dropout
    else:
      xs, ys = source_data.test.images, source_data.test.labels
      k = 1.0
    return {x: xs, y_: ys, keep_prob: k}

  print('------------training process------------')
  for i in range(FLAGS.max_steps):
    if i % 100 == 0:  # Record summaries and training or test-set accuracy
      acc = sess.run(accuracy, feed_dict=feed_dict(True))
      print('Accuracy at step %s: %s' % (i, acc))
    else: # Record train set summarieis, and train
      _ = sess.run(train_step, feed_dict=feed_dict(True))

  print('---------------predicting---------------')
#  predict_out = sess.run(tf.nn.softmax(y), feed_dict=feed_dict(False))
  predictions = sess.run(y, feed_dict=feed_dict(False))
  idx = (tf.argmax(predictions, 1)).eval()
  rng = np.loadtxt(FLAGS.data_dir + '/Mapping_range_labels.txt')
      #rng = np.loadtxt('./data/Range_simulation.txt')
  rng2 = rng[idx]
  print('predictions: \n  %s' % (rng2))

  rng_true = np.loadtxt(FLAGS.data_dir + '/test_Ranges.txt')
  np.savetxt('predictions_'+ FileName[:-15] +'predictions',rng2)
  print(Data_set)


#  b1 = rng_true*0.9
#  b2 = rng_true*1.1
      
#  fig=plt.figure(figsize=(3.0,2.5))
# ax = fig.add_subplot(111)

# xl1 = np.arange(0.,120.)[:, np.newaxis]
#  xl2 = xl1[::-1]
# b3 = b2[::-1]
#  coor = np.c_[np.r_[xl1,xl2], np.r_[b1,b3]]
      
#  patches = []
#  polygon = Polygon(coor, True)
#  patches.append(polygon)
#  p = PatchCollection(patches, cmap=cm.jet, alpha=0.3)
#  ax.add_collection(p)
      
  plt.plot(rng2,'bo',markersize=3)
  plt.plot(rng_true,'r',linewidth=1.5)
      
  plt.xlabel('Signal index',fontname='Helvetica',fontsize=10)
  plt.ylabel('Range (km)',fontname='Helvetica',fontsize=10)
  plt.tick_params(axis='both', which='major', labelsize=9)
  plt.tick_params(axis='both', which='minor', labelsize=9)

#  pos1 = ax.get_position() # get the original position
#  pos2 = [pos1.x0 + 0.05, pos1.y0 + 0.065,  pos1.width, pos1.height-0.01]
#  ax.set_position(pos2) # set a new position
#      plt.text(100, 3.0, '(d)')

  plt.show()
#      fig.savefig('Fig10d.eps', dpi=300)
#      fig.savefig('Fig10d.pdf', dpi=300)
def main(_):
  onlyfiles = [f for f in listdir(FLAGS.data_dir+'/train_input') if isfile(join(FLAGS.data_dir+'/train_input', f))]
  #print(onlyfiles[2])
  #exit()
  for FileName in onlyfiles:
    if FileName.endswith(".txt"):
      print(FileName)
      train_and_prediction(FileName)

if __name__ == '__main__':
  tf.app.run()
