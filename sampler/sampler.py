import numpy as np

# this is the minimum value we can exponentiate
MIN = np.log(np.finfo('float64').tiny)


class RejectionSampler(object):

    def __init__(self, propose_func, propose_logpdf, target_logpdf):
        """Initialize the rejection sampler.

        Parameters
        ----------
        propose_func : function
            The proposal distribution, q. Calling this function should
            return one sample, x, from this distribution.

        propose_logpdf : function
            The proposal distribution's log probability density
            function (log-PDF). Calling this function with a sample
            from `propose_func` should return the log probability
            density for the proposal distribution at that location,
            i.e. log(q(x)). This MUST be greater than the log-PDF of
            the target distribution, for any given input (i.e., q(x) >
            p(x) for all x)

        target_logpdf : function
            The target distribution's log probability density function
            (log-PDF). Calling this function with a sample from
            `propose_func` should return the log probability density
            for the target distribution at that location,
            i.e. log(p(x)).

        """

        self.propose_func = propose_func
        self.propose_logpdf = propose_logpdf
        self.target_logpdf = target_logpdf

        self.samples = None

    def draw(self):
        """Sample a single value, x, from the target log probability density
        function (`self.target_logpdf`, or p) using rejection
        sampling.

        """

        while True:
            # 1. Sample a candidate value (x ~ q)
            candidate_sample = self.propose_func()

            # 2. Sample a point uniformly between 0 and the PDF of the
            # proposal distribution (y ~ Uniform(0, q(x)))
            upper = self.propose_logpdf(candidate_sample)
            if upper >= MIN:
                threshold = np.random.uniform(0.0, np.exp(upper))
                log_threshold = np.log(threshold)

                # 3. If this point is less than the target PDF (y <
                # p(x)), then we accept the candidate value;
                # otherwise, we reject it.
                if log_threshold < self.target_logpdf(candidate_sample):
                    break

        return candidate_sample

    def sample(self, n, seed=None):
        """Sample `n` values of x from the target log probability density
        function (`self.target_logpdf`, or p) using rejection
        sampling.

        Parameters
        ----------
        n : int
            The number of samples to draw.
        seed : int (optional)
            If given, seed NumPy's random number generator.

        """

        # seed the random number generator
        if seed is not None:
            np.random.seed(seed)

        # Draw our first sample, so we can determine the size of the
        # array that we need to allocate. If this sample is
        # array-like, then we need to allocate an array with more than
        # one dimension `d`.
        first = self.draw()
        try:
            d = len(first)
        except TypeError:
            # create an empty numpy array with shape (n,)
            self.samples = np.empty(n)
        else:
            # create an empty numpy array with shape (n, d)
            self.samples = np.empty((n, d))

        # Run the sampling loop for the number of requested samples.
        self.samples[0] = first
        for i in xrange(1, n):
            self.samples[i] = self.draw()

        return self.samples

    def plot(self, axes, x_min, x_max, y_max):
        """Plot the proposal distribution (q), target distribution (p), and
        normalized histogram of the samples (x) drawn by
        `self.sample`.

        Parameters
        ----------
        axes : matplotlib axes object
        x_min : number
            Minimum value for the x-axis
        x_max : number
            Maximum value for the x-axis
        y_max : number
            Maximum value for the y-axis

        """

        if self.samples is None:
            raise ValueError("no samples yet, please call `sample` first")
        if self.samples.ndim == 2 and self.samples.shape[1] > 1:
            raise ValueError(
                "visualization for dimensions great than 1 not supported")

        X = np.linspace(x_min, x_max, 1000)
        Yp = np.exp(np.array([self.propose_logpdf(x) for x in X]))
        Yt = np.exp(np.array([self.target_logpdf(x) for x in X]))

        # plot the histogram of samples
        axes.hist(
            self.samples,
            bins=100,
            color='#999999',
            label="samples",
            normed=True,
            edgecolor='#999999')

        # plot the proposal distribution PDF
        axes.plot(
            X, Yp, 'r-',
            linewidth=2,
            label="proposal")

        # plot the target distribution PDF
        axes.plot(
            X, Yt, 'b-',
            linewidth=2,
            label="target")

        axes.legend(loc='upper right')
        axes.set_xlabel("x")
        axes.set_ylabel("p(x)")
        axes.set_xlim(x_min, x_max)
        axes.set_ylim(0, y_max)
