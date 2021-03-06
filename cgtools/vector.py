import numpy as np
from fastmath import inv3, matvec


__all__ = [
    'normalized', 'veclen', 'sq_veclen', 'scaled', 'dot', 'project',
    'homogenize', 'dehomogenize', 'hom', 'dehom', 'ensure_dim', 'hom3', 'hom4',
    'transform',
    'convert_3x4_to_4x4', 'to_4x4', 'assemble_4x4', 'assemble_3x4', 'inv_3x4',
]

ARR = np.asanyarray

def normalized(vectors):
    """ normalize vector(s) such that ||vectors|| == 1 """
    vectors = ARR(vectors)
    lengths = veclen(vectors)
    return vectors / lengths[..., np.newaxis]

def veclen(vectors):
    """ calculate euclidean norm of a vector or an array of vectors 
        when an nd-array is given, then the norm is computed about the last dimension
    """
    return np.sqrt(np.sum(ARR(vectors)**2, axis=-1))

def sq_veclen(vectors):
    """ calculate squared euclidean norm of a vector or an array of vectors 
        when an nd-array is given, then the norm is computed about the last dimension
    """
    vectors = ARR(vectors)
    return np.sum(vectors**2, axis=vectors.ndim-1)

def scaled(vectors, scale):
    """ scales vectors such that ||vectors|| == scale """
    return normalized(vectors) * ARR(scale)[..., np.newaxis]

def dot(v, u):
    """ pairwise dot product of 2 vector arrays, 
    essentially the same as [sum(vv*uu) for vv,uu in zip(v,u)], 
    that is, pairwise application of the inner product
    >>> dot([1, 0], [0, 1])
    0
    >>> dot([1, 1], [2, 3])
    5
    >>> dot([[1, 0], [1, 1]], [[0, 1], [2, 3]]).tolist()
    [0, 5]
    """
    return np.sum(ARR(u)*ARR(v), axis=-1)

def project(v, u):
    """ project v onto u """
    u_norm = normalized(u)
    return (dot(v, u_norm)[..., np.newaxis] * u_norm)

def homogenize(v, value=1):
    """ returns v as homogeneous vectors by inserting one more element into the last axis 
    the parameter value defines which value to insert (meaningful values would be 0 and 1) 
    >>> homogenize([1, 2, 3]).tolist()
    [1, 2, 3, 1]
    >>> homogenize([1, 2, 3], 9).tolist()
    [1, 2, 3, 9]
    >>> homogenize([[1, 2], [3, 4]]).tolist()
    [[1, 2, 1], [3, 4, 1]]
    >>> homogenize([[1, 2], [3, 4]], 99).tolist()
    [[1, 2, 99], [3, 4, 99]]
    >>> homogenize([[1, 2], [3, 4]], [33, 99]).tolist()
    [[1, 2, 33], [3, 4, 99]]
    """
    v = ARR(v)
    if hasattr(value, '__len__'):
        return np.append(v, ARR(value).reshape(v.shape[:-1] + (1,)), axis=-1)
    else:
        return np.insert(v, v.shape[-1], np.array(value, v.dtype), axis=-1)

# just some handy aliases
hom = homogenize

def dehomogenize(a):
    """ makes homogeneous vectors inhomogenious by dividing by the last element in the last axis 
    >>> dehomogenize([1, 2, 4, 2]).tolist()
    [0.5, 1.0, 2.0]
    >>> dehomogenize([[1, 2], [4, 4]]).tolist()
    [[0.5], [1.0]]
    """
    a = np.asfarray(a)
    return a[...,:-1] / a[...,np.newaxis,-1]

# just some handy aliases
dehom = dehomogenize

def ensure_dim(a, dim, value=1):
    """
    checks if an array of vectors has dimension dim, and if not,
    adds one dimension with values set to value (default 1)
    """
    cdim = a.shape[-1]
    if cdim == dim - 1:
        return homogenize(a, value=value)
    elif cdim == dim:
        return a
    else:
        raise ValueError('vectors had %d dimensions, but expected %d or %d' % (cdim, dim-1, dim))

def hom4(a, value=1):
    return ensure_dim(a, 4, value)

def hom3(a, value=1):
    return ensure_dim(a, 3, value)

def transform(v, M, w=1):
    """
    transforms vectors in v with the matrix M
    if matrix M has one more dimension then the vectors
    this will be done by homogenizing the vectors
    (with the last dimension filled with w) and
    then applying the transformation
    """
    if M.shape[-1] == v.shape[-1] + 1:
        v1 = matvec(M, hom(v))
        if v1.shape[-1] == v.shape[-1] + 1:
            v1 = dehom(v1)
        return v1
    else:
        return matvec(M, v)

def toskewsym(v):
    assert v.shape == (3,)
    return np.array([[0, -v[2], v[1]],
                     [v[2], 0, -v[0]],
                     [-v[1], v[0], 0]])

