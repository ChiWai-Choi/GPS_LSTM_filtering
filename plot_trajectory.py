import tensorflow as tf
import scipy as sp
from scipy.integrate import cumtrapz
from matplotlib import pyplot as plt

#%% Constants
N_TIME = 200
N_HIDDEN = 20
N_INPUT = 2
N_OUTPUT = 2
LR_BASE = 5e-3
BATCH_SIZE = 4
ITRS = 800

#%% Generate a sample
t = sp.linspace(0,10,N_TIME)
def gen_sample(f, vnoise, xnoise):
    true_vx = f(t)
    true_x  = cumtrapz(true_vx,t)
    true_x  = sp.hstack([[0],true_x])
    
    noisy_vx = f(t+sp.random.rand(*t.shape)*xnoise)+sp.random.rand(*t.shape)*vnoise
    noisy_x  = true_x+sp.random.rand(*t.shape)*xnoise
    noisy_x  = noisy_x
    
    return sp.stack([true_x,true_vx]).T, sp.stack([noisy_x,noisy_vx]).T

#%%
y_batch, x_batch = list(zip(*[gen_sample(f, 0.2, 0.2) for f in [sp.sin,lambda x: sp.cos(x)+1,lambda x: 0.5*x/max(t),lambda x: 0.25*(sp.sin(x)+sp.cos(x)**2)]]))
batch_y= sp.stack(y_batch)
batch_x= sp.stack(x_batch)
print(batch_y.shape,batch_x.shape)

#%%
g1 = tf.Graph()
with g1.as_default():
    #input series placeholder
    x=tf.placeholder(dtype=tf.float32,shape=[None,N_TIME,N_INPUT])
    #input label placeholder
    y=tf.placeholder(dtype=tf.float32,shape=[None,N_TIME,N_INPUT])
    lr=tf.placeholder(dtype=tf.float32,shape=())
    
    
    
    #defining the network as two stacked layers of LSTMs
    lstm_layers=[tf.nn.rnn_cell.BasicLSTMCell(size,forget_bias=0.4) for size in [N_HIDDEN]]
    lstm_cell = tf.nn.rnn_cell.MultiRNNCell(lstm_layers)
    
    #Unroll the rnns
    outputs, state = tf.nn.dynamic_rnn(lstm_cell,x,dtype=tf.float32)
    print('Outputs:', outputs.shape)
    predictions = tf.layers.Dense(N_HIDDEN, activation=tf.nn.relu)(outputs)
    predictions = tf.layers.Dense(N_HIDDEN, activation=tf.nn.relu)(predictions)
    predictions = tf.layers.Dense(N_OUTPUT, activation=None)(predictions)
    print('Predictions:', predictions.shape)
    
    #loss_function
    loss= tf.reduce_mean((y-predictions)**2)
    #optimization
    opt=tf.train.AdamOptimizer(learning_rate=lr).minimize(loss)
    
    #initialize variables
    init=tf.global_variables_initializer()

#%%


with tf.Session(graph=g1) as sess:
    sess.run(init)
    itr=1
    learning_rate = LR_BASE
    while itr<ITRS:

        sess.run(opt, feed_dict={x: batch_x, y: batch_y, lr:learning_rate})
        
        if itr %20==0:
            learning_rate *= 0.91
            los,out=sess.run([loss,predictions],feed_dict={x:batch_x,y:batch_y,lr:learning_rate})
            print("For iter %i, learning rate %3.6f"%(itr, learning_rate))
            print("Loss ",los)
            print("__________________")

        itr=itr+1
        

#%% Plot the fit    
plt.figure(figsize=(14,7))
for batch_idx in range(BATCH_SIZE):
    out_x = sp.squeeze(out[batch_idx,:,0])
    out_vx = sp.squeeze(out[batch_idx,:,1])
    noisy_x = batch_x[batch_idx,:,0]
    noisy_vx = batch_x[batch_idx,:,1]
    true_x = batch_y[batch_idx,:,0]
    true_vx = batch_y[batch_idx,:,1]
    
    plt.subplot(20+(BATCH_SIZE)*100 + batch_idx*2+1)
    plt.title('Location x')
    plt.plot(t,noisy_x,label='measured')
    plt.plot(t,true_x,label='true')
    plt.plot(t,out_x,label='LSTM')
    plt.grid(which='both')
    plt.ylabel('x[m]')
    plt.xlabel('time[s]')
    plt.legend()
    
    plt.subplot(20+(BATCH_SIZE)*100 + batch_idx*2+1)
    plt.title('Velocity x')
    plt.plot(t,noisy_vx,label='measured')
    plt.plot(t,true_vx,label='true')
    plt.plot(t,out_vx,label='LSTM')
    plt.ylabel('vx[m/s]')
    plt.xlabel('time[s]')
    plt.grid(which='both')
    plt.legend()
    
