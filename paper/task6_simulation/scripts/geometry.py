"""Deterministic population geometry; no test or random experiment is run.

The exact executed-source excerpts and hashes are in inputs/geometry_sources.json.
Python translation is self-contained for rebuilding the delivered archive.
"""
from pathlib import Path
import csv
import json
import sys
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt


def design(u, s):
    """Exact _fourier_design convention: 1, sin1, cos1, ..., sin10, cos10."""
    B = np.ones((len(u), s))
    for k in range(1, s):
        trig = np.sin if k % 2 else np.cos
        B[:, k] = np.sqrt(2)*trig(2*np.pi*((k+1)//2)*u)
    return B


def kernels(u):
    phi5 = design(u, 6)[:, 1:]
    m1 = (phi5*((200/441)*np.arange(1., 6.)**-2)) @ phi5.T
    m2 = np.minimum.outer(u, u)/(63/64)
    phi20 = design(u, 21)[:, 1:]
    a = design(np.array([3/8]), 21)[0, 1:]/20
    f = phi20 @ a
    return {'M1': (m1, m1), 'M2': (m2, m2),
            'coherent': (phi20 @ phi20.T/20, np.outer(f, f))}


def build(root):
    root = Path(root).resolve()
    out, data = root/'figures/main', root/'data'
    out.mkdir(parents=True, exist_ok=True)
    data.mkdir(parents=True, exist_ok=True)
    sys.path.insert(0, str(root/'scripts/qa'))
    from audit_panel_alignment import require_matplotlib_panel_alignment
    u = np.arange(64)/64
    geometries = kernels(u)
    rows, payload, effects = [], {'grid': u}, {}
    for model, (K0, delta) in geometries.items():
        assert np.isclose(np.abs(delta).max(), 1)
        payload[model+'_K0'] = K0
        payload[model+'_Kdelta'] = delta
        for s in (5, 11, 21):
            B = design(u, s)
            P = B.T/64
            S = P @ (K0+.0025*np.eye(64)) @ P.T
            A = .30 * P @ delta @ P.T
            # Independent channels under H0: V_ab=0 even if S_rh != 0.
            d = np.sqrt(800)*A/np.sqrt(np.outer(np.diag(S), np.diag(S)))
            Q = np.linalg.qr(B, mode='reduced')[0]
            reconstructed = B @ (P @ delta @ P.T) @ B.T
            energy = (np.linalg.norm(Q @ (Q.T @ delta @ Q) @ Q.T)/np.linalg.norm(delta))**2
            rows.append(dict(model=model, n=800, tau=.30, s=s,
                signal_peak=float(np.abs(delta).max()),
                weighted_frobenius=float(np.linalg.norm(delta)/64),
                max_abs_standardized_effect=float(np.abs(d).max()),
                reconstruction_peak_ratio=float(np.abs(reconstructed).max()/np.abs(delta).max()),
                orthogonal_energy_ratio=float(energy),
                source_type='executed_source_snapshot'))
            for key, val in {'P': P, 'S': S, 'A': A, 'd': d}.items():
                payload[f'{model}_s{s}_{key}'] = val
            if s == 21:
                effects[model] = d
    with (data/'geometry_diagnostics.csv').open('w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    np.savez_compressed(data/'geometry_arrays.npz', **payload)
    (data/'geometry_definitions.json').write_text(json.dumps(dict(
        n=800, tau=.30, M=64, noise_variance=.0025,
        projection='P=B.T/64; B=(1,sin1,cos1,...,sin10,cos10), sqrt(2) normalization',
        standardized_effect='sqrt(n)*A[r,h]/sqrt(S[r,r]*S[h,h]); j!=k; null cross covariance=0',
        weighted_frobenius='norm(Kdelta,F)/M; one channel edge; no tau or edge multiplicity',
        reconstruction_peak_ratio='max(abs(B@(P@Kdelta@P.T)@B.T))/max(abs(Kdelta)) on original grid',
        orthogonal_energy_ratio='norm(Q@(Q.T@Kdelta@Q)@Q.T,F)^2/norm(Kdelta,F)^2; Q=qr(B)',
        basis_order=['1']+[v+str(h) for h in range(1,11) for v in ('sin','cos')],
        uncertainty='none: exact population quantities; no Monte Carlo'), indent=2), encoding='utf-8')
    plt.rcParams.update({'font.family':'sans-serif', 'font.sans-serif':['Arial','DejaVu Sans'], 'font.size':8,
        'axes.titlesize':9, 'axes.labelsize':8, 'xtick.labelsize':7,
        'ytick.labelsize':7, 'svg.fonttype':'none', 'pdf.fonttype':42,
        'axes.linewidth':.6})
    fig, ax = plt.subplots(2,3,figsize=(7.2,5.15), gridspec_kw={'wspace':.38,'hspace':.48})
    fig.subplots_adjust(left=.08,right=.85,bottom=.16,top=.93)
    lim = max(np.abs(d).max() for d in effects.values())
    basis_ticks = [0,2,6,10,14,20]
    basis_labels = ['1','c1','c3','c5','c7','c10']
    for c, (model, (_,delta)) in enumerate(geometries.items()):
        im0 = ax[0,c].imshow(delta,origin='lower',extent=[-.5/64,63.5/64,-.5/64,63.5/64],
            interpolation='nearest',cmap='RdBu_r',vmin=-1,vmax=1,aspect='auto')
        ax[0,c].set(title=model,xlabel='Time t',ylabel='Time u' if c == 0 else '')
        ax[0,c].set_xticks([0,.5,63/64],['0','0.5','63/64'])
        ax[0,c].set_yticks([0,.5,63/64],['0','0.5','63/64'])
        ax[0,c].set_xlim(0,63/64)
        ax[0,c].set_ylim(0,63/64)
        im1 = ax[1,c].imshow(effects[model],origin='lower',cmap='RdBu_r',
            vmin=-lim,vmax=lim,interpolation='nearest',aspect='auto')
        ax[1,c].set(xlabel='Basis direction h',ylabel='Basis direction r' if c == 0 else '',
            title='max |d| = '+f'{np.abs(effects[model]).max():.2f}')
        ax[1,c].set_xticks(basis_ticks,basis_labels,rotation=60,ha='right',rotation_mode='anchor')
        ax[1,c].set_yticks(basis_ticks,basis_labels)
    for label, axis in zip('abcdef',ax.flat):
        axis.text(-.22,1.04,label,transform=axis.transAxes,fontweight='bold',fontsize=10)
    pos0, pos1 = ax[0,2].get_position(), ax[1,2].get_position()
    cax0 = fig.add_axes([.89,pos0.y0,.016,pos0.height])
    cax1 = fig.add_axes([.89,pos1.y0,.016,pos1.height])
    fig.colorbar(im0,cax=cax0,ticks=[-1,0,1],label='Signal kernel')
    fig.colorbar(im1,cax=cax1,ticks=[-lim,0,lim],label='Standardized coefficient effect d')
    fig.text(.08,.015,'s = sin; c = cos; basis order: 1, s1, c1, s2, c2, ..., s10, c10',fontsize=7)
    stem = out/'fig04_signal_geometry'
    require_matplotlib_panel_alignment(fig, axes=list(ax.flat), panel_ids=list('abcdef'),
        json_out=str(data/'geometry_alignment.json'), strict=True)
    fig.savefig(str(stem)+'.pdf')
    fig.savefig(str(stem)+'.svg')
    fig.savefig(str(stem)+'.png',dpi=600)
    plt.close(fig)
    return rows


if __name__ == '__main__':
    build(Path(__file__).resolve().parents[1])
