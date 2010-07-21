from module import *

class linear (module_1_1):
    def __init__(self, shape_in, shape_out):
        ''' out[] = w[][] . in[] '''
        self.shape_in  = ensure_tuple(shape_in)
        self.shape_out = ensure_tuple(shape_out)
        size_in  = product(shape_in)
        size_out = product(shape_out)
        self.w = self.param((size_out, size_in))

    def forget(self):
        arg = self.parameter.forget
        fanin = self.w.shape[1]
        z = arg.lin_value / (fanin ** (1.0 / arg.lin_exponent))
        self.w.x = sp.random.random(self.w.shape) * (2*z) - z

    def normalize(self):
        for col in self.w.x.T:
            col *= 1.0 / sqrt(sqmag(col))

    def fprop(self, input, output):
        assert (self.shape_in == input.shape)
        output.resize(self.shape_out)
        output.x[:] = sp.dot(self.w.x, input.x.ravel()).reshape(output.shape)

    def bprop_input(self, input, output):
        input.dx.ravel()[:] += sp.dot(self.w.x.T, output.dx.ravel())
    def bprop_param(self, input, output):
        self.w.dx += sp.outer(output.dx.ravel(), input.x.ravel())

    def bbprop_input(self, input, output):
        input.ddx.ravel()[:] += sp.dot(sp.square(self.w.x.T),output.ddx.ravel())
    def bbprop_param(self, input, output):
        self.w.ddx += sp.outer(output.ddx.ravel(), sp.square(input.x.ravel()))


class bias (module_1_1):
    def __init__(self, shape_in, per_feature = False):
        ''' if per_feature is false, out[]    = in[]    + b[]
            otherwise                out[k][] = in[k][] + b[k] '''
        self.per_feature = per_feature
        shape_in = ensure_tuple(shape_in)
        shape_b = shape_in
        if per_feature:
            ndim = len(shape_in)
            shape_b = (shape_in[0],) + (ndim-1)*(1,)
        self.b = self.param(shape_b)
    
    def forget(self):
        arg = self.parameter.forget
        z = arg.lin_value
        self.b.x = sp.random.random(self.b.shape) * (2*z) - z
    
    def normalize(self): pass
    
    def fprop(self, input, output):
        assert (self.b.ndim     == input.ndim)
        assert (self.b.shape[0] == input.shape[0])
        assert (self.per_feature or self.b.shape == input.shape)
        output.resize(input.shape)
        output.x[:] = input.x + self.b.x
    
    def bprop_input(self, input, output):
        input.dx += output.dx
    def bprop_param(self, input, output):
        odx = output.dx
        if self.per_feature:
            odx = odx.reshape((len(self.b), -1)).sum(1).reshape(self.b.shape)
        self.b.dx += odx
    
    def bbprop_input(self, input, output):
        input.ddx  += output.ddx
    def bbprop_param(self, input, output):
        oddx = output.ddx
        if self.per_feature:
            oddx = oddx.reshape((len(self.b), -1)).sum(1).reshape(self.b.shape)
        self.b.ddx += oddx


