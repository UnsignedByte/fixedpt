# -*- coding: utf-8 -*-
# @Author: UnsignedByte
# @Date:   2022-10-29 17:59:31
# @Last Modified by:   UnsignedByte
# @Last Modified time: 2022-10-29 20:33:18

import sys
sys.path.insert(0, '../')
from src.fixedpt import Fixed
from random import randint
from decimal import getcontext, Decimal

EPSILON_RAW = 1e-12 # epsilon value
EPSILON = Fixed.cast(EPSILON_RAW)

def distr(s, n, d):
	return lambda _=0: (
		ms := randint(s[0], s[1]),
		nb := randint(max(ms+1, n[0]), n[1]),
		randint(d[0], min(d[1], nb-ms))
	)

TEST_DISTRIBUTIONS = [(distr(s, n, d), c) for (s, n, d, c) in [ # Distribution of types of fixed numbers to test
	((0, 1), (1, 8), (0, 8), 100), # small numbers
	((0, 1), (32, 32), (0, 32), 500), # signed and unsigned 32 bit floats 
	((0, 1), (1, 64), (0, 64), 500), # signed and unsigned 64 bit floats 
	((0, 1), (128, 1024), (0, 1024), 100) # large bit width numbers
]]

def rand_fixed(s, n, d):
	return Fixed(randint(0, (1<<n)-1), s, n, d, raw=True)

def eval_distrs(t): # evaluate tests on all distributions
	for (d, c) in TEST_DISTRIBUTIONS:
		for i in range(c):
			t(d)

# check that float(f) is approximately equal to f
def test_float_cast():
	def t(d):
		(s, n, d) = d()
		f = rand_fixed(s, n, d)
		
		assert (float(f) - (f.get() / (1 << d))) <= EPSILON_RAW 

	eval_distrs(t)

# check that f-f = 0
def test_sub_identity():
	def t(d):
		(s, n, d) = d()
		f = rand_fixed(s, n, d)

		f.resize(1, None, None) # make signed

		assert abs(f - f) <= EPSILON
	eval_distrs(t)


# check that +, -, * are approximately equal to their float counterparts
def test_ops():
	def t(d):
		a = rand_fixed(*d())
		b = rand_fixed(*d())

		# force same sign (for float later)
		b.resize(a._signed, None, None);

		print(a, b)

		getcontext().prec = max(len(a), len(b)) + 1 # set precision

		assert abs((a+b).decimal() - (a.decimal() + b.decimal())) <= EPSILON_RAW

		if a._signed: # unsigned subtraction diff
			assert abs((a-b).decimal() - (a.decimal() - b.decimal())) <= EPSILON_RAW

		getcontext().prec = len(a) + len(b) # set precision
		assert abs((a*b).decimal() - (a.decimal() * b.decimal())) <= EPSILON_RAW

	eval_distrs(t)