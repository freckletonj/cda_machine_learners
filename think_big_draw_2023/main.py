#!.venv/bin/python

'''.
An MNIST Generator
This was created in a live coding session for the CdA Machine Learners Group
* NOTE: in it's current state, we flipped the inputs and outputs, so it generates mnist images from one-hot vectors.
* NOTE: you'll have to rewrite the dataloader code a bit since it relies on a local dependency. Consider using: https://pytorch.org/vision/main/generated/torchvision.datasets.MNIST.html
'''


import numpy as np
import torch as th
import matplotlib.pyplot as plt
import torch.nn as nn
from torch import einsum
import torchvision
from torchvision.datasets import MNIST
import matplotlib.pyplot as plt

import torch, sys, time

SEED = 0
torch.random.manual_seed(SEED)
np.random.seed(SEED)


##################################################
# PARAMETERS

LR = 5e-3
BATCH_SIZE = 100
DEVICE = 'cuda' if len(sys.argv) <= 1 else sys.argv[1]


##################################################
# DATA

data_path = 'data'

def onehot(i, size):
    out = torch.zeros(size)
    out[i] = 1
    return out

try:
    test_dl
except:
    transform = torchvision.transforms.ToTensor()
    train_ds_pre = MNIST(data_path, train=True, transform=transform, download=True)
    train_ds = []
    for x, i in train_ds_pre:
        train_ds.append((x.flatten(), onehot(i, 10)))
    train_dl = torch.utils.data.DataLoader(train_ds, batch_size=BATCH_SIZE, shuffle=True)

    test_ds_pre = MNIST(data_path, train=False, transform=transform, download=True)
    test_ds = []
    for x, i in test_ds_pre:
        test_ds.append((x.flatten(), onehot(i, 10)))
    test_dl = torch.utils.data.DataLoader(test_ds, batch_size=BATCH_SIZE, shuffle=True)


##################################################
# ARCHITECTURE


class Spy(nn.Module):
    def __init__(self):
        super(Spy, self).__init__()
        self.tensor = None

    def forward(self, x):
        self.tensor = x
        return x


class Model(nn.Module):
    def __init__(self):
        super(Model, self).__init__()
        IMG_SIZE = 28
        self.spy = Spy() # Captures middle layers
        self.w = nn.Sequential(
            nn.Linear(IMG_SIZE*IMG_SIZE, 128),
            # nn.Tanh(),
            # nn.Linear(128, 128),
            nn.ReLU(),
            nn.Dropout(0.2),
            self.spy,
            nn.Linear(128, 10),
            nn.Softmax(dim=1),
        )

    def forward(self, x):
        return self.w(x)

##################################################
# TRAINING

def train(dataloader, model, loss_fn, optimizer):
    size = len(dataloader.dataset)
    model.train()
    for batch, (X, y) in enumerate(dataloader):
        X, y = X.to(DEVICE), y.to(DEVICE)

        # Forward Pass
        pred = model(X)
        loss = loss_fn(pred, y)

        # Backprop
        optimizer.zero_grad()
        loss.backward()
        optimizer.step()

        if batch % 100 == 0:
            loss, current = loss.item(), batch * len(X)
            print(f'loss: {loss:>7f} [{current:>5d}/{size:>5d}]')

def test(dataloader, model, loss_fn):
    size = len(dataloader.dataset)
    num_batches = len(dataloader)
    model.eval()
    test_loss, correct = 0, 0
    with torch.no_grad():
        for X, y in dataloader:
            X, y = X.to(DEVICE), y.to(DEVICE)
            pred = model(X)
            test_loss += loss_fn(pred, y).item()
            correct += (pred.argmax(dim=1) == y.argmax(dim=1)).sum().item()
    test_loss /= num_batches
    correct /= size
    print(f'Test Error: \nAccuracy: {(100*correct):>0.1f}%, Avg loss: {test_loss:>8f} \n')


##################################################
# BOMBS AWAY

model = Model().to(DEVICE)
loss_fn = nn.MSELoss()
optimizer = torch.optim.AdamW(model.parameters(), lr=LR)

epochs = 5
for t in range(epochs):
    print(f'Epoch {t+1}\n------------------------------')
    train(train_dl, model, loss_fn, optimizer)
    test(test_dl, model, loss_fn)
print('Trained.')


