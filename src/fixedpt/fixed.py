from decimal import Decimal

# Fixed point number
class Fixed():
	# INVARIANT:
	# n >= d
	# d >= 0
	# signed = 0 or 1

	def __init__(self, v=0, signed=0, n=32, d=16, raw=False):
		if (signed + d > n) or (signed >= n):
			raise ValueError(f"Too many decimal places! ({signed} sign bits, {n} total bits, {d} decimal bits)")
		self._signed = signed
		self._n = n
		self._d = d

		self.set(v, raw)

	@staticmethod
	def cast(o, d=64): # casts a fixed value and copies it with default precision
		if (isinstance(o, Fixed)):
			return o.clone()
		
		elif (isinstance(o, int)):
			return Fixed(o, 1, max(1, o.bit_length()) + 1, 0)

		elif (isinstance(o, float)):
			return Fixed(o, 1, max(1, int(o).bit_length()) + d + 1, d)

		elif (isinstance(o, Decimal)):
			i = int(o * (1 << d))
			return Fixed(i, 1, max(1, int(i).bit_length()) + 1, d, raw=True)

		else:
			raise ValueError(f"Casting from invalid type {type(o)}")


	def clone(self): # clone a Fixed
		return Fixed(self.get(), self._signed, self._n, self._d, raw=True)

	def set(self, k, raw=False):
		if not raw:
			k = int(k * (1 << self._d))
		else:
			k = int(k)
		self._data = k % (1 << len(self))

	def get(self, raw=True): # get raw value
		if raw or (not self.is_neg()):
			return self._data
		else:
			return self._data - (1 << len(self))

	def is_neg(self):
		return bool(self._signed and self[-1])

	def fixed_left_shift(self, s): # left shift while fixing d
		self._data <<= s
		self._n += s;
		return self

	def fixed_right_shift(self, s): # right shift while fixing d
		self._data >>= s
		return self

	def resize(self, signed=None, n=None, d=None):
		n = n if n is not None else self._n
		if signed and not self._signed:
			n = n + 1
		
		if d is not None and d != self._d:
			if d > self._d:
				self.fixed_left_shift(d - self._d) # pad right
			else:
				self.fixed_right_shift(self._d-d) # truncate decimal bits

			self._d = d # update decimal bit count

		if n is not None and n != self._n:
			if n < self._n:
				self._n = n; # update bit count
				self.set(self.get(), raw=True)
			else: # sign extension
				ext = (((self.is_neg() << (n - self._n)) - self.is_neg()) << self._n) + self.get(); # sign ext


				self._n = n # update bit count
				self.set(ext, raw=True)

		self._signed = signed if signed is not None else self._signed

		return self
	
	def __repr__(self):
		return f"{'' if self._signed else 'u'}{len(self)}.{self._d}({float(self)})"

	def __float__(self):
		return self.get(False) / 2**self._d

	# Get high precision decimal version of self
	def decimal(self):
		return Decimal(self.get(False)) / Decimal(1 << self._d)

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

		# special case to add an extra bit when we are at MIN_INT
		if self.is_neg() and self.get() == (1 << (len(self)-1)): 
			t.resize(None, len(self)+1, None)

		t.set(-t._data, raw=True)
		return t

	def __invert__(self):
		t = self.clone()
		t.set(-t._data - 1, raw=True)
		return t

	def __abs__(self):
		return (-self) if self.is_neg else self.clone();

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
		o = Fixed.cast(o)

		# normalize decimal bits
		if o._d < self._d:
			o.resize(self._signed, len(o) + self._d-o._d, self._d);
		else:
			self.resize(None, len(self) + o._d-self._d, o._d);

		lo = len(o)
		ls = len(self)

		self.resize(None, max(ls, lo) + 1, None) # resize
		o.resize(None, max(ls, lo) + 1, None) # resize with signedness of self
		self.set(self._data + o._data, raw=True)
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
		o = Fixed.cast(o)

		od = o._d
		sd = self._d

		o <<= od;
		self <<= sd;

		nl = len(self) + len(o)

		self.resize(None, nl, None);
		o.resize(None, nl, None);

		self.set(self.get() * o.get(), raw=True)

		self>>= (od + sd)

		# nl = len(self) + len(o)
		# nd = self._d + o._d;
		# self.resize(None, nl, nd)
		# o.resize(None, nl, nd)

		# self.set((self.get() * o.get()) >> nd, raw=True)

		return self

	def __mul__(self, o):
		t = self.clone()
		t *= o
		return t

	def __itruediv__(self, o):
		o = Fixed.cast(o)

		self <<= o._d; # shift left self to counteract the shift of o

		if o.is_neg():
			og = (-o).get()
		else:
			og = o.get()

		if self.is_neg():
			sg = (-self).get()
		else:
			sg = self.get()

		self.set((-1 if o.is_neg() ^ self.is_neg() else 1) * (sg // og), raw=True)

		return self

	def __truediv__(self, o):
		t = self.clone()
		t /= o
		return t

	### COMPARISON
	def __lt__(self, o):
		return (self - o).is_neg()

	def __eq__(self, o):
		return (self - o).get() == 0

	def __ge__(self, o):
		return not (self < o)

	def __ne__(self, o):
		return not (self == o)

	def __le__(self, o):
		return o >= self

	def __gt__(self, o):
		return o < self