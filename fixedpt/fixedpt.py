class Fixed():
	# INVARIANT:
	# n >= d
	# d >= 0
	# signed = 0 or 1

	def __init__(self, v=0, signed=0, n=32, d=16):
		self._signed = signed
		self._n = n
		self._d = d

		self.set(v)

	def clone(self): # clone a Fixed
		return Fixed(self.get(), self._signed, self._n, self._d)

	def set(self, k): # set raw value
		self._data = k % (1 << len(self))

	def get(self): # get raw value
		return self._data

	def is_neg(self):
		return self._signed and self[-1]

	def fixed_left_shift(self, s): # left shift while fixing d
		self._data <<= s
		self._n += s;
		return self

	def fixed_right_shift(self, s): # right shift while fixing d
		self._data >>= s
		return self

	def resize(self, signed=None, n=None, d=None):
		self._signed = signed if signed is not None else self._signed
		
		if d is not None and d != self._d:
			if d > self._d:
				self.fixed_left_shift(d - self._d) # pad right
			else:
				self.fixed_right_shift(self._d-d) # truncate decimal bits

			self._d = d # update decimal bit count

		if n is not None and n != self._n:
			if n < self._n:
				self._n = n; # update bit count
				self.set(self.get())
			else: # sign extension
				ext = (((self.is_neg() << (n - self._n)) - self.is_neg()) << self._n) + self.get(); # sign ext


				self._n = n # update bit count
				self.set(ext)

		return self
	
	def __repr__(self):
		return f"{'' if self._signed else 'u'}{len(self)}.{self._d}({float(self)})"

	def __float__(self):
		return (((self.get() % (1 << len(self)-1)) - (1 << len(self))) if self.is_neg() else self.get()) / 2**self._d

	def __int__(self):
		return int(float(self))

	def bin(self, dot=False):
		b = format(self.get(), f'#0{len(self) + 2}b');

		if dot:
			return b[:len(self) + 2-self._d] + "." + b[len(self) + 2-self._d:]
		else:
			return b

	def __len__(self):
		return self._n

	def __getitem__(self, key): # returns the nth bit of the number
		return (self._data >> (key % len(self))) & 1

### OPERATORS

	def __neg__(self):
		t = self.clone();
		t.set(-t._data)
		return t

	def __invert__(self):
		t = self.clone()
		t.set(-t._data - 1)
		return t

	def __ilshift__(self, s):
		if s > self._d:
			self.fixed_left_shift(s-self._d) # do a real left shift here
			self._d = 0
		else:
			self._d -= s

		return self

	def __irshift__(self, s):
		self._d += s
		self.resize(None, max(self._d, self._n), None) # make sure n >= d
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
		if (isinstance(o, int)):
			o = Fixed(o, 1, o.bit_length() + (o < 0) + 1, 0)
		to = o.clone()

		# normalize decimal bits
		if o._d < self._d:
			to.resize(None, len(to) + self._d-o._d, self._d);
		else:
			self.resize(None, len(self) + o._d-self._d, o._d);

		self.resize(None, max(len(self), len(to)) + 1, None) # resize
		to.resize(None, max(len(self), len(to)) + 1, None) # resize
		self.set(self._data + to._data)
		return self

	def __add__(self, o):
		t = self.clone();
		t += o;
		return t;

	def __isub__(self, o):
		self += -o;
		return self;

	def __sub__(self, o):
		return self + -o

	def __imul__(self, o):
		if (isinstance(o, int)):
			o = Fixed(o, 1, o.bit_length() + (o < 0) + 1, 0)
		self.resize(None, len(self) + len(o), self._d + o._d)

		self.set(self.get() * o.get())

		return self

	def __mul__(self, o):
		t = self.clone()
		t *= o
		return t

	def __ifloordiv__(self, o):
		if (isinstance(o, int)):
			o = Fixed(o, 1, o.bit_length() + (o < 0) + 1, 0)

		self <<= o._d; # shift left self to counteract the shift of o

		self.set(self.get() // o.get())

		return self

	def __floordiv__(self, o):
		t = self.clone()
		t //= o
		return t