import math
from linghelper.phonetics.representations.amplitude_envelopes import to_envelopes
from linghelper.phonetics.representations.prosody import to_pitch,to_intensity,to_prosody
from linghelper.phonetics.representations.mfcc import to_mfcc
from linghelper.phonetics.representations.mhec import to_mhec
from linghelper.distance.dtw import dtw_distance
from linghelper.distance.dct import dct_distance
from linghelper.distance.xcorr import xcorr_distance

import multiprocessing
from queue import Empty
from functools import partial

import csv
import os
import networkx as nx
import numpy
from scipy.sparse import lil_matrix
import scipy.signal
import pickle
import time
from matplotlib import pyplot as plt

from sklearn.cluster import AffinityPropagation
from sklearn import metrics
from sklearn import manifold
from sklearn.decomposition import PCA

def job_adder(files,token_path,jobs_q):
    mapping = ((x,y,fx,fy,token_path) for x,fx in enumerate(files)
                                    for y,fy in enumerate(files) if y > x)
    m = next(mapping,None)
    while m is not None:
        jobs_q.put(m,timeout = 2)
        if m[1] % 1000 == 0:
            print(m[0],m[1])
        m = next(mapping,None)

def worker(job_q,result_q):
    while True:
        try:
            tup = job_q.get(timeout=1)
        except Empty:
            break
        rep1 = pickle.load(open(os.path.join(tup[4],tup[2]),'rb'))
        rep2 = pickle.load(open(os.path.join(tup[4],tup[3]),'rb'))

        dist = -1 * dtw_distance(
                                rep1['representation'],
                                rep2['representation'])
        if numpy.isinf(dist):
            print(rep1['representation'].shape)
            print(tup[2])
            print(rep2['representation'].shape)
            print(tup[3])
        res = (tup[0],tup[1],dist)

        result_q.put(res)

def results_manager(job_q,result_q,N,files,durations):
    startTime = time.time()
    simMat = numpy.zeros((N,N))

    while True:
        try:
            o = result_q.get(timeout=1)
        except Empty:
            break
        simMat[o[0],o[1]] = o[2]
        simMat[o[1],o[0]] = o[2]
    print(simMat[1:10,1:10])
    print(numpy.min(simMat))

    pickle.dump({'file_names':files,'simMat':simMat,'durations':durations},open('acoustics.network','wb'))
    simMat = numpy.zeros((N,N))
    for i in range(N):
        for j in range(i+1,N):
            dist = numpy.sqrt((durations[i]-durations[j])**2)
            simMat[i,j] = dist
            simMat[j,i] = dist
    pickle.dump({'file_names':files,'simMat':simMat,'durations':durations},open('durations.network','wb'))

def create_sim_mat(token_path,speaker, word):

    nprocs = 5
    files = [x for x in os.listdir(token_path) if speaker in x.split('_') and word in x.split('_')]
    N = len(files)
    if N < 5:
        return False
    print(speaker, word,N)
    durations = [ pickle.load(open(os.path.join(token_path,x),'rb'))['duration'] for x in files]
    #print(len(files))
    job_queue = multiprocessing.Queue(10000)
    result_queue = multiprocessing.Queue()
    jp = multiprocessing.Process(
                target=job_adder,
                args=(files,
                        token_path,
                      job_queue))
    jp.start()
    time.sleep(10)
    procs = []
    rp = multiprocessing.Process(
                target=results_manager,
                args=(job_queue,
                      result_queue,N,files,durations))
    rp.start()
    for i in range(nprocs):
        p = multiprocessing.Process(
                target=worker,
                args=(job_queue,
                      result_queue))
        procs.append(p)
        p.start()
    jp.join()
    for p in procs:
        p.join()
    rp.join()
    return True

