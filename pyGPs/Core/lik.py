#================================================================================
#    Marion Neumann [marion dot neumann at uni-bonn dot de]
#    Daniel Marthaler [marthaler at ge dot com]
#    Shan Huang [shan dot huang at iais dot fraunhofer dot de]
#    Kristian Kersting [kristian dot kersting at cs dot tu-dortmund dot de]
#
#    This file is part of pyGPs.
#    The software package is released under the BSD 2-Clause (FreeBSD) License.
#
#    Copyright (c) by
#    Marion Neumann, Daniel Marthaler, Shan Huang & Kristian Kersting, 30/09/2013
#================================================================================

# likelihood functions are provided to be used by the gp.py function:
#
#   likErf         (Error function, classification, probit regression)
#   likLogistic    (Logistic, classification, logit regression)
#   likUni         [NOT IMPLEMENTED!] (Uniform likelihood, classification)
#
#   likGauss       (Gaussian, regression)
#   likLaplace     (Laplacian or double exponential, regression)
#   likSech2       [NOT IMPLEMENTED!] (Sech-square, regression)
#   likT           [NOT IMPLEMENTED!] (Student's t, regression)
#
#   likPoisson     [NOT IMPLEMENTED!] (Poisson regression, count data)
#
#   likMix         [NOT IMPLEMENTED!] (Mixture of individual covariance functions)
#
# The likelihood functions have two possible modes, the mode being selected
# as follows (where "lik" stands for "proceed" method for any likelihood function):
#
#
# 1) With two or three input arguments:                       [PREDICTION MODE]
#
#    lp = lik(y, mu) OR lp, ymu, ys2 = lik(y, mu, s2)
#
# This allows to evaluate the predictive distribution. Let p(y_*|f_*) be the
# likelihood of a test point and N(f_*|mu,s2) an approximation to the posterior
# marginal p(f_*|x_*,x,y) as returned by an inference method. The predictive
# distribution p(y_*|x_*,x,y) is approximated by.
#   q(y_*) = \int N(f_*|mu,s2) p(y_*|f_*) df_*
#
#   lp = log( q(y) ) for a particular value of y, if s2 is [] or 0, this
#                    corresponds to log( p(y|mu) )
#   ymu and ys2      the mean and variance of the predictive marginal q(y)
#                    note that these two numbers do not depend on a particular 
#                    value of y 
# All vectors have the same size.
#
#
# 2) With four or five input arguments, the fouth being an object of class "Inference" [INFERENCE MODE]
#
#  lik(y, mu, s2, inf) OR lik(y, mu, s2, inf, i)
#
# There are three cases for inf, namely a) infLaplace, b) infEP and c) infVB. 
# The last input i, refers to derivatives w.r.t. the ith hyperparameter. 
#
# a1)   lp,dlp,d2lp,d3lp = lik(y, f, [], 'infLaplace')
#       lp, dlp, d2lp and d3lp correspond to derivatives of the log likelihood 
#       log(p(y|f)) w.r.t. to the latent location f.
#           lp = log( p(y|f) )
#           dlp = d   log( p(y|f) ) / df
#           d2lp = d^2 log( p(y|f) ) / df^2
#           d3lp = d^3 log( p(y|f) ) / df^3
#
# a2)   lp_dhyp,dlp_dhyp,d2lp_dhyp = lik(y, f, [], 'infLaplace', i)
#       returns derivatives w.r.t. to the ith hyperparameter
#           lp_dhyp = d   log( p(y|f) ) / (     dhyp_i)
#           dlp_dhyp = d^2 log( p(y|f) ) / (df   dhyp_i)
#           d2lp_dhyp = d^3 log( p(y|f) ) / (df^2 dhyp_i)
#
#
# b1)   lZ,dlZ,d2lZ = lik(y, mu, s2, 'infEP')
#       let Z = \int p(y|f) N(f|mu,s2) df then
#           lZ =     log(Z)
#           dlZ = d   log(Z) / dmu
#           d2lZ = d^2 log(Z) / dmu^2
#
# b2)   dlZhyp = lik(y, mu, s2, 'infEP', i)
#       returns derivatives w.r.t. to the ith hyperparameter
#           dlZhyp = d log(Z) / dhyp_i
#
#
# c1)   h,b,dh,db,d2h,d2b = lik(y, [], ga, 'infVB')
#       ga is the variance of a Gaussian lower bound to the likelihood p(y|f).
#       p(y|f) \ge exp( b*f - f.^2/(2*ga) - h(ga)/2 ) \propto N(f|b*ga,ga)
#       The function returns the linear part b and the "scaling function" h(ga) and derivatives
#           dh = d h/dga
#           db = d b/dga
#           d2h = d^2 h/dga
#           d2b = d^2 b/dga
#
# c2)   dhhyp = lik(y, [], ga, 'infVB', i)
#           dhhyp = dh / dhyp_i, the derivative w.r.t. the ith hyperparameter
#
# Cumulative likelihoods are designed for binary classification. Therefore, they
# only look at the sign of the targets y; zero values are treated as +1.
#
# Some examples for valid likelihood functions:
#      lik = likGauss([0.1])
#      lik = likErf()

