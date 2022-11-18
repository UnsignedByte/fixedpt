# -*- coding: utf-8 -*-
# @Author: UnsignedByte
# @Date:   2022-11-18 12:20:13
# @Last Modified by:   UnsignedByte
# @Last Modified time: 2022-11-18 14:34:58

import sys
sys.path.insert(0, '../')
from src.fixedpt import CFixed
from random import randint
from decimal import getcontext, Decimal

EPSILON_RAW = 1e-12 # epsilon value

def distr(n, d):
	return lambda _=0: (
		nb := randint(n[0], n[1]),
		randint(d[0], min(d[1], nb-1))
	)

TEST_DISTRIBUTIONS = [(distr(n, d), c) for (n, d, c) in [ # Distribution of types of fixed numbers to test
	((2, 8), (0, 8), 100), # small numbers
	((32, 32), (0, 32), 500), # signed and unsigned 32 bit floats 
	((2, 64), (0, 64), 500), # signed and unsigned 64 bit floats 
	# ((128, 1024), (0, 1024), 100) # large bit width numbers
]]

def rand_cfixed(n, d):
	return CFixed((randint(0, (1<<n)-1), randint(0, (1<<n)-1)), n, d, raw=True)

def eval_distrs(t): # evaluate tests on all distributions
	for (d, c) in TEST_DISTRIBUTIONS:
		for i in range(c):
			t(d)

def cmul(a, b):
	return (a[0] * b[0] - a[1] * b[1], a[0] * b[1] + a[1] * b[0])

# check that +, -, * are approximately equal to their float counterparts
def test_ops():
	def t(d):
		a = rand_cfixed(*d())
		b = rand_cfixed(*d())
		print(a, b)

		t = a+b

		getcontext().prec = len(t) # set precision

		t = t.decimal()
		t1 = a.decimal()
		t2 = b.decimal()

		assert (a + b).real == (a.real + b.real)
		assert (a + b).imag == (a.imag + b.imag)

		assert (t[0] - (t1[0] + t2[0]) <= EPSILON_RAW) and (t[1] - (t1[1] + t2[1]) <= EPSILON_RAW)

		t = (a-b).decimal();

		assert (t[0] - t1[0] + t2[0] <= EPSILON_RAW) and (t[1] - t1[1] + t2[1] <= EPSILON_RAW)

		getcontext().prec = len(a) + len(b) # set precision

		t = (a*b).decimal();
		t1 = cmul(t1, t2);
		assert (t[0] - t1[0] <= EPSILON_RAW) and (t[1] - t1[1] <= EPSILON_RAW)

	eval_distrs(t)