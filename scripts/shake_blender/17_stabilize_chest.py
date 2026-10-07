from kinematics import *
p=ROOT/'工具腳本'/'motion_fit.npz';d=dict(np.load(p));a=d['angles'].copy();tr=d['translation'];ch=idx['Spine_05'];ne=idx['neck']
for f in range(len(a)):
 old=mats(a[f],tr[f]);desired=Rotation.from_matrix(old[ch,:3,:3]).as_euler('xyz');desired[1]*=.30;Rdesired=Rotation.from_euler('xyz',desired).as_matrix();parent=old[parents[ch],:3,:3];a[f,ch]=Rotation.from_matrix(parent.T@Rdesired).as_euler('xyz');new=mats(a[f],tr[f]);a[f,ne]=Rotation.from_matrix(new[ch,:3,:3].T@old[ne,:3,:3]).as_euler('xyz')
a[-1]=a[0];d['angles']=a;d['S']=np.array([mats(a[f],tr[f]) for f in range(len(a))]);np.savez(p,**d);print('Chest stabilization: preserve head orientation, brace chest between planted forelegs')