#
# See the documentation for the individual likelihood for the computations specific 
# to each likelihood function.
#
#
# This is a object-oriented python implementation of gpml functionality 
# (Copyright (c) by Carl Edward Rasmussen and Hannes Nickisch, 2011-02-18).
# based on the functional-version of python implementation
# (Copyright (c) by Marion Neumann and Daniel Marthaler, 20/05/2013)
# 
# Copyright (c) by Marion Neumann and Shan Huang, 30/09/2013


import numpy as np
from scipy.special import erf
import inf

class Likelihood(object):
    """Base function for Likelihood function"""
    def __init__(self):
        self.hyp = []
    def proceed(self):
        pass


class Gauss(Likelihood):
    '''
    Gaussian likelihood function for regression. 

    :math:`Gauss(t)=\\frac{1}{\\sqrt{2\\pi\\sigma^2}}e^{-\\frac{(t-y)^2}{2\\sigma^2}}`,
    where :math:`y` is the mean and :math:`\\sigma` is the standard deviation.

    hyp = [ log_sigma ]
    '''
    def __init__(self, log_sigma=np.log(0.1) ):
        self.hyp = [log_sigma]

    def proceed(self, y=None, mu=None, s2=None, inffunc=None, der=None, nargout=1):
        sn2 = np.exp(2. * self.hyp[0])
        if inffunc == None:              # prediction mode 
            if y == None:
                y = np.zeros_like(mu)
            s2zero = True
            if (not s2==None) and np.linalg.norm(s2) > 0:
                s2zero = False     
            if s2zero:                   # log probability
                lp = -(y-mu)**2 /sn2/2 - np.log(2.*np.pi*sn2)/2. 
                s2 = np.zeros_like(s2)
            else:
                inf_func = inf.EP()   # prediction
                lp = self.proceed(y, mu, s2, inf_func)
            if nargout>1:
                ymu = mu                 # first y moment
                if nargout>2:
                    ys2 = s2 + sn2       # second y moment
                    return lp,ymu,ys2
                else:
                    return lp,ymu
            else:
                return lp  
        else:
            if isinstance(inffunc, inf.EP):
                if der == None:                                  # no derivative mode
                    lZ = -(y-mu)**2/(sn2+s2)/2. - np.log(2*np.pi*(sn2+s2))/2. # log part function
                    if nargout>1:
                        dlZ  = (y-mu)/(sn2+s2)                   # 1st derivative w.r.t. mean
                        if nargout>2:
                            d2lZ = -1/(sn2+s2)                   # 2nd derivative w.r.t. mean
                            return lZ,dlZ,d2lZ
                        else:
                           return lZ,dlZ
                    else:
                        return lZ
                else:                                            # derivative mode
                    dlZhyp = ((y-mu)**2/(sn2+s2)-1) / (1+s2/sn2) # deriv. w.r.t. hyp.lik
                    return dlZhyp
            elif isinstance(inffunc, inf.Laplace):
                if der == None:                                  # no derivative mode
                    if y == None: 
                        y=0 
                    ymmu = y-mu
                    lp = -ymmu**2/(2*sn2) - np.log(2*np.pi*sn2)/2. 
                    if nargout>1:
                        dlp = ymmu/sn2                           # dlp, derivative of log likelihood
                        if nargout>2:                            # d2lp, 2nd derivative of log likelihood
                            d2lp = -np.ones_like(ymmu)/sn2
                            if nargout>3:                        # d3lp, 3rd derivative of log likelihood
                                d3lp = np.zeros_like(ymmu)
                                return lp,dlp,d2lp,d3lp
                            else:
                                return lp,dlp,d2lp
                        else:
                            return lp,dlp
                    else:
                        return lp
                else:                                            # derivative mode
                    lp_dhyp   = (y-mu)**2/sn2 - 1                # derivative of log likelihood w.r.t. hypers
                    dlp_dhyp  = 2*(mu-y)/sn2                     # first derivative,
                    d2lp_dhyp = 2*np.ones_like(mu)/sn2           # and also of the second mu derivative
                    return lp_dhyp,dlp_dhyp,d2lp_dhyp
            '''
            elif isinstance(inffunc, infVB):
                if der == None:
                    # variational lower site bound
                    # t(s) = exp(-(y-s)^2/2sn2)/sqrt(2*pi*sn2)
                    # the bound has the form: b*s - s.^2/(2*ga) - h(ga)/2 with b=y/ga
                    ga  = s2
                    n   = len(ga)
                    b   = y/ga
                    y   = y*np.ones((n,1))
                    db  = -y/ga**2 
                    d2b = 2*y/ga**3
                    h   = np.zeros((n,1))
                    dh  = h
                    d2h = h                           # allocate memory for return args
                    id  = (ga <= sn2 + 1e-8)          # OK below noise variance
                    h[id]   = y[id]**2/ga[id] + np.log(2*np.pi*sn2)
                    h[np.logical_not(id)] = np.inf
                    dh[id]  = -y[id]**2/ga[id]**2
                    d2h[id] = 2*y[id]**2/ga[id]**3
                    id = ga < 0
                    h[id] = np.inf
                    dh[id] = 0
                    d2h[id] = 0                       # neg. var. treatment
                    varargout = [h,b,dh,db,d2h,d2b]
                else:
                    ga = s2 
                    n  = len(ga)
                    dhhyp = np.zeros((n,1))
                    dhhyp[ga<=sn2] = 2
                    dhhyp[ga<0] = 0                   # negative variances get a special treatment
                    varargout = dhhyp                 # deriv. w.r.t. hyp.lik
            else:
                raise Exception('Incorrect inference in lik.Gauss\n')
        '''


