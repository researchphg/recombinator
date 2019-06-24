import math
import numba
import numpy as np
from types import ModuleType
import typing as tp


from .utilities import \
    _verify_shape_of_bootstrap_input_data_and_get_dimensions, \
    _grab_sub_samples_from_indices


def _verify_iid_bootstrap_arguments(
                x: np.ndarray,
                replications: int,
                replace: bool,
                sub_sample_length: tp.Optional[int] = None) -> None:
    T, k = _verify_shape_of_bootstrap_input_data_and_get_dimensions(x)

    if not sub_sample_length:
        sub_sample_length = T

    if replications <= 0:
        raise ValueError('The argument replications must be strictly positive.')

    if sub_sample_length <= 0:
        raise ValueError('The argument sub_sample_length must be strictly '
                         'positive.')

    if sub_sample_length > T:
        if not replace:
            raise ValueError(
                'The argument sub_sample_length must not exceed the size of '
                'the data.')


# ------------------------------------------------------------------------------
# Non-Balanced Bootstrap via Numba Loops
# - Separate Functions for One-Dimensional and Multi-Dimensional Data
@numba.njit
def _iid_bootstrap_loop_one_dimensional(
        x: np.ndarray,
        replications: int,
        sub_sample_length: int,
        replace: bool) -> np.ndarray:
    n = len(x)

    # allocate memory for resampled data
    x_star = np.empty((replications, sub_sample_length), dtype=x.dtype)

    if replace:
        for b in range(replications):
            # generate random integer indices from 0 to n-1
            u = np.random.randint(low=0, high=n, size=(sub_sample_length,))

            # x-star sample simulation
            x_star[b, :] = x[u]
    else:
        for b in range(replications):
            x_star[b, :] = np.random.choice(x, size=(sub_sample_length,),
                                            replace=replace)

    return x_star


def iid_bootstrap_via_loop_one_dimensional(
        x: np.ndarray,
        replications: int,
        sub_sample_length: tp.Optional[int] = None,
        replace: bool = True) -> np.ndarray:
    """
    This function performs an i.i.d. non-balanced bootstrap using loops in Numba
    for one-dimensional input data.

    Args:
        x: (n,) dimensional NumPy array of input data
        replications: the number of samples to generate
        sub_sample_length: the length of the bootstrapped samples to generate
        replace: whether to repeat the same observation in a given sub-sample

    Returns:
        a (replications, n) dimensional NumPy array
    """

    # dimensions of original data
    n, k = _verify_shape_of_bootstrap_input_data_and_get_dimensions(x)

    if k > 1:
        raise ValueError(
            'This function only supports one-dimensional input data.')

    if not sub_sample_length:
        sub_sample_length = n

    _verify_iid_bootstrap_arguments(
        x,
        replications=replications,
        replace=replace,
        sub_sample_length=sub_sample_length)

    x_star = _iid_bootstrap_loop_one_dimensional(
                            x=x,
                            replications=replications,
                            sub_sample_length=sub_sample_length,
                            replace=replace)

    assert x_star.shape == (replications, n)

    return x_star


@numba.njit
def _iid_bootstrap_loop_multi_dimensional(
        x: np.ndarray,
        n: int,
        k: int,
        replications: int,
        sub_sample_length: int,
        replace: bool) -> np.ndarray:
    # allocate memory for samples
    x_star = np.empty((replications, sub_sample_length, k), dtype=x.dtype)

    if replace:
        # loop over replications
        for b in range(replications):
            # generate random integer indices from 0 to n-1
            u = np.random.randint(low=0, high=n, size=(sub_sample_length,))

            x_star[b, :, :] = x[u, :]
    else:
        # loop over replications
        for b in range(replications):
            # generate random integer indices from 0 to n-1
            u = np.random.choice(np.arange(n), size=(sub_sample_length,),
                                 replace=replace)

            x_star[b, :, :] = x[u, :]

    return x_star


def iid_bootstrap_via_loop_multi_dimensional(
        x: np.ndarray,
        replications: int,
        sub_sample_length: tp.Optional[int] = None,
        replace: bool = True) -> np.ndarray:
    """
    This function performs an i.i.d. non-balanced bootstrap using loops in Numba
    for multi-dimensional input data.

    Args:
        x: (n, k) dimensional NumPy array of input data
        replications: the number of samples to generate
        sub_sample_length: the length of the bootstrapped samples to generate
        replace: whether to repeat the same observation in a given sub-sample

    Returns:
        a (replications, n, k) dimensional NumPy array
    """

    # dimensions of original data
    n, k = _verify_shape_of_bootstrap_input_data_and_get_dimensions(x)

    if k == 1:
        raise ValueError('This function does not support one-dimensional data.')

    if not sub_sample_length:
        sub_sample_length = n

    _verify_iid_bootstrap_arguments(
        x,
        replications=replications,
        replace=replace,
        sub_sample_length=sub_sample_length)

    # simulate samples
    x_star = _iid_bootstrap_loop_multi_dimensional(
                            x=x,
                            n=n,
                            k=k,
                            replications=replications,
                            sub_sample_length=sub_sample_length,
                            replace=replace)

    assert x_star.shape == (replications, sub_sample_length, k)

    return x_star


