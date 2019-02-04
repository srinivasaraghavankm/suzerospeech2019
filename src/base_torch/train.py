"""
Pytorch Training Script

"""

# imports
import os
import time
import torch
import torch.nn as nn
import argparse as arg
import src.modules as mymod
import torch.optim as optimizer
from torch.optim import lr_scheduler
from .process_data import MfccDataset
from tensorboardX import SummaryWriter
from torch.utils.data import DataLoader


# ----------------------------------------------------------------------------------------------------------------------
# Argument Parser
# ----------------------------------------------------------------------------------------------------------------------

# create Argument Parser
parser = arg.ArgumentParser(
    prog='Train: STE Binary Compression Systems:',
    description='ste binary training script'
)

parser.add_argument(
    '--sys',
    '-s',
    metavar='SYSTEM',
    type=str,
    required=True,
    choices=['MfccAuto'],
    help='MFCC Compression System'
)

parser.add_argument(
    '--epochs',
    '-e',
    metavar='EPOCHS',
    type=int,
    default=100,
    help='Number of epochs'
)

parser.add_argument(
    '--learn_rate',
    '-lr',
    metavar='LEARN_RATE',
    type=float,
    default=0.0001,
    help='Learning rate'
)

parser.add_argument(
    '--gamma',
    '-g',
    metavar='GAMMA',
    type=float,
    default=0.1,
    help='Learning rate decay rate'
)

parser.add_argument(
    '--log',
    '-l',
    metavar='LOG_DIR',
    type=str,
    default='./',
    help='Log directory'
)

parser.add_argument(
    '--train',
    '-td',
    metavar='TRAIN_DIR',
    type=str,
    default='./',
    help='Training data directory'
)

parser.add_argument(
    '--save',
    '-sv',
    metavar='SAVE_LOC',
    type=str,
    default='./',
    help='Model save location'
)

parser.add_argument(
    '--batch_size',
    '-bs',
    metavar='BATCH_SIZE',
    type=int,
    default=3,
    help='Batch size'
)

parser.add_argument(
    '--bottleneck_depth',
    '-bnd',
    metavar='BND',
    type=int,
    default=3,
    help='Bottleneck depth'
)

parser.add_argument(
    '--verbose',
    '-v',
    action='store_true'
)

parser.add_argument(
    '--checkpoint',
    '-chkp',
    action='store_true'
)

args = parser.parse_args()

# ----------------------------------------------------------------------------------------------------------------------
# TRAINING LOOP
# ----------------------------------------------------------------------------------------------------------------------

sys = None

# GPU || CPU
device = torch.device(
    "cuda:0" if torch.cuda.is_available() else "cpu"
)

if args.sys == 'MfccAuto':
    # def network
    sys = mymod.MfccAuto(
        bnd=args.bottleneck_depth
    )


# model -> device
sys.to(device)

# MSE Loss function
criterion = nn.MSELoss()

# Adam Optimizer
opt = optimizer.Adam(sys.parameters(), args.learn_rate)

# MultiStep scheduler
scheduler = lr_scheduler.MultiStepLR(
    optimizer=opt,
    milestones=[30, 80, 140],
    gamma=args.gamma
)

# check train, log and save locations
log_loc = os.path.expanduser(args.log)

if not os.path.isdir(log_loc):
    raise NotADirectoryError('Log directory d.n.e')

save_loc = os.path.expanduser(args.save)

if not os.path.isdir(save_loc):
    raise NotADirectoryError('Save directory d.n.e')

train_dir = os.path.expanduser(args.train)

if not os.path.isdir(train_dir):
    raise NotADirectoryError('Train directory d.n.e')

# Mfcc Dataset

train_dataset = MfccDataset(
    mfcc_dir=train_dir
)

valid_dataset = MfccDataset(
    mfcc_dir=valid_dir
)

# Mfcc DataLoader

train_data_loader = DataLoader(
    dataset=train_dataset,
    batch_size=args.batch_size,
    shuffle=True,
    num_workers=2
)

valid_data_loader = MfccDataset(
    mfcc_dir=valid_dir
)

# dataLoader dict
dataLoaders = {
    'train': train_data_loader,
    'valid': valid_data_loader
}


# start epoch, time previously elapsed, best MSE
t_prev = 0.0
best_loss = 10e8
current_epoch = 1

# def state file
state_file = ''.join([save_loc, '/', sys.name, '_chkp.pt'])

if os.path.isfile(state_file):

    print("Continue Training from m.r.c : ")

    # load checkpoint
    chkp = torch.load(state_file)

    # load previous train time
    t_prev = chkp['time']

    # load previous epoch
    current_epoch = chkp['epoch']

    # load previous loss
    best_loss = chkp['best_loss']

    # load model weights
    sys.load_state_dict(chkp['sys'])

    # load optimizer states
    opt.load_state_dict(chkp['optimizer'])

    # load scheduler states
    scheduler.load_state_dict(chkp['scheduler'])

else:
    print("Training New System : ")

# writer for loss logging
writer = None

if args.verbose:
    writer = SummaryWriter(log_loc)

# start timing
train_start = time.time()

for epoch in range(current_epoch, args.epochs + 1, 1):

    # start epoch
    if args.verbose:
        print("Epoch {}/{}".format(epoch, args.epochs))
        print("--------------------------------------")

    epoch_start = time.time()

    for phase in ['train', 'valid']:

        # running MSE loss
        run_loss = 0.0

        if phase is 'train':
            sys.train(True)
            # step scheduler
            scheduler.step()

        elif phase is 'valid':
            sys.train(False)

        i = 0
        for i, data in enumerate(dataLoaders[phase], 0):

            # data -> device
            data = data.to(device)

            # [0, 1] -> [-1, 1]
            data = (data - 0.5) / 0.5

            # zero model gradients
            opt.zero_grad()

            # forward
            out = sys(inpt)

            # loss
            loss = criterion(out, target=data)

            # running loss
            run_loss += loss.item()

            if phase == 'train':
                # backward & optimise
                loss.backward()
                opt.step()

            del loss

        # epoch loss averaged over batch number
        epoch_loss = run_loss / (i + 1)

        if args.verbose:
            print("Phase: {} Loss : {}".format(phase, epoch_loss))
            writer.add_scalar('{}/loss'.format(phase), epoch_loss, epoch)

        # save best system
        if phase is 'valid' and epoch_loss < best_loss:
            best_loss = epoch_loss
            fn = ''.join([save_loc, '/', sys.name, '.pt'])
            torch.save(sys.state_dict(), fn)

    # end of epoch
    epoch_time = (time.time() - epoch_start) / 60

    if args.verbose:
        print("Epoch time: {} min".format(epoch_time))
        print("-------------------------------------")

    if args.checkpoint:
        # save checkpoint
        chkp = {
            'epoch': epoch + 1,
            'sys': sys.state_dict(),
            'optimizer': opt.state_dict(),
            'scheduler': scheduler.state_dict(),
            'best_loss': best_loss,
            'time': time.time() - train_start + t_prev
        }
        torch.save(chkp, state_file)

# end of Training
train_time = (time.time() - train_start + t_prev) / 60

if args.verbose:
    print('Total Training Time {} min'.format(train_time))
    print('Best Loss : {}'.format(best_loss))
    print('FIN TRAINING')

# close writer
writer.close()
