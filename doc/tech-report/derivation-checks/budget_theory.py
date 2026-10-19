"""The corrected atomic-budget trim of the report (eq-ch09-conservation-trim), written independently of atm2d.

For each element in the order given: X = max(0, sum_n A_n - B), A_n = a_n c_n over non-fixed species with a_n > 0;
hogs H = {n : A_n > mean share}; c_n <- max(0, c_n - (A_n / sum_H A) X / a_n) for n in H. No floor on sum_H A.
"""
import torch


def trim(conc, atom_counts, fixed_mask, budget):
    c = conc.clone()
    for elem, counts in atom_counts.items():
        mask = (counts > 0) & (~fixed_mask)
        if not mask.any():
            continue
        a = counts.view(1, 1, -1).to(c.dtype)
        A = c * a * mask
        excess = (A.sum(-1, keepdim=True) - budget[elem]).clamp(min=0.0)
        hog = A > A.sum(-1, keepdim=True) / mask.sum()
        Ah = torch.where(hog, A, torch.zeros_like(A))
        tot = Ah.sum(-1, keepdim=True)
        frac = torch.where(tot > 0, Ah / torch.where(tot > 0, tot, torch.ones_like(tot)), torch.zeros_like(Ah))
        dc = frac * excess / a.clamp(min=1.0)
        c = torch.where(hog & (excess > 0), (c - dc).clamp(min=0.0), c)
    return c