def doAffProp():
    loaded = pickle.load(open('output.network','rb'))
    files = loaded['file_names']
    simMat = loaded['simMat']
    af = AffinityPropagation(affinity='precomputed').fit(simMat)
    cluster_centers_indices = af.cluster_centers_indices_
    labels = af.labels_
    print(dir(af))
    print(labels)
    n_clusters_ = len(cluster_centers_indices)

    print('Estimated number of clusters: %d' % n_clusters_)
    #print("Silhouette Coefficient: %0.3f"
    #      % metrics.silhouette_score(simMat, labels, metric='sqeuclidean'))
    import pylab as pl
    from itertools import cycle

    pl.close('all')
    pl.figure(1)
    pl.clf()

    colors = cycle('bgrcmykbgrcmykbgrcmykbgrcmyk')
    for k, col in zip(range(n_clusters_), colors):
        class_members = labels == k
        cluster_center = simMat[cluster_centers_indices[k]]
        pl.plot(simMat[class_members, 0], simMat[class_members, 1], col + '.')
        pl.plot(cluster_center[0], cluster_center[1], 'o', markerfacecolor=col,
                markeredgecolor='k', markersize=14)
        for x in simMat[class_members]:
            pl.plot([cluster_center[0], x[0]], [cluster_center[1], x[1]], col)

    pl.title('Estimated number of clusters: %d' % n_clusters_)
    pl.show()

def doMDS(nettype):
    loaded = pickle.load(open('%s.network' % nettype,'rb'))
    files = loaded['file_names']
    durations = loaded['durations']
    info = [x.split('.')[0].split('_') for x in files]
    simMat = loaded['simMat']
    seed = numpy.random.RandomState(seed=3)
    mds = manifold.MDS(n_components=2, max_iter=3000, eps=1e-9, random_state=seed,
                   dissimilarity="precomputed", n_jobs=4)
    pos = mds.fit(-1 * simMat).embedding_

    clf = PCA(n_components=2)
    pos = clf.fit_transform(pos)

    fig = plt.figure(1)
    ax = plt.axes([0., 0., 1., 1.])

    plt.scatter(pos[:, 0], pos[:, 1], s=20, c='g')


    # Plot the edges
    #a sequence of (*line0*, *line1*, *line2*), where::
    #            linen = (x0, y0), (x1, y1), ... (xm, ym)

    #plt.show()
    pref = -250
    if nettype == 'durations':
        pref = -5
    af = AffinityPropagation(affinity='precomputed',preference=pref).fit(simMat)
    cluster_centers_indices = af.cluster_centers_indices_
    labels = af.labels_
    print(labels)
    try:
        n_clusters_ = len(cluster_centers_indices)
    except TypeError:
        print('Had an issue with AffinityPropagation')
        return

    print('Estimated number of clusters: %d' % n_clusters_)
    #print("Silhouette Coefficient: %0.3f"
    #      % metrics.silhouette_score(simMat, labels, metric='sqeuclidean'))
    import pylab as pl
    from itertools import cycle

    pl.close('all')
    pl.figure(1,figsize=(10,6))
    pl.clf()
    output = []
    colors = cycle('bgrcmykbgrcmykbgrcmykbgrcmyk')
    for k, col in zip(range(n_clusters_), colors):
        class_members = labels == k
        cluster_center = pos[cluster_centers_indices[k]]
        pl.plot(pos[class_members, 0], pos[class_members, 1], col + '.')
        pl.plot(cluster_center[0], cluster_center[1], 'o', markerfacecolor=col,
                markeredgecolor='k', markersize=14)
        for i, x in enumerate(class_members):
            if not x:
                continue
            x = pos[i]
            dist_to_center = simMat[i,cluster_centers_indices[k]]
            duration_dist = durations[i] - durations[cluster_centers_indices[k]]
            output.append(info[i] + [dist_to_center,duration_dist])
            pl.text(x[0], x[1],'  %1.3f' % (durations[i],))
            pl.plot([cluster_center[0], x[0]], [cluster_center[1], x[1]], col)
    with open('%s_output.txt' % nettype,'a') as f:
        writer = csv.writer(f,delimiter='\t', lineterminator='\n')
        #writer.writerow(['Speaker','Dialog','Word','TokenId','DistRatio'])
        for line in output:
            writer.writerow(line)
    speaker = info[0][0]
    word = info[0][2]
    #pl.title('Speaker %s, %s' % (speaker,word))
    if nettype == 'acoustics' and speaker in ('s07','s35') and word in ('time','said','back'):
        #pl.show()
        pl.savefig('%s_%s.pdf' %(speaker,word), bbox_inches='tight')


