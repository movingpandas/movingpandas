def split_list(a, n):  # source: https://stackoverflow.com/a/2135920/449624
    k, m = divmod(len(a), n)
    return (a[i * k + min(i, m) : (i + 1) * k + min(i + 1, m)] for i in range(n))