def convert_3x4_to_4x4(matrices, new_row=[0, 0, 0, 1]):
    """
    Turn a 3x4 matrix or an array of 3x4 matrices into 4x4 matrices by appending the <new_row>.
    >>> A = np.zeros((3, 4))
    >>> convert_3x4_to_4x4(A).shape
    (4, 4)
    >>> convert_3x4_to_4x4(A)[3].tolist()
    [0.0, 0.0, 0.0, 1.0]
    >>> many_A = np.random.random((10, 20, 3, 4))
    >>> many_A_4x4 = convert_3x4_to_4x4(many_A)
    >>> many_A_4x4.shape
    (10, 20, 4, 4)
    >>> many_A_4x4[2, 1, 3].tolist()
    [0.0, 0.0, 0.0, 1.0]
    >>> np.all(many_A_4x4[:, :, :3, :] == many_A)
    True
    """
    assert matrices.shape[-1] == 4 and matrices.shape[-2] == 3
    return np.insert(matrices, 3, new_row, axis=-2)

to_4x4 = convert_3x4_to_4x4


def assemble_3x4(rotations, translations):
    """
    Given one (or more) 3x3 matrices and one (or more) 3d vectors,
    create an array of 3x4 matrices

    >>> rots = np.arange(9).reshape(3, 3)
    >>> ts = np.array([99, 88, 77])
    >>> assemble_3x4(rots, ts)
    array([[ 0,  1,  2, 99],
           [ 3,  4,  5, 88],
           [ 6,  7,  8, 77]])

    >>> rots = np.random.random((100, 3, 3))
    >>> ts = np.random.random((100, 3))
    >>> Ms = assemble_3x4(rots, ts)
    >>> Ms.shape
    (100, 3, 4)
    >>> np.all(Ms[:, :, :3] == rots)
    True
    >>> np.all(Ms[:, :, 3] == ts)
    True
    """
    if rotations.ndim not in [2, 3] or rotations.shape[-2:] != (3, 3):
        raise ValueError("requires rotations argument to be one or more 3x3 matrices, so the shape should be either (3, 3) or (n, 3, 3)")
    if translations.ndim not in [1, 2] or translations.shape[-1] != 3:
        raise ValueError("requires translations argument to be one or more 3d vectors, so the shape should be either (3,) or (n, 3)")
    if rotations.ndim == 2 and translations.ndim == 1:
        # single translation, single rotation -> output single matrix
        return np.column_stack((rotations, translations))
    else:
        if rotations.ndim == 2:
            rotations = rotations[np.newaxis]
        if translations.ndim == 1:
            translations = translations[np.newaxis]
        translations = translations[:, :, np.newaxis]
        return np.concatenate((rotations, translations), axis=-1)


def assemble_4x4(rotations, translations, new_row=[0, 0, 0, 1]):
    """
    Given one (or more) 3x3 matrices and one (or more) 3d vectors,
    create an array of 4x4 matrices

    >>> rots = np.arange(9).reshape(3, 3)
    >>> ts = np.array([99, 88, 77])
    >>> assemble_4x4(rots, ts)
    array([[ 0,  1,  2, 99],
           [ 3,  4,  5, 88],
           [ 6,  7,  8, 77],
           [ 0,  0,  0,  1]])

    >>> rots = np.random.random((100, 3, 3))
    >>> ts = np.random.random((100, 3))
    >>> Ms = assemble_4x4(rots, ts)
    >>> Ms.shape
    (100, 4, 4)
    >>> np.all(Ms[:, :3, :3] == rots)
    True
    >>> np.all(Ms[:, :3, 3] == ts)
    True
    >>> np.all(Ms[:, 3, :] == np.array([0, 0, 0, 1]))
    True
    """
    return to_4x4(assemble_3x4(rotations, translations), new_row=new_row)


def inv_3x4(matrices):
    """Given one (or more) 3x4 matrices, converts matrices into common
    transformation matrices by appending a row (0, 0, 0, 1), then
    inverts those matrices. Since the inverse will also have the
    same last row, the returned matrices are also 3x4

    >>> X = np.random.random((3, 4))
    >>> X_4x4 = to_4x4(X)
    >>> np.allclose(inv_3x4(X), np.linalg.inv(X_4x4)[:3, :])
    True
    """
    if matrices.ndim not in [2, 3] or matrices.shape[-2:] != (3, 4):
        raise ValueError("requires matrices argument to be one or more 3x4 matrices, so the shape should be either (3, 4) or (n, 3, 4)")
    R_inv = inv3(matrices[..., :3, :3]) # "rotation" part (upper left 3x3 block)
    t_inv = matvec(R_inv, -matrices[..., :3, 3]) # "translation" part
    return assemble_3x4(R_inv, t_inv)