def iid_bootstrap_via_loop(x: np.ndarray,
                           replications: int,
                           sub_sample_length: tp.Optional[int] = None) \
        -> np.ndarray:
    """
    This function performs an i.i.d. non-balanced bootstrap using loops in
    Numba.

    Args:
        x: (n,) or (n, k) dimensional NumPy array of input data
        replications: the number of samples to generate
        sub_sample_length: the length of the bootstrapped samples to generate

    Returns:
        a (replications, n) or (replications, n, k) dimensional NumPy array
    """

    # dimensions of original data
    n, k = _verify_shape_of_bootstrap_input_data_and_get_dimensions(x)

    if not sub_sample_length:
        sub_sample_length = n

    _verify_iid_bootstrap_arguments(
        x,
        replications=replications,
        replace=True,
        sub_sample_length=sub_sample_length)

    if k == 1:
        return iid_bootstrap_via_loop_one_dimensional(
                                x=x,
                                replications=replications,
                                sub_sample_length=sub_sample_length)

    else:
        return iid_bootstrap_via_loop_multi_dimensional(
                                x=x,
                                replications=replications,
                                sub_sample_length=sub_sample_length)


# ------------------------------------------------------------------------------
# non-balanced bootstrap via choice
def iid_bootstrap_via_choice(x: np.ndarray,
                             replications: int,
                             sub_sample_length: tp.Optional[int] = None,
                             choice=np.random.choice) \
        -> np.ndarray:
    """
    This function performs an i.i.d. non-balanced bootstrap via
    NumPy's random choice function.

    Args:
        x: (n,) dimensional NumPy array of input data
        replications: the number of samples to generate
        sub_sample_length: the length of the bootstrapped samples to generate
        choice: a function compatible with numpy.random.choice

    Returns:
        a (replications, n) dimensional NumPy array
    """

    # dimensions of original data
    n, k = _verify_shape_of_bootstrap_input_data_and_get_dimensions(x)

    if k > 1:
        raise ValueError('iid bootstrap via choice does not support '
                         'multi-dimensional input data')

    if not sub_sample_length:
        sub_sample_length = n

    _verify_iid_bootstrap_arguments(
        x,
        replications=replications,
        replace=True,
        sub_sample_length=sub_sample_length)

    # generate random integer indices from 0 to n-1
    x_star = choice(x, size=(replications, sub_sample_length), replace=True)

    assert x_star.shape == (replications, sub_sample_length)

    return x_star


# ------------------------------------------------------------------------------
# non-balanced bootstrap vectorized
def iid_bootstrap_vectorized(x: np.ndarray,
                             replications: int,
                             sub_sample_length: tp.Optional[int] = None,
                             randint=np.random.randint) \
        -> np.ndarray:
    """
    This function performs an i.i.d. non-balanced bootstrap via
    a vectorized implementation.

    Args:
        x: (n,) or (n, k) dimensional NumPy array of input data
        replications: the number of samples to generate
        sub_sample_length: the length of the bootstrapped samples to generate
        randint: a function to generate random integers

    Returns:
        a (replications, n) or (replications, n, k) dimensional NumPy array
    """

    # dimensions of original data
    n, k = _verify_shape_of_bootstrap_input_data_and_get_dimensions(x)

    if not sub_sample_length:
        sub_sample_length = n

    _verify_iid_bootstrap_arguments(
        x,
        replications=replications,
        replace=True,
        sub_sample_length=sub_sample_length)

    # generate random integer indices from 0 to n-1
    u = randint(low=0, high=n, size=(replications, sub_sample_length))

    # grab samples
    x_star = _grab_sub_samples_from_indices(x, u)

    if k == 1:
        assert x_star.shape == (replications, sub_sample_length)
    else:
        assert x_star.shape == (replications, sub_sample_length, k)

    return x_star


# ------------------------------------------------------------------------------
# Non-Balanced Bootstrap with Antithetic Resampling - Vectorized Implementation
def iid_bootstrap_with_antithetic_resampling(
                        x: np.ndarray,
                        replications: int,
                        sub_sample_length: tp.Optional[int] = None,
                        num_pack=np,
                        randint=np.random.randint) \
        -> np.ndarray:
    """
    This function performs an i.i.d. non-balanced bootstrap with antithetic
    sampling.

    Args:
        x: (n,) dimensional NumPy array of input data
        replications: the number of samples to generate
        sub_sample_length: the length of the bootstrapped samples to generate
        num_pack: a module compatible with NumPy (function uses vstack and sort)
        randint: a function to generate random integers

    Returns:
        a (replications, n) dimensional NumPy array
    """

    # dimensions of original data
    n, k = _verify_shape_of_bootstrap_input_data_and_get_dimensions(x)

    if k > 1:
        raise ValueError('Antithetic resampling is not supported for '
                         'multi-dimensional data.')

    if not sub_sample_length:
        sub_sample_length = n

    _verify_iid_bootstrap_arguments(x,
                                    replications=replications,
                                    replace=True,
                                    sub_sample_length=sub_sample_length)

    # sort original sample
    x = num_pack.sort(x)

    # generate random integer indices from 0 to n-1
    u1 = randint(low=0,
                 high=n,
                 size=(math.ceil(replications / 2),
                       sub_sample_length))
    u2 = n - u1 - 1
    u = num_pack.vstack((u1, u2[:math.floor(replications / 2), :]))
    # print(u.shape)

    # grab samples
    x_star = _grab_sub_samples_from_indices(x, u)

    # print(x_star.shape)

    assert x_star.shape == (replications, sub_sample_length)

    return x_star


