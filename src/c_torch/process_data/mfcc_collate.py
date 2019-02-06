# imports
import torch
from torch.nn import ConstantPad1d

"""
Function mfcc_collate

    pads each mfcc in batch to longest seq in that batch

"""


def mfcc_collate(batch, pad_val=0.0):
    r"""Puts each data field into a tensor with outer dimension batch size"""

    if isinstance(batch[0], torch.Tensor):

        # max seq length
        seq_len = [b.size(0) for b in batch]
        max_seq = max(seq_len)

        # pad to max length
        batch = [
            ConstantPad1d((0, int(max_seq - b.size(0))), value=pad_val)(b.transpose(0, 1)) for b in batch
        ]

        batch = torch.stack(batch, 0)

        # (B, f, T) -> (B, T, f)
        batch = batch.permute(0, 2, 1)

        # ret tensor batch && original seq lengths

        return batch, seq_len

    elif isinstance(batch[0], tuple):

        # split features and keys

        utt_keys = [
            b[0] for b in batch
        ]

        utt_feats = [
            b[1] for b in batch
        ]

        # batch feat
        batch, seq_len = mfcc_collate(utt_feats)

        return utt_keys, batch, seq_len

    else:
        err_msg = "mfcc collate requires batch contain tensors or [key, tensor] pairs, found {}"
        raise TypeError((
            err_msg.format(type(batch[0]))
        ))

    return
