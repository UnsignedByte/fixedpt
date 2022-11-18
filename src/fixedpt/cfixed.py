from .fixed import Fixed
from decimal import Decimal

# Complex fixed number
class CFixed():
	# Invariant:
	# Both real and complex part have the same precision

	def __init__(self, v=0, n=32, d=16, raw=False):
		if d > n-1:
			raise ValueError(f"Too many decimal places! ({n} total bits, {d} decimal bits)")

		self.real = Fixed(0, 1, n, d)
		self.imag = Fixed(0, 1, n, d)

		self.set(v, raw)

	@staticmethod
	def cast(o, d=64): # casts a fixed value and copies it with default precision
		if (isinstance(o, CFixed)):
			return o.clone()
		
		elif (isinstance(o, tuple)):
			r = Fixed.cast(o[0])
			i = Fixed.cast(o[1])
			md = max(r._d, i._d);
			ndims = (max(r._n-r._d, i._n - i._d) + md, md);
			r.resize(1, ndims[0], ndims[1]);
			i.resize(1, ndims[0], ndims[1]);
			return CFixed((r.get(), i.get()), ndims[0], ndims[1], raw=True)
		
		elif (isinstance(o, Fixed)):
			return CFixed(complex(o, 0), o._n + 1 - o._signed, o._d)
		
		elif (isinstance(o, int)):
			return CFixed(complex(o, 0), max(1, o.bit_length()) + 1, 0)

		elif (isinstance(o, float)):
			return CFixed(complex(o, 0), max(1, int(o).bit_length()) + d + 1, d)

		elif (isinstance(o, Decimal)):
			i = int(o * (1 << d))
			return Fixed(complex(i, 0), max(1, int(i).bit_length()) + 1, d, raw=True)

		else:
			raise ValueError(f"Casting from invalid type {type(o)}")


	def clone(self): # clone a Fixed
		return CFixed(self.get(), self.real._n, self.real._d, raw=True)

	def set(self, k, raw=False):
		if (isinstance(k, complex)):
			self.real.set(k.real, raw)
			self.imag.set(k.imag, raw)
		elif (isinstance(k, tuple)):
			self.real.set(k[0], raw)
			self.imag.set(k[1], raw)
		else:
			raise ValueError(f"Assigning with invalid type {type(k)}")

	def get(self, raw=True): # get raw value
		if raw:
			return (self.real.get(), self.imag.get())
		else:
			return complex(self.real.get(False), self.imag.get(False))

	#normalize the dimensions of the real and imaginary parts
	def normalize(self):
		md = max(self.real._d, self.imag._d);

		return self.resize(
			max(self.real._n - self.real._d,
				self.imag._n - self.imag._d) + md,
			md
		)

	def resize(self, n=None, d=None):
		self.real.resize(None, n, d);
		self.imag.resize(None, n, d);

		return self
	
	def __repr__(self):
		return f"{len(self)}.{self.real._d}<{complex(self)}>"

	def __complex__(self):
		return complex(float(self.real), float(self.imag))

	# Get high precision decimal version of self
	def decimal(self):
		return (self.real.decimal(), self.imag.decimal())

	def bin(self, dot=False):
		return f'({self.real.bin(dot)} + {self.imag.bin(dot)}j)'

	def __len__(self):
		return self.real._n

### OPERATORS

	def __neg__(self):
		t = self.clone()
		t.real = -t.real
		t.imag = -t.imag
		t.normalize()
		return t

	def __invert__(self):
		t = self.clone()
		t.real = ~t.real
		t.imag = ~t.imag
		t.normalize()
		return t

	def magsq(self): # Magnitude squared
		a = abs(self.real)
		b = abs(self.imag)
		return (a * a + b * b)

	def __ilshift__(self, s):
		self.real <<= s
		self.imag <<= s
		self.normalize()

		return self

	def __irshift__(self, s):
		self.real >>= s
		self.imag >>= s
		self.normalize()

		return self

	def __lshift__(self, s):
		t = self.clone()
		t <<= s
		return t

	def __rshift__(self, s):
		t = self.clone()
		t >>= s
		return t

	def __iadd__(self, o):
		o = CFixed.cast(o);

		self.real += o.real
		self.imag += o.imag
		# pre = (self.real.clone(), self.imag.clone())
		self.normalize()
		# assert (self.real == pre[0]) and (self.imag == pre[1])

		return self

	def __add__(self, o):
		t = self.clone();
		t += o;
		return t;

	def __isub__(self, o):
		self += -o;
		return self;

	def __sub__(self, o):
		t = self.clone();
		t -= o;
		return t

	def __imul__(self, o):
		o = CFixed.cast(o)
		a = self.real * o.real
		b = self.imag * o.imag
		c = (self.real + self.imag) * (o.real + o.imag)

		# print("T", self, o)

		self.real = a - b
		self.imag = c - a - b

		self.normalize()

		# print(self)

		return self

	def __mul__(self, o):
		t = self.clone()
		t *= o
		return t

	### COMPARISON
	def __lt__(self, o):
		return (self - o).magsq().is_neg()

	def __eq__(self, o):
		return (self - o).magsq() == 0

	def __ge__(self, o):
		return not (self < o)

	def __ne__(self, o):
		return not (self == o)

	def __le__(self, o):
		return o >= self

	def __gt__(self, o):
		return o < self