class Erf(Likelihood):
    '''
    Error function or cumulative Gaussian likelihood function for binary
    classification or probit regression. 

    :math:`Erf(t)=\\frac{1}{2}(1+erf(\\frac{t}{\\sqrt{2}}))=normcdf(t)`
    '''
    def __init__(self):
        self.hyp = []

    def proceed(self, y=None, mu=None, s2=None, inffunc=None, der=None, nargout=1):
        if not y == None:
            y = np.sign(y)
            y[y==0] = 1
        else:
            y = 1                                        # allow only +/- 1 values
        if inffunc == None:                              # prediction mode if inf is not present
            y = y*np.ones_like(mu)                       # make y a vector
            s2zero = True; 
            if not s2 == None: 
                if np.linalg.norm(s2)>0:
                    s2zero = False                       # s2==0?       
            if s2zero:                                   # log probability evaluation
                p,lp = self.cumGauss(y,mu,2)
            else:                                        # prediction
                lp = self.proceed(y, mu, s2, inf.EP())
                p = np.exp(lp)
            if nargout>1:
                ymu = 2*p-1                              # first y moment
                if nargout>2:
                    ys2 = 4*p*(1-p)                      # second y moment
                    return lp,ymu,ys2
                else:
                    return lp,ymu
            else:
                return lp
        else:                                            # inference mode
            if isinstance(inffunc, inf.Laplace):
                if der == None:                          # no derivative mode
                    f = mu; yf = y*f                     # product latents and labels
                    p,lp = self.cumGauss(y,f,2)
                    if nargout>1:                        # derivative of log likelihood
                        n_p = self.gauOverCumGauss(yf,p)
                        dlp = y*n_p                      # derivative of log likelihood
                        if nargout>2:                    # 2nd derivative of log likelihood
                            d2lp = -n_p**2 - yf*n_p
                            if nargout>3:                # 3rd derivative of log likelihood
                                d3lp = 2*y*n_p**3 + 3*f*n_p**2 + y*(f**2-1)*n_p 
                                return lp,dlp,d2lp,d3lp
                            else:
                                return lp,dlp,d2lp
                        else:
                            return lp,dlp
                    else:
                        return lp
                else:                                    # derivative mode
                    return []                            # derivative w.r.t. hypers

            elif isinstance(inffunc, inf.EP):
                if der == None:                          # no derivative mode
                    z = mu/np.sqrt(1+s2) 
                    junk,lZ = self.cumGauss(y,z,2)       # log part function
                    if not y == None:
                         z = z*y
                    if nargout>1:
                        if y == None: y = 1
                        n_p = self.gauOverCumGauss(z,np.exp(lZ))
                        dlZ = y*n_p/np.sqrt(1.+s2)       # 1st derivative wrt mean
                        if nargout>2:
                            d2lZ = -n_p*(z+n_p)/(1.+s2)  # 2nd derivative wrt mean
                            return lZ,dlZ,d2lZ
                        else:
                            return lZ,dlZ
                    else:
                        return lZ
                else:                                    # derivative mode
                    return []                       # deriv. wrt hyp.lik
        '''
        if inffunc == 'inf.infVB':
            if der == None:                              # no derivative mode
                # naive variational lower bound based on asymptotical properties of lik
                # normcdf(t) -> -(t*A_hat^2-2dt+c)/2 for t->-np.inf (tight lower bound)
                d =  0.158482605320942;
                c = -1.785873318175113;
                ga = s2; n = len(ga); b = d*y*np.ones((n,1)); db = np.zeros((n,1)); d2b = db
                h = -2.*c*np.ones((n,1)); h[ga>1] = np.inf; dh = np.zeros((n,1)); d2h = dh   
                varargout = [h,b,dh,db,d2h,d2b]
            else:                                        # derivative mode
                varargout = []                           # deriv. wrt hyp.lik
        '''


    def cumGauss(self, y=None, f=None, nargout=1):
        # return [p,lp] = cumGauss(y,f)
        if not y == None: 
            yf = y*f 
        else:
            yf = f 
        p = (1. + erf(yf/np.sqrt(2.)))/2. # likelihood
        if nargout>1: 
            lp = self.logphi(yf,p)
            return p,lp 
        else:
            return p

    def gauOverCumGauss(self,f,p):
        # return n_p = gauOverCumGauss(f,p)
        n_p = np.zeros_like(f)       # safely compute Gaussian over cumulative Gaussian
        ok = f>-5                    # naive evaluation for large values of f
        n_p[ok] = (np.exp(-f[ok]**2/2)/np.sqrt(2*np.pi)) / p[ok] 
        bd = f<-6                    # tight upper bound evaluation
        n_p[bd] = np.sqrt(f[bd]**2/4+1)-f[bd]/2
        interp = np.logical_and(np.logical_not(ok),np.logical_not(bd)) # linearly interpolate between both of them
        tmp = f[interp]
        lam = -5. - f[interp]
        n_p[interp] = (1-lam)*(np.exp(-tmp**2/2)/np.sqrt(2*np.pi))/p[interp] + lam *(np.sqrt(tmp**2/4+1)-tmp/2);
        return n_p

    def logphi(self,z,p):
        # return lp = logphi(z,p)
        lp = np.zeros_like(z)                       # allocate memory
        zmin = -6.2; zmax = -5.5;
        ok = z>zmax                                 # safe evaluation for large values
        bd = z<zmin                                 # use asymptotics
        nok = np.logical_not(ok)
        ip = np.logical_and(nok,np.logical_not(bd)) # interpolate between both of them
        lam = 1/(1.+np.exp( 25.*(0.5-(z[ip]-zmin)/(zmax-zmin)) ))  # interp. weights
        lp[ok] = np.log(p[ok])
        lp[nok] = -np.log(np.pi)/2. -z[nok]**2/2. - np.log( np.sqrt(z[nok]**2/2.+2.) - z[nok]/np.sqrt(2.) )
        lp[ip] = (1-lam)*lp[ip] + lam*np.log( p[ip] )
        return lp