# ------------------------------------------------------------------------------
# Non-Balanced Bootstrap with Antithetic Resampling - Numba Loop Implementation
@numba.njit
def _iid_bootstrap(x: np.ndarray,
                   replications: int,
                   sub_sample_length: int,
                   replace: bool) -> np.ndarray:
    n = len(x)

    # allocate memory for indices
    u = np.empty((replications, sub_sample_length), dtype=np.int32)

    if replace:
        for b in range(replications):
            # generate random integer indices from 0 to n-1
            u[b, :] = np.random.randint(low=0,
                                        high=n,
                                        size=(sub_sample_length,))

    else:
        for b in range(replications):
            u[b, :] = np.random.choice(np.arange(n),
                                       size=(sub_sample_length,),
                                       replace=replace)

    return u


def iid_bootstrap(x: np.ndarray,
                  replications: int,
                  sub_sample_length: tp.Optional[int] = None,
                  replace: bool = True,
                  antithetic: bool = False) -> np.ndarray:
    """
    This function performs an i.i.d. non-balanced bootstrap using loops in Numba
    for one-dimensional input data.

    Args:
        x: (n,) dimensional NumPy array of input data
        replications: the number of samples to generate
        sub_sample_length: the length of the bootstrapped samples to generate
        replace: whether to repeat the same observation in a given sub-sample
        antithetic: whether to use antithetic sampling

    Returns:
        a (replications, n) dimensional NumPy array
    """

    # dimensions of original data
    n, k = _verify_shape_of_bootstrap_input_data_and_get_dimensions(x)

    if not sub_sample_length:
        sub_sample_length = n

    if k > 1 and antithetic:
        raise ValueError('Antithetic resampling is not supported for '
                         'multi-dimensional data.')

    _verify_iid_bootstrap_arguments(
        x,
        replications=replications,
        replace=replace,
        sub_sample_length=sub_sample_length)

    if antithetic:
        x = np.sort(x)

        u1 = _iid_bootstrap(x=x,
                            replications=math.ceil(replications / 2),
                            sub_sample_length=sub_sample_length,
                            replace=replace)

        u2 = n - u1 - 1
        u = np.vstack((u1, u2[:math.floor(replications / 2), :]))
    else:
        u = _iid_bootstrap(x=x,
                           replications=replications,
                           sub_sample_length=sub_sample_length,
                           replace=replace)

    x_star = _grab_sub_samples_from_indices(x, u)

    if k == 1:
        assert x_star.shape == (replications, sub_sample_length)
    else:
        assert x_star.shape == (replications, sub_sample_length, k)

    return x_star


# ------------------------------------------------------------------------------
# Balanced Bootstrap
def iid_balanced_bootstrap(x: np.ndarray,
                           replications: int,
                           num_pack=np,
                           permutation=np.random.permutation,
                           shuffle=np.random.shuffle) -> np.ndarray:
    """
    This function performs an i.i.d. balanced bootstrap. That means
    each value of the original sample appears 'replication' times
    in all of the bootstrapped samples altogether.

    Args:
        x: (n, k) dimensional NumPy array of input data
        replications: the number of samples to generate
        num_pack: a module compatible with NumPy (function uses vstack and sort)
        permutation: a function compatible with numpy.random.permutation
        shuffle: a function compatible with numpy.random.shuffle

    Returns:
        a (replications, n) or (replications, n, k) dimensional NumPy array
    """

    # dimensions of original data
    n, k = _verify_shape_of_bootstrap_input_data_and_get_dimensions(x)

    _verify_iid_bootstrap_arguments(x,
                                    replications=replications,
                                    replace=True,
                                    sub_sample_length=n)

    # simulate sub-samples
    if k > 1:
        u = (permutation(num_pack
                         .arange(n)
                         .repeat(replications))
             .reshape(replications, n))
        x_star = _grab_sub_samples_from_indices(x, u)
        assert x_star.shape == (replications, n, k)
    else:
        y = num_pack.repeat(x, replications)
        shuffle(y)
        x_star = y.reshape(replications, n)

        assert x_star.shape == (replications, n)

    return x_star
