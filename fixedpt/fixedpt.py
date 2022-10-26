import numpy as np

class Fixed():
	# INVARIANT:
	# n >= d
	# d >= 0
	# signed = 0 or 1

	def __init__(self, v=0, signed=0, n=32, d=16):
		self._signed = signed
		self._n = n
		self._d = d
		
		self._data = np.zeros((n+31)//32, dtype=np.uint32)
		self.set(v)

	def clone(self): # clone a Fixed
		return Fixed(self.get(), self._signed, self._n, self._d)

	def set(self, k): # set raw value
		k %= 1 << len(self)
		for i in range(len(self._data)):
			self._data[i] = np.uint32(k % (1 << 32))
			k >>= 32

		self.resize()
		return self

	def get(self): # get raw value
		res = 0;
		for i in self._data[::-1]:
			res <<= 32
			res |= int(i)
		return res

	def is_neg(self):
		return self._signed and self[-1]

	def fixed_left_shift(self, s): # left shift while fixing d
		sm = np.uint64(s % 32)
		if sm + (self._n % 32) > 32:
			np.append(self._data, 0) # add extra leading 0 if necessary

		if sm > 0:
			l = np.uint64(0);
			for i in range(len(self._data)):
				ln = np.uint64(self._data[i]) << sm
				self._data[i] = np.uint32(ln + (l >> np.uint64(32)))
				l = ln

		np.insert(self._data, 0, s//32) # add trailing zeros
		self._n += s # update number of bits total

		return self

	def fixed_right_shift(self, s): # right shift while fixing d
		sm = np.uint64(s % 32)

		if sm > 0:
			l = np.uint64(0);
			for i in range(len(self._data)-1, -1, -1):
				ln = np.uint64(self._data[i])
				self._data[i] = np.uint32((l + ln) >> sm)
				l = ln << np.uint64(32)

		if s//32 > 0:
			self._data = self._data[:-(s//32)]
		self._n -= s # update number of bits total

		return self

	def resize(self, signed=None, n=None, d=None):
		self._signed = signed if signed is not None else self._signed

		if d is not None:
			if d > self._d:
				self.fixed_left_shift(d - self._d) # pad right
			else:
				self.fixed_right_shift(self._d-d) # truncate decimal bits

			self._d = d # update decimal bit count

		if n is not None:
			if n > self._n:
				nl = (n-self._n)//32
				if self.is_neg():
					self._data[-1] |= ~np.uint32((1 << (self._n % 32)) - 1) # extend sign bits
					self._data = np.append(self._data, np.ones(nl))
				else:
					self._data = np.append(self._data, np.zeros(nl))	
			else:
				self._data = np.resize(self._data, (self._n+31)//32) # truncate or extend data

			self._n = n # update bit count

		if self._n % 32 > 0:
			self._data[-1] &= (1 << (self._n % 32)) - 1 # truncate leading bits
	
	def __repr__(self):
		return f"{'' if self._signed else 'u'}{len(self)}.{self._d}({float(self)})"

	def __float__(self):
		t = -self if self.is_neg() else self
		return float(sum(
			int(t._data[i]) * (2**((i << 5) - t._d))
			for i in range(len(t._data))
		) * (-1 if t.is_neg() else 1))

	def __len__(self):
		return self._n

	def __getitem__(self, key): # returns the nth bit of the number
		key = key % len(self);
		return (self._data[key//32] >> (key % 32)) & 1

### OPERATORS

	def __neg__(self):
		return ~self + Fixed(1, self._signed, self._n, self._d)

	def __invert__(self):
		t = self.clone()
		for i in range(len(t._data)):
			t._data[i] = ~t._data[i]

		t.resize()
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

	def __add__(self, o):
		# TODO
		return self