class Logistic(Likelihood):
    ''' 
    Logistic function for binary classification or logit regression.

    :math:`Logistic(t)=\\frac{1}{1+e^{-t}}`
    '''
    def __init__(self):
        self.hyp = []

    def proceed(self, y=None, mu=None, s2=None, inffunc=None, der=None, nargout=1):
        mu = np.atleast_2d(mu)
        y = np.atleast_2d(y)
        s2 = np.atleast_2d(s2)

        if not y == None:
            y = np.sign(y)
            y[y==0] = 1
        else:
            y = 1                                        # allow only +/- 1 values
    
        if inffunc == None:                              # prediction mode if inf is not present
            y = y*np.ones_like(mu)                       # make y a vector
            s2zero = True;
            if not s2 == None: 
                if np.linalg.norm(s2)>0:
                    s2zero = False                       # s2==0?       
            if s2zero:                                   # log probability evaluation
                yf = y*mu                                # product latents and variables
                lp = yf
                ok = -35 < yf
                lp[ok] = -np.log(1.+np.exp(-yf[ok]))     # log of likelihood
            else:                                        # prediction
                lp = self.proceed(y, mu, s2, inf.EP())

            if nargout>1:
                p = np.exp(lp)
                ymu = 2*p-1                              # first y moment
                if nargout>2:
                    ys2 = 4*p*(1-p)                      # second y moment
                    return lp,ymu,ys2
                else:
                    return lp,ymu
            else:
                return lp
        else:                                            # inference mode
            if isinstance(inffunc, inf.Laplace):
                if der == None:                          # no derivative mode
                    f = mu; yf = y*f; s = -yf            # product latents and labels
                    ps = max(0,s)
                    lp = -(ps+np.log(np.exp(-ps)+np.exp(s-ps))) # lp = -(log(1+exp(s)))
                    if nargout>1:                        # derivative of log likelihood
                        s = min(0,f)
                        p = np.exp(s)/(np.exp(s)+np.exp(s-f))
                        dlp = (y+1)/2.-p                      # derivative of log likelihood
                        if nargout>2:                    # 2nd derivative of log likelihood
                            d2lp = -np.exp(2*s-f)/(np.exp(s)+np.exp(s-f))**2
                            if nargout>3:                # 3rd derivative of log likelihood
                                d3lp = 2*d2lp*(0.5-p)
                                return lp,dlp,d2lp,d3lp
                            else:
                                return lp,dlp,d2lp
                        else:
                            return lp,dlp
                    else:
                        return lp
                else:                                    # derivative mode
                    return []                            # derivative w.r.t. hypers
            elif isinstance(inffunc, inf.EP):
                if der == None:                          # no derivative mode
                    y = y*np.ones_like(mu)
                    lam = np.sqrt(2)*np.array([[0.44, 0.41, 0.40, 0.39, 0.36]])      # approx coeffs lam_i and c_i
                    c = np.array([[1.146480988574439e+02, -1.508871030070582e+03, 2.676085036831241e+03, -1.356294962039222e+03, 7.543285642111850e+01]]).T
                    l = Erf()
                    a = l.proceed(y=np.dot(y,np.ones((1,5))), mu=np.dot(mu,lam), s2=np.dot(s2,lam**2), inffunc=inffunc, der=None, nargout=3)
                    lZc = a[0]; dlZc = a[1]; d2lZc = a[2];

                    lZ   = self._log_expA_x(lZc,c)
                    dlZ  = self._expABz_expAx(lZc, c, dlZc, c*lam.T)
                    d2lZ = self._expABz_expAx(lZc, c, dlZc**2+d2lZc, c*(lam**2).T) - dlZ**2;
                    
                    # The scale mixture approximation does not capture the correct asymptotic
                    # behavior; we have linear decay instead of quadratic decay as suggested
                    # by the scale mixture approximation. By observing that for large values
                    # of -f*y ln(p(y|f)) for likLogistic is linear in f with slope y, we are
                    # able to analytically integrate the tail region.

                    val = np.abs(mu)-196./200*s2-4.       # empirically determined bound at val==0
                    lam = 1./(1+np.exp(-10.0*val))         # interpolation weights
                    lZtail = min((s2/2-np.abs(mu)), -0.1)  # apply the same to p(y|f) = 1 - p(-y|f)
                    dlZtail = -np.sign(mu)
                    d2lZtail = np.zeros_like(mu)

                    id = (y*mu)>0
                    lZtail[id] = np.log(1-np.exp(lZtail[id])) # label and mean agree
                    dlZtail[id] = 0
                    lZ   = (1-lam)*lZ + lam*lZtail      # interpolate between scale ..
                    dlZ  = (1-lam)*dlZ + lam*dlZtail    # ..  mixture and   ..
                    d2lZ = (1-lam)*d2lZ + lam*d2lZtail  # .. tail approximation
                    if nargout>1:
                        if nargout>2:
                            return lZ,dlZ,d2lZ
                        else:
                            return lZ,dlZ
                    else:
                        return lZ
                else:                               # derivative mode
                    return []                       # deriv. wrt hyp.lik
            elif isinstance(inffunc, inf.VB):
                # variational lower site bound
                # using -log(1+exp(-s)) = s/2 -log( 2*cosh(s/2) );
                # the bound has the form: (b+z/ga)*f - f.^2/(2*ga) - h(ga)/2
                n = len(s2.flatten()); b = (y/2)*np.ones((n,1)); z = np.zeros_like(b)
                return b,z

    def _log_expA_x(self,A,x):
        '''  
        Computes y = log( exp(A)*x ) in a numerically safe way by subtracting the
        maximal value in each row to avoid cancelation after taking the exp
        '''
        N = A.shape[1]
        maxA = np.max(A,axis=1)                    # number of columns, max over columns
        maxA = np.array([maxA]).T
        B = np.dot(maxA, np.dot(np.ones((1,N)),x))       # subtract maximum value
        y = np.log(np.dot(np.exp(A-B),x)) + maxA     # exp(A) = exp(A-max(A))*exp(max(A))
        return y
  
    def _expABz_expAx(self,A,x,B,z):
        ''' 
        Computes y = ( (exp(A).*B)*z ) ./ ( exp(A)*x ) in a numerically safe way
        The function is not general in the sense that it yields correct values for
        all types of inputs. We assume that the values are close together.
        '''
        N = A.shape[1]
        maxA = np.max(A,axis=1)                    # number of columns, max over columns
        maxA = np.array([maxA]).T
        A = A - np.dot(maxA, np.ones((1,N)))       # subtract maximum value
        y = ( np.dot((np.exp(A)*B),z) ) / ( np.dot(np.exp(A),x) )
        return np.atleast_2d(y[0])