if __name__ == '__main__':
    GOOD_WORDS = ['back', 'bad', 'badge', 'bag', 'ball', 'bar', 'bare', 'base', 'bash', 'bass', 'bat', 'bath', 'beach', 'bean', 'bear', 'beat',
                 'bed', 'beer', 'bell', 'berth', 'big', 'bike', 'bill', 'birth', 'bitch', 'bite', 'boat', 'bob', 'boil', 'bomb', 'book', 'boom', 'boon',
                 'boss', 'bought', 'bout', 'bowl', 'buck', 'bum', 'burn', 'bus', 'bush', 'cab', 'cad', 'cake', 'calf', 'call', 'came', 'cap',
                 'car', 'care', 'case', 'cash', 'cat', 'catch', 'caught', 'cave', 'cell', 'chain', 'chair', 'chat', 'cheap', 'cheat', 'check',
                 'cheer', 'cheese', 'chess', 'chick', 'chief', 'chill', 'choice', 'choose', 'chose', 'church', 'coach', 'code', 'coke',
                 'comb', 'come', 'cone', 'cook', 'cool', 'cop', 'cope', 'corps', 'couch', 'cough', 'cub', 'cuff', 'cup', 'curl', 'curve', 'cut',
                 'dab', 'dad', 'dare', 'date', 'dawn', 'dead', 'deal', 'dear', 'death', 'debt', 'deck', 'deed', 'deep', 'deer', 'dime', 'dirt',
                 'doc', 'dodge', 'dog', 'dole', 'doll', 'doom', 'door', 'dot', 'doubt', 'duck', 'dug', 'dumb', 'face', 'fad', 'fade', 'fail',
                 'fair', 'faith', 'fake', 'fall', 'fame', 'fan', 'far', 'fat', 'faze', 'fear', 'fed', 'feed', 'feet', 'fell', 'fight', 'file', 'fill', 'fine',
                 'firm', 'fish', 'fit', 'fog', 'folk', 'food', 'fool', 'foot', 'fore', 'fought', 'fun', 'fuss', 'gain', 'game', 'gap', 'gas',
                 'gate', 'gave', 'gear', 'geese', 'gig', 'girl', 'give', 'goal', 'gone', 'good', 'goose', 'gum', 'gun', 'gut', 'gym', 'hail', 'hair',
                 'hall', 'ham', 'hang', 'hash', 'hat', 'hate', 'head', 'hear', 'heard', 'heat', 'height', 'hick', 'hid', 'hide', 'hill', 'hip', 'hit',
                 'hole', 'home', 'hood', 'hook', 'hop', 'hope', 'hot', 'house', 'hug', 'hum', 'hung', 'hurt', 'jab', 'jail', 'jam', 'jazz', 'jerk',
                 'jet', 'job', 'jog', 'join', 'joke', 'judge', 'june', 'keep', 'kick', 'kid', 'kill', 'king', 'kiss', 'knife', 'knit', 'knob', 'knock',
                 'known', 'lack', 'lag', 'laid', 'lake', 'lame', 'lane', 'lash', 'latch', 'late', 'laugh', 'lawn', 'league', 'leak', 'lean', 'learn',
                 'lease', 'leash', 'leave', 'led', 'leg', 'let', 'lid', 'life', 'light', 'line', 'load', 'loan', 'lock', 'lodge', 'lone', 'long', 'look',
                 'loose', 'lose', 'loss', 'loud', 'love', 'luck', 'mad', 'made', 'maid', 'mail', 'main', 'make', 'male', 'mall',
                 'map', 'mass', 'mat', 'match', 'math', 'meal', 'meat', 'meet', 'men', 'mess', 'met', 'mid', 'mike', 'mile', 'mill',
                 'miss', 'mock', 'moon', 'mouth', 'move', 'mud', 'nail', 'name', 'nap', 'neat', 'neck', 'need', 'nerve', 'net', 'news',
                 'nice', 'niche', 'niece', 'night', 'noise', 'noon', 'nose', 'notch', 'note', 'noun', 'nurse', 'nut', 'pace', 'pack', 'page',
                 'paid', 'pain', 'pair', 'pal', 'pass', 'pat', 'path', 'pawn', 'peace', 'peak', 'pearl', 'peek', 'peer', 'pen', 'pet', 'phase',
                 'phone', 'pick', 'piece', 'pile', 'pill', 'pine', 'pipe', 'pit', 'pool', 'poor', 'pop', 'pope', 'pot', 'pour', 'puck', 'push',
                 'put', 'race', 'rage', 'rail', 'rain', 'raise', 'ran', 'rash', 'rat', 'rate', 'rave', 'reach', 'rear', 'red', 'reef', 'reel',
                 'rice', 'rich', 'ride', 'ring', 'rise', 'road', 'roam', 'rob', 'rock', 'rode', 'role', 'roll', 'roof', 'room', 'rose', 'rough',
                 'rub', 'rude', 'rule', 'run', 'rush', 'sack', 'sad', 'safe', 'said', 'sake', 'sale', 'sang', 'sat', 'save', 'scene', 'search',
                 'seat', 'seen', 'sell', 'serve', 'set', 'sewn', 'shake', 'shame', 'shape', 'share', 'shave', 'shed', 'sheep', 'sheer', 'sheet',
                 'shell', 'ship', 'shirt', 'shock', 'shoot', 'shop', 'shot', 'shown', 'shun', 'shut', 'sick', 'side', 'sight', 'sign', 'sin', 'sing',
                 'sit', 'site', 'size', 'soap', 'son', 'song', 'soon', 'soul', 'soup', 'south', 'suit', 'sung', 'tab', 'tag', 'tail', 'take', 'talk',
                 'tap', 'tape', 'taught', 'teach', 'team', 'tease', 'teeth', 'tell', 'term', 'theme', 'thick', 'thief', 'thing', 'thought', 'tiff',
                 'tight', 'time', 'tip', 'tongue', 'took', 'tool', 'top', 'tore', 'toss', 'touch', 'tough', 'tour', 'town', 'tub', 'tube',
                 'tune', 'turn', 'type', 'use', 'van', 'vet', 'vice', 'voice', 'vote', 'wade', 'wage', 'wait', 'wake', 'walk', 'wall', 'war',
                 'wash', 'watch', 'wear', 'web', 'week', 'weight', 'wet', 'whack', 'wheat', 'wheel', 'whim', 'whine', 'whip', 'white',
                 'whole', 'wick', 'wide', 'wife', 'win', 'wine', 'wing', 'wise', 'wish', 'woke', 'womb', 'wood', 'word', 'wore', 'work',
                 'worse', 'wreck', 'wright', 'write', 'wrong', 'wrote', 'wrought', 'year', 'yell', 'young', 'youth', 'zip']


    with open('acoustics_output.txt','w') as f:
        pass

    with open('durations_output.txt','w') as f:
        pass

    speakers = []

    for s in range(1,41):
        for w in GOOD_WORDS:
            if s != 7:
                continue
            if w != 'time':
                continue
            speaker = 's%02d' % s
            mdscheck = create_sim_mat(r'C:\Users\michael\Documents\Data\TestAll',speaker, w)
            if mdscheck:
                for n in ['durations','acoustics']:
                    doMDS(n)
    #doAffProp()