# for i in range(10):
#     n = onehot(i, 10).to('cuda')
#     img = model(n.unsqueeze(0)).reshape((28, 28))
#     plt.subplot(4, 4, i+1)
#     plt.imshow(img.detach().cpu().numpy())
# plt.show()


##################################################
##################################################

import numpy as np
import cv2, math, random
from queue import Queue, Empty
from threading import Thread

#create a 512x512 black image
nn_img = np.zeros((1008,256,3), np.uint8)
draw = np.zeros((1008,1008,3), np.uint8)
que = Queue()


def image_to_array(img, size=28):
    # Convert image to array
    img = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    img = cv2.resize(img, (size, size))
    img = cv2.GaussianBlur(img, (5, 5), 0)
    #img = cv2.bitwise_not(img)
    #img = img / 255.0
    #img = img.reshape(1, size, size, 1)

    ret = []
    for i in range(size):
        for j in range(size):
            ret.append(math.ceil(img[i][j]))

    #cv2.imshow("Before NN", img)

    return ret

def drawCircles(img, ary, x_offset=0, show_labels=True):
    #img = img.copy()
    if not isinstance( ary, list ):
        ary = ary.tolist()
    # Calc some dimensions
    init = 40
    height = img.shape[0]
    step = (height - init * 2) / len(ary)

    #draw a circle
    x = math.floor(img.shape[1] / 2) + x_offset
    y = step / 2 + init / 2
    for i, t in enumerate(ary):
        color = (0, math.floor(t * 255), math.floor((1 - t) * 255))
        center = (x, math.floor(y))

        #filled circle
        cv2.circle(img, center, math.floor(step * 0.3), color, -1)
        if show_labels:
            # non filled circle
            cv2.circle(img, center, math.floor(step * 0.3), (255,0,0), 3)
            # DRaw text
            cv2.putText(img, f"{i}", (math.floor(center[0] + step / 2), center[1]),
                        cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2, cv2.LINE_AA)

        y += step

    return img

def threadWorker(queue):
    while True:
        queue.get()

        vizualizeNN()

        # Clear out the queue so we block correctly
        try:
            while queue.get(False):
                pass
        except Empty:
            pass


def vizualizeNN():
    # Convert the image into a pixel array
    pix_ary = image_to_array(draw)

    # Convert to pixels to tensor
    tens = torch.tensor(pix_ary).to(DEVICE).unsqueeze(0) / 255

    # What does this do?
    # tens += torch.randn_like(tens) / 1000
    # Run the NN, and get the output
    ary = model(tens)[0]
    hidden = model.spy.tensor[0]

    # Draw the middle nodes, With a scale?
    drawCircles(nn_img, hidden, -60, False)

    # Draw the image
    drawCircles(nn_img, pix_ary, -100, False)

    #for layer in model.parameters():
    #    if len(layer.shape) == 1 and layer.shape[0] == 128:
    #        print(layer[29])
    #        print(layer)

    # Draw the NN
    drawCircles(nn_img, ary, 20)


def draw_mouse(event, x, y, flags, param):
    if event == cv2.EVENT_RBUTTONDOWN or event == cv2.EVENT_LBUTTONDBLCLK:
        (w,h,d) = draw.shape
        cv2.rectangle(draw, (0,0), (w,h), (0,0,0), -1)

        ary = torch.zeros(10)# [random.random() for i in range(10)]
        drawCircles( nn_img, ary, 20)

    if event == cv2.EVENT_MOUSEMOVE and flags == cv2.EVENT_FLAG_LBUTTON:
        cv2.circle(draw, (x, y), 25, (255, 255, 255), -1)

        # This will trigger a refresh
        que.put(True, block=False)
        # visulizeNN()


# Setup the threads
t1 = Thread(target=threadWorker, args=(que,))
t1.start()

# First draw
model.eval()
ary = torch.zeros(10)# [random.random() for i in range(10)]
drawCircles( nn_img, ary, 20)

cv2.namedWindow(winname="Draw a number")
cv2.setMouseCallback("Draw a number", draw_mouse)

while True:
    cv2.imshow("Draw a number", draw)
    cv2.imshow("AI Output", nn_img)
    if cv2.waitKey(10) & 0xFF == 27:
        break

    time.sleep(0.1)

cv2.destroyAllWindows()