class Laplace(Likelihood):
    ''' 
    Laplacian likelihood function for regression. ONLY works with EP inference!

    :math:`Laplace(t) = \\frac{1}{2b}e^{-\\frac{|t-y|}{b}}` where :math:`b=\\frac{\\sigma}{\\sqrt{2}}`,
    :math:`y` is the mean and :math:`\\sigma` is the standard deviation.

    hyp = [ log_sigma ]
    '''
    def __init__(self, log_sigma=np.log(0.1) ):
        self.hyp = [ log_sigma ]

    def proceed(self, y=None, mu=None, s2=None, inffunc=None, der=None, nargout=1):
        sn = np.exp(self.hyp); b = sn/np.sqrt(2);
        if y == None:
            y = np.zeros_like(mu) 
        if inffunc == None:                              # prediction mode if inf is not present
            if y == None:
                y = np.zeros_like(mu)
            s2zero = True; 
            if not s2 == None: 
                if np.linalg.norm(s2)>0:
                    s2zero = False                       # s2==0?       
            if s2zero:                                   # log probability evaluation
                lp = -np.abs(y-mu)/b -np.log(2*b); s2 = 0
            else:                                        # prediction
                lp = self.proceed(y, mu, s2, inf.EP())
            if nargout>1:
                ymu = mu                              # first y moment
                if nargout>2:
                    ys2 = s2 + sn**2                  # second y moment
                    return lp,ymu,ys2
                else:
                    return lp,ymu
            else:
                return lp
        else:                                            # inference mode
            if isinstance(inffunc, inf.Laplace):
                if der == None:                          # no derivative mode
                    if y == None:
                        y = np.zeros_like(mu) 
                    ymmu = y-mu
                    lp = np.abs(ymmu)/b - np.log(2*b)
                    if nargout>1:                        # derivative of log likelihood
                        dip = np.sign(ymmu)/b
                        if nargout>2:                    # 2nd derivative of log likelihood
                            d2lp = np.zeros_like(ymmu)
                            if nargout>3:                # 3rd derivative of log likelihood
                                d3lp = np.zeros_like(ymmu)
                                return lp,dlp,d2lp,d3lp
                            else:
                                return lp,dlp,d2lp
                        else:
                            return lp,dlp
                    else:
                        return lp
                else:                                    # derivative mode
                    return []                            # derivative w.r.t. hypers
            elif isinstance(inffunc, inf.EP):
                n = np.max([len(y.flatten()),len(mu.flatten()),len(s2.flatten()),len(sn.flatten())])
                on = np.ones((n,1))
                y = y*on; mu = mu*on; s2 = s2*on; sn = sn*on; 
                fac = 1e3;          # factor between the widths of the two distributions ...
                                    # ... from when one considered a delta peak, we use 3 orders of magnitude
                #idlik = np.reshape( (fac*sn) < np.sqrt(s2) , (sn.shape[0],) ) # Likelihood is a delta peak
                #idgau = np.reshape( (fac*np.sqrt(s2)) < sn , (sn.shape[0],) ) # Gaussian is a delta peak
                idlik = (fac*sn) < np.sqrt(s2) 
                idgau = (fac*np.sqrt(s2)) < sn 
                id    = np.logical_and(np.logical_not(idgau),np.logical_not(idlik)) # interesting case in between

                if der == None:                          # no derivative mode
                    lZ = np.zeros((n,1))
                    dlZ = np.zeros((n,1))
                    d2lZ = np.zeros((n,1))
                    if np.any(idlik):
                        l = Gauss(log_sigma=np.log(s2[idlik])/2)
                        a = l.proceed(mu[idlik], y[idlik])
                        lZ[idlik] = a[0]; dlZ[idlik] = a[1]; d2lZ[idlik] = a[2]
                    if np.any(idgau):
                        l = Laplace(log_hyp=np.log(sn[idgau]))
                        a = l.proceed(mu=mu[idgau], y=y[idgau])
                        lZ[idgau] = a[0]; dlZ[idgau] = a[1]; d2lZ[idgau] = a[2] 
                    if np.any(id):
                        # substitution to obtain unit variance, zero mean Laplacian
                        tvar = s2[id]/(sn[id]**2+1e-16)
                        tmu = (mu[id]-y[id])/(sn[id]+1e-16)
                        # an implementation based on logphi(t) = log(normcdf(t))
                        zp = (tmu+np.sqrt(2)*tvar)/np.sqrt(tvar)
                        zm = (tmu-np.sqrt(2)*tvar)/np.sqrt(tvar)
                        ap =  self._logphi(-zp)+np.sqrt(2)*tmu
                        am =  self._logphi( zm)-np.sqrt(2)*tmu
                        apam = np.vstack((ap,am)).T
                        lZ[id] = self._logsum2exp(apam) + tvar - np.log(sn[id]*np.sqrt(2.))

                    if nargout>1:
                        lqp = -0.5*zp**2 - 0.5*np.log(2*np.pi) - self._logphi(-zp);       # log( N(z)/Phi(z) )
                        lqm = -0.5*zm**2 - 0.5*np.log(2*np.pi) - self._logphi( zm);
                        dap = -np.exp(lqp-0.5*np.log(s2[id])) + np.sqrt(2)/sn[id]
                        dam =  np.exp(lqm-0.5*np.log(s2[id])) - np.sqrt(2)/sn[id]
                        _z1 = np.vstack((ap,am)).T
                        _z2 = np.vstack((dap,dam)).T
                        _x = np.array([[1],[1]])
                        dlZ[id] = self._expABz_expAx(_z1, _x, _z2, _x)
                        if nargout>2:
                            a = np.sqrt(8.)/sn[id]/np.sqrt(s2[id]);
                            bp = 2./sn[id]**2 - (a - zp/s2[id])*np.exp(lqp)
                            bm = 2./sn[id]**2 - (a + zm/s2[id])*np.exp(lqm)
                            _x = np.reshape(np.array([1,1]),(2,1))
                            _z1 = np.reshape(np.array([ap,am]),(1,2))
                            _z2 = np.reshape(np.array([bp,bm]),(1,2))
                            d2lZ[id] = self._expABz_expAx(_z1, _x, _z2, _x) - dlZ[id]**2
                            return lZ,dlZ,d2lZ
                        else:
                            return lZ,dlZ
                    else:
                        return lZ
                else:                                    # derivative mode
                    dlZhyp = np.zeros((n,1))
                    if np.any(idlik):
                        dlZhyp[idlik] = 0
                    if np.any(idgau):
                        l = Laplace(log_hyp=np.log(sn[idgau]))
                        a =  l.proceed(mu=mu[idgau], y=y[idgau], inffunc='inf.Laplace', nargout=1)
                        dlZhyp[idgau] = a[0]

                    if np.any(id):
                        # substitution to obtain unit variance, zero mean Laplacian
                        tmu = (mu[id]-y[id])/(sn[id]+1e-16);        tvar = s2[id]/(sn[id]**2+1e-16)
                        zp  = (tvar+tmu/np.sqrt(2))/np.sqrt(tvar);  vp = tvar+np.sqrt(2)*tmu
                        zm  = (tvar-tmu/np.sqrt(2))/np.sqrt(tvar);  vm = tvar-np.sqrt(2)*tmu
                        dzp = (-s2[id]/sn[id]+tmu*sn[id]/np.sqrt(2)) / np.sqrt(s2[id])
                        dvp = -2*tvar - np.sqrt(2)*tmu
                        dzm = (-s2[id]/sn[id]-tmu*sn[id]/np.sqrt(2)) / np.sqrt(s2[id])
                        dvm = -2*tvar + np.sqrt(2)*tmu
                        lezp = self._lerfc(zp); # ap = exp(vp).*ezp
                        lezm = self._lerfc(zm); # am = exp(vm).*ezm
                        vmax = np.max(np.array([vp+lezp,vm+lezm]),axis=0); # subtract max to avoid numerical pb
                        ep  = np.exp(vp+lezp-vmax)
                        em  = np.exp(vm+lezm-vmax)
                        dap = ep*(dvp - 2/np.sqrt(np.pi)*np.exp(-zp**2-lezp)*dzp)
                        dam = em*(dvm - 2/np.sqrt(np.pi)*np.exp(-zm**2-lezm)*dzm)        
                        dlZhyp[id] = (dap+dam)/(ep+em) - 1;       
                    return dlZhyp               # deriv. wrt hyp.lik
            elif isinstance(inffunc, inf.VB):
                n = len(s2.flatten()); b = np.zeros((n,1)); y = y*np.ones((n,1)); z = y
                return b,z

    def _lerfc(self,t):
        ''' numerically safe implementation of f(t) = log(1-erf(t)) = log(erfc(t))'''
        from scipy.special import erfc
        f  = np.zeros_like(t)
        tmin = 20; tmax = 25
        ok = t<tmin                              # log(1-erf(t)) is safe to evaluate
        bd = t>tmax                              # evaluate tight bound
        nok = np.logical_not(ok)
        interp = np.logical_and(nok,np.logical_not(bd)) # interpolate between both of them
        f[nok] = np.log(2/np.sqrt(np.pi)) -t[nok]**2 -np.log(t[nok]+np.sqrt( t[nok]**2+4/np.pi ))
        lam = 1/(1+np.exp( 12*(0.5-(t[interp]-tmin)/(tmax-tmin)) ))   # interp. weights
        f[interp] = lam*f[interp] + (1-lam)*np.log(erfc( t[interp] ))
        f[ok] += np.log(erfc( t[ok] ))             # safe eval
        return f

    def _expABz_expAx(self,A,x,B,z):
        ''' 
        Computes y = ( (exp(A).*B)*z ) ./ ( exp(A)*x ) in a numerically safe way
        The function is not general in the sense that it yields correct values for
        all types of inputs. We assume that the values are close together.
        '''
        N = A.shape[1]
        maxA = np.max(A,axis=1)                    # number of columns, max over columns
        maxA = np.array([maxA]).T
        A = A - np.dot(maxA, np.ones((1,N)))       # subtract maximum value
        y = ( np.dot((np.exp(A)*B),z) ) / ( np.dot(np.exp(A),x) )
        return y[0]

    def _logphi(self,z):
        ''' Safe implementation of the log of phi(x) = \int_{-\infty}^x N(f|0,1) df
         returns lp = log(normcdf(z))
        '''
        lp = np.zeros_like(z)                       # allocate memory
        zmin = -6.2; zmax = -5.5;
        ok = z>zmax                                 # safe evaluation for large values
        bd = z<zmin                                 # use asymptotics
        nok = np.logical_not(ok)
        ip = np.logical_and(nok,np.logical_not(bd)) # interpolate between both of them
        lam = 1./(1.+np.exp( 25.*(0.5-(z[ip]-zmin)/(zmax-zmin)) ))  # interp. weights
        lp[ok] = np.log( 0.5*( 1.+erf(z[ok]/np.sqrt(2.)) ) )
        lp[nok] = -0.5*(np.log(np.pi) + z[nok]**2) - np.log( np.sqrt(2.+0.5*(z[nok]**2)) - z[nok]/np.sqrt(2)) 
        lp[ip] = (1-lam)*lp[ip] + lam*np.log( 0.5*( 1.+erf(z[ip]/np.sqrt(2.)) ) )
        return lp

    def _logsum2exp(self,logx):
        '''computes y = log( sum(exp(x),2) ) in a numerically safe way 
        by subtracting the row maximum to avoid cancelation after taking 
        the exp the sum is done along the rows'''
        N = logx.shape[1]
        max_logx = logx.max(1)
        max_logx = np.array([max_logx]).T
        # we have all values in the log domain, and want to calculate a sum
        x = np.exp(logx - np.dot(max_logx,np.ones((1,N))))
        y = np.log(np.array([np.sum(x,1)]).T) + max_logx
        return list(y.flatten())


 

# test
if __name__ == '__main__':
    l = Logistic()
    mu = np.array([1,2,3])
    a = l.proceed(mu=mu, nargout=3)
    print a 

    # at least it can run without throwing error/exception 
    # result is:
    # [array([-1.98660617, -2.1896091 , -2.52794731]), array([1, 2, 3]), 7.3890560989306504]

    # need further test


