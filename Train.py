import torch
import socket
import time
import argparse
import torch.optim as optim
import torch.backends.cudnn as cudnn
import torch.optim.lr_scheduler as lrs
from torch.utils.data import DataLoader
from model import mynet
from torch.autograd import Variable
from data import get_training_set


# Training settings
parser = argparse.ArgumentParser(description='PyTorch LPUIE-Net')
parser.add_argument('--device', type=str, default='cuda:0')
parser.add_argument('--batchSize', type=int, default=8, help='training batch size')
parser.add_argument('--nEpochs', type=int, default=1000, help='number of epochs to train for')
parser.add_argument('--snapshots', type=int, default=2, help='Snapshots')
parser.add_argument('--start_iter', type=int, default=1, help='Starting Epoch')
parser.add_argument('--lr', type=float, default=1e-4, help='Learning Rate. Default=1e-4')
parser.add_argument('--data_dir', type=str, default='dataset/UIEBD/train')
parser.add_argument('--label_train_dataset', type=str, default='label')
parser.add_argument('--data_train_dataset', type=str, default='image')
parser.add_argument('--patch_size', type=int, default=256, help='Size of cropped image')
parser.add_argument('--save_folder', default='weights/', help='Location to save checkpoint models')
parser.add_argument('--gpu_mode', type=bool, default=True)
parser.add_argument('--threads', type=int, default=2, help='number of threads for data loader to use')
parser.add_argument('--decay', type=int, default='10000', help='learning rate decay type')
parser.add_argument('--gamma', type=float, default=0.3, help='learning rate decay factor for step decay')
parser.add_argument('--seed', type=int, default=123, help='random seed to use. Default=123')
parser.add_argument('--data_augmentation', type=bool, default=True)


opt = parser.parse_args()
device = torch.device(opt.device)
hostname = str(socket.gethostname())
cudnn.benchmark = True
print(opt)


def train(epoch):
    epoch_loss = 0
    model.train()
    for iteration, batch in enumerate(training_data_loader, 1):
        input, target = Variable(batch[0]), Variable(batch[1])
        if cuda:
            input = input.to(device)
            target = target.to(device)
        t0 = time.time()
        model.forward(input, target, training=True)
        loss = model.elbo(target)
        optimizer.zero_grad()

        loss.backward()
        epoch_loss += loss.item()
        optimizer.step()
        t1 = time.time()

        total_iterations = len(training_data_loader)

        print(
            "===> Epoch[{}]({}/{}): Loss: {:.4f} || Learning rate: lr={} || Timer: {:.4f} sec.".format(epoch, iteration,
                                                                                                       total_iterations,
                                                                                                       loss.item(),
                                                                                                       optimizer.param_groups[
                                                                                                           0]['lr'],
                                                                                                       (t1 - t0)))
    print("===> Epoch {} Complete: Avg.Loss: {:.4f}".format(epoch, epoch_loss / total_iterations))
    avg_loss = epoch_loss / total_iterations
    return avg_loss


def checkpoint(epoch):
    model_out_path = opt.save_folder + "epoch_{}.pth".format(epoch)
    torch.save(model.state_dict(), model_out_path)
    print("Checkpoint saved to {}".format(model_out_path))


cuda = opt.gpu_mode
if cuda and not torch.cuda.is_available():
    raise Exception("No GPU found, please run without --cuda")

torch.manual_seed(opt.seed)
if cuda:
    torch.cuda.manual_seed(opt.seed)

print('===> Loading datasets')

train_set = get_training_set(opt.data_dir, opt.label_train_dataset, opt.data_train_dataset, opt.patch_size,
                             opt.data_augmentation)
training_data_loader = DataLoader(dataset=train_set, num_workers=0, batch_size=opt.batchSize, shuffle=True)

model = mynet(opt)

print('---------- Networks architecture -------------')
# print_network(model)
# print('----------------------------------------------')

optimizer = optim.Adam(model.parameters(), lr=opt.lr, betas=(0.9, 0.999), eps=1e-8)

milestones = []
for i in range(1, opt.nEpochs + 1):
    if i % opt.decay == 0:
        milestones.append(i)

scheduler = lrs.MultiStepLR(optimizer, milestones, opt.gamma)

for epoch in range(opt.start_iter, opt.nEpochs + 1):

    train(epoch)
    scheduler.step()

    if (epoch + 1) % opt.snapshots == 0:
        checkpoint(epoch)




