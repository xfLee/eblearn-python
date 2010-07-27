from module import *
from basic import multiplication

class distance_l2 (no_params, module_2_1):
    def __init__(self, average = True):
        self.average = average
    
    def fprop(self, input1, input2, energy):
        energy.resize((1,))
        assert (input1.shape == input2.shape)
        coeff = 0.5
        if self.average: coeff /= input1.size
        energy.x[0] = sqdist(input1.x, input2.x) * coeff

    def bprop_input(self, input1, input2, energy):
        edx = energy.dx[0]
        if self.average: edx /= input1.size
        r = (input1.x - input2.x) * edx
        input1.dx += r
        input2.dx -= r
    
    def bbprop_input(self, input1, input2, energy):
        edx, eddx = energy.dx[0], energy.ddx[0]
        d = input1.x - input2.x
        if self.average:
            d   /= input1.size
            edx /= input1.size
        d_sq = sp.square(d)
        input1.ddx += d_sq * eddx + edx
        input2.ddx += d_sq * eddx + edx


class cross_entropy (no_params, module_2_1):
    def fprop(self, input1, input2, energy):
        energy.resize((1,))
        assert (input1.shape == input2.shape)
        expin1 = sp.exp(input1.x)
        softmaxin1 = expin1 * (1.0 / expin1.sum())
        energy.x[0] = sp.dot(-input2.x.ravel(),
                              sp.log(softmaxin1).ravel())

    def bprop_input(self, input1, input2, energy):
        expin1 = sp.exp(input1.x)
        softmaxin1 = expin1 * (1.0 / expin1.sum())
        d1 = ((input2.x.sum() * softmaxin1) - input2.x)
        d2 = sp.log(softmaxin1) 
        input1.dx += energy.dx[0] * d1
        input2.dx -= energy.dx[0] * d2
        
    def bbprop_input(self, input1, input2, energy):
        expin1 = sp.exp(input1.x)
        expin1_sum_inv = 1.0 / expin1.sum()
        softmaxin1 = expin1 * expin1_sum_inv
        sum2 = input2.x.sum()
        
        d1 = (sum2 * softmaxin1) - input2.x
        d2 = sp.log(softmaxin1) 
        input1.ddx += energy.ddx[0] * sp.square(d1)
        input1.ddx += (energy.dx[0] * sum2) * softmaxin1 * (1 - softmaxin1)
        input2.ddx += energy.ddx[0] * sp.square(d2)


class penalty_l1 (no_params, module_1_1):
    def __init__(self, thresh = 0.0001, average = True):
        self.thresh = thresh
        self.average = average
    def fprop(self, input, energy):
        energy.resize((1,))
        energy.x[0] = sp.absolute(input.x).sum()
        if self.average: energy.x[0] /= input.size
    def bprop_input (self, input, energy):
        d = None
        if self.thresh:
            d = sp.sign(thresh_less(input.x, sp.absolute(input.x), self.thresh))
        else:
            d = sp.sign(input.x)
        d *= (energy.dx[0] / input.size if self.average else energy.dx[0])
        input.dx += d
    def bbprop_input(self, input, energy):
        eddx = energy.ddx[0]
        if self.average:
            eddx /= input.size ** 2
        if self.thresh:
            input.ddx += eddx * (sp.absolute(input.x) >= self.thresh)
        else:
            input.ddx += eddx


class penalty_l2 (no_params, module_1_1):
    def __init__(self, average = True):
        self.average = average
    def fprop(self, input, energy):
        energy.resize((1,))
        energy.x[0] = 0.5 * sqmag(input.x)
        if self.average: energy.x[0] /= input.size
    def bprop_input (self, input, energy):
        edx = energy.dx[0]
        if self.average: edx /= input.size
        input.dx += input.x * edx
    def bbprop_input(self, input, energy):
        edx, eddx = energy.dx[0], energy.ddx[0]
        d = input.x
        if self.average:
            d   /= input.size
            edx /= input.size
        d_sq = sp.square(d)
        input.ddx += d_sq * eddx + edx


class bconv_rec_cost (no_params, module_2_1):
    @staticmethod
    def coeff_from_conv(rec_shape, kernel_shape):
        rec_shape    = ensure_tuple(rec_shape)
        kernel_shape = ensure_tuple(kernel_shape)
        assert(len(rec_shape) == len(kernel_shape))
        coeff = zeros(rec_shape)
        ucoeff = coeff
        for d, kd in enumerate(kernel_shape):
            ucoeff = unfold(ucoeff, d, kd, 1)
        ucoeff += 1. / sp.prod(kernel_shape)
        return coeff
    
    def __init__(self, coeff, average = True):
        self.mw = multiplication()
        self.l2 = distance_l2(average)
        self.cstate = state(coeff.shape)
        self.cstate.x[:] = coeff
        self.ostate = state(coeff.shape)

    def fprop(self, input1, input2, output):
        self.mw.fprop(self.cstate, input2, self.ostate)
        self.l2.fprop(input1, self.ostate, output)

    def bprop_input(self, input1, input2, output):
        clear(self.cstate.dx)
        clear(self.ostate.dx)
        self.l2.bprop_input(input1, self.ostate, output)
        self.mw.bprop_input(self.cstate, input2, self.ostate)

    def bbprop_input(self, input1, input2, output):
        clear(self.cstate.ddx)
        clear(self.ostate.ddx)
        self.l2.bbprop_input(input1, self.ostate, output)
        self.mw.bbprop_input(self.cstate, input2, self.ostate)

    
