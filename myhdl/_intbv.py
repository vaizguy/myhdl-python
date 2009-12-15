#  This file is part of the myhdl library, a Python package for using
#  Python as a Hardware Description Language.
#
#  Copyright (C) 2003-2008 Jan Decaluwe
#
#  The myhdl library is free software; you can redistribute it and/or
#  modify it under the terms of the GNU Lesser General Public License as
#  published by the Free Software Foundation; either version 2.1 of the
#  License, or (at your option) any later version.
#
#  This library is distributed in the hope that it will be useful, but
#  WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
#  Lesser General Public License for more details.

#  You should have received a copy of the GNU Lesser General Public
#  License along with this library; if not, write to the Free Software
#  Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA 02111-1307 USA

""" Module with the intbv class """



import sys
maxint = sys.maxint
from types import StringType
import operator

from myhdl._bin import bin

from __builtin__ import max as maxfunc

class intbv(object):
    __slots__ = ('_val', '_min', '_max', '_nrbits')
    
    def __init__(self, val=None, min=None, max=None, _nrbits=0):
        if _nrbits:
            self._min = 0
            self._max = 2**_nrbits
        else:
            self._min = min
            self._max = max
            if max is not None and min is not None:
                if min >= 0:
                    _nrbits = len(bin(max-1))
                elif max <= 1:
                    _nrbits = len(bin(min))
                else:
                    # make sure there is a leading zero bit in positive numbers
                    _nrbits = maxfunc(len(bin(max-1))+1, len(bin(min)))
        if isinstance(val, (int, long)):
            self._val = val
        elif isinstance(val, StringType):
            mval = val.replace('_', '')
            self._val = long(mval, 2)
            _nrbits = len(val)
        elif isinstance(val, intbv):
            self._val = val._val
            self._min = val._min
            self._max = val._max
            _nrbits = val._nrbits
        elif val is None:
            self._val = None # for Cosimulation and X, Z support perhaps
        else:
            raise TypeError("intbv constructor arg should be int or string")
        self._nrbits = _nrbits
        self._checkBounds()
        
    # support for the 'min' and 'max' attribute
    def _get_max(self):
        return self._max
    max = property(_get_max, None)
    def _get_min(self):
        return self._min
    min = property(_get_min, None)

    def _checkBounds(self):
        if self._val is None: return
        if self._max is not None:
            if self._val >= self._max:
                raise ValueError("intbv value %s >= maximum %s" %
                                 (self._val, self._max))
        if self._min is not None:
            if self._val < self._min:
                raise ValueError("intbv value %s < minimum %s" %
                                 (self._val, self._min))


    # hash
    def __hash__(self):
        raise TypeError("intbv objects are unhashable")
        
    # copy methods
    def __copy__(self):
        return intbv(self)
    def __deepcopy__(self, visit):
        return intbv(self)

    # iterator method
    def __iter__(self):
        if not self._nrbits:
            raise TypeError, "Cannot iterate over unsized intbv"
        return iter([self[i] for i in range(self._nrbits-1, -1, -1)])

    # logical testing
    def __nonzero__(self):
        if self._val:
            return 1
        else:
            return 0

    # length
    def __len__(self):
        return self._nrbits

    # indexing and slicing methods

    def __getitem__(self, key):
        if isinstance(key, int):
            i = key
            if self._val is None:
                return intbv(None, _nrbits=1)
            res = bool((self._val >> i) & 0x1)
            return res
        elif isinstance(key, slice):
            i, j = key.start, key.stop
            if j is None: # default
                j = 0
            if j < 0:
                raise ValueError, "intbv[i:j] requires j >= 0\n" \
                      "            j == %s" % j
            if i is None: # default
                return intbv(self._val >> j)
            if i <= j:
                raise ValueError, "intbv[i:j] requires i > j\n" \
                      "            i, j == %s, %s" % (i, j)
            if self._val is None:
                return intbv(None, _nrbits=i-j)
            res = intbv((self._val & (1L << i)-1) >> j, _nrbits=i-j)
            return res
        else:
            raise TypeError("intbv item/slice indices should be integers")

       
    def __setitem__(self, key, val):
        if isinstance(key, int):
            i = key
            if val not in (0, 1):
                raise ValueError, "intbv[i] = v requires v in (0, 1)\n" \
                      "            i == %s " % i
            if val:
                self._val |= (1L << i)
            else:
                self._val &= ~(1L << i)
            self._checkBounds()
        elif isinstance(key, slice):
            if val == None:
                raise ValueError, "cannot attribute None to a slice"
            i, j = key.start, key.stop
            if (self._val == None) and (i != None) and (j != None):
                raise ValueError, "cannot slice value None"
            if j is None: # default
                if i is None and self._val is None:
                    self._val = val
                j = 0
            if j < 0:
                raise ValueError, "intbv[i:j] = v requires j >= 0\n" \
                      "            j == %s" % j
            if i is None: # default
                q = self._val % (1L << j)
                self._val = val * (1L << j) + q
                self._checkBounds()
                return
            if i <= j:
                raise ValueError, "intbv[i:j] = v requires i > j\n" \
                      "            i, j, v == %s, %s, %s" % (i, j, val)
            lim = (1L << (i-j))
            if val >= lim or val < -lim:
                raise ValueError, "intbv[i:j] = v abs(v) too large\n" \
                      "            i, j, v == %s, %s, %s" % (i, j, val)
            mask = (1L << (i-j))-1
            mask *= (1L << j)
            self._val &= ~mask
            self._val |= val * (1L << j)
            self._checkBounds()
        else:
            raise TypeError("intbv item/slice indices should be integers")

        
    # integer-like methods
    
    def __add__(self, other):
        if isinstance(other, intbv):
            return self._val + other._val
        else:
            return self._val + other
    def __radd__(self, other):
        return other + self._val
    
    def __sub__(self, other):
        if isinstance(other, intbv):
            return self._val - other._val
        else:
            return self._val - other
    def __rsub__(self, other):
        return other - self._val

    def __mul__(self, other):
        if isinstance(other, intbv):
            return self._val * other._val
        else:
            return self._val * other
    def __rmul__(self, other):
        return other * self._val

    def __div__(self, other):
        if isinstance(other, intbv):
            return self._val / other._val
        else:
            return self._val / other
    def __rdiv__(self, other):
        return other / self._val
    
    def __truediv__(self, other):
        if isinstance(other, intbv):
            return operator.truediv(self._val, other._val)
        else:
            return operator.truediv(self._val, other)
    def __rtruediv__(self, other):
        return operator.truediv(other, self._val)
    
    def __floordiv__(self, other):
        if isinstance(other, intbv):
            return self._val // other._val
        else:
            return self._val // other
    def __rfloordiv__(self, other):
        return other //  self._val
    
    def __mod__(self, other):
        if isinstance(other, intbv):
            return self._val % other._val
        else:
            return self._val % other
    def __rmod__(self, other):
        return other % self._val

    # divmod
    
    def __pow__(self, other):
        if isinstance(other, intbv):
            return self._val ** other._val
        else:
            return self._val ** other
    def __rpow__(self, other):
        return other ** self._val

    def __lshift__(self, other):
        if isinstance(other, intbv):
            return intbv(long(self._val) << other._val)
        else:
            return intbv(long(self._val) << other)
    def __rlshift__(self, other):
        return other << self._val
            
    def __rshift__(self, other):
        if isinstance(other, intbv):
            return intbv(self._val >> other._val)
        else:
            return intbv(self._val >> other)
    def __rrshift__(self, other):
        return other >> self._val
           
    def __and__(self, other):
        if isinstance(other, intbv):
            return intbv(self._val & other._val)
        else:
            return intbv(self._val & other)
    def __rand__(self, other):
        return intbv(other & self._val)

    def __or__(self, other):
        if isinstance(other, intbv):
            return intbv(self._val | other._val)
        else:
            return intbv(self._val | other)
    def __ror__(self, other):
        return intbv(other | self._val)
    
    def __xor__(self, other):
        if isinstance(other, intbv):
            return intbv(self._val ^ other._val)
        else:
            return intbv(self._val ^ other)
    def __rxor__(self, other):
        return intbv(other ^ self._val)

    def __iadd__(self, other):
        if isinstance(other, intbv):
            self._val += other._val
        else:
            self._val += other
        self._checkBounds()
        return self
        
    def __isub__(self, other):
        if isinstance(other, intbv):
            self._val -= other._val
        else:
            self._val -= other
        self._checkBounds()
        return self
        
    def __imul__(self, other):
        if isinstance(other, intbv):
            self._val *= other._val
        else:
            self._val *= other
        self._checkBounds()
        return self
    
    def __ifloordiv__(self, other):
        if isinstance(other, intbv):
            self._val //= other._val
        else:
            self._val //= other
        self._checkBounds()
        return self

    def __idiv__(self, other):
        raise TypeError("intbv: Augmented classic division not supported")
    def __itruediv__(self, other):
        raise TypeError("intbv: Augmented true division not supported")
    
    def __imod__(self, other):
        if isinstance(other, intbv):
            self._val %= other._val
        else:
            self._val %= other
        self._checkBounds()
        return self
        
    def __ipow__(self, other, modulo=None):
        # XXX why 3rd param required?
        # unused but needed in 2.2, not in 2.3 
        if isinstance(other, intbv):
            self._val **= other._val
        else:
            self._val **= other
        if not isinstance(self._val, (int, long)):
            raise ValueError("intbv value should be integer")
        self._checkBounds()
        return self
        
    def __iand__(self, other):
        if isinstance(other, intbv):
            self._val &= other._val
        else:
            self._val &= other
        self._checkBounds()
        return self

    def __ior__(self, other):
        if isinstance(other, intbv):
            self._val |= other._val
        else:
            self._val |= other
        self._checkBounds()
        return self

    def __ixor__(self, other):
        if isinstance(other, intbv):
            self._val ^= other._val
        else:
            self._val ^= other
        self._checkBounds()
        return self

    def __ilshift__(self, other):
        self._val = long(self._val)
        if isinstance(other, intbv):
            self._val <<= other._val
        else:
            self._val <<= other
        self._checkBounds()
        return self

    def __irshift__(self, other):
        if isinstance(other, intbv):
            self._val >>= other._val
        else:
            self._val >>= other
        self._checkBounds()
        return self

    def __neg__(self):
        return -self._val

    def __pos__(self):
        return self._val

    def __abs__(self):
        return abs(self._val)

    def __invert__(self):
        if self._nrbits and self._min >= 0:
            return intbv(~self._val & (1L << self._nrbits)-1)
        else:
            return intbv(~self._val)
    
    def __int__(self):
        return int(self._val)
        
    def __long__(self):
        return long(self._val)

    def __float__(self):
        return float(self._val)

    # XXX __complex__ seems redundant ??? (complex() works as such?)
    
    def __oct__(self):
        return oct(self._val)
    
    def __hex__(self):
        return hex(self._val)
      
        
    def __cmp__(self, other):
        if isinstance(other, intbv):
            return cmp(self._val, other._val)
        else:
            return cmp(self._val, other)

    # representation 
    def __str__(self):
        return str(self._val)

    def __repr__(self):
        return "intbv(" + repr(self._val) + ")"


    def signed(self):
      ''' return integer with the signed value of the intbv instance

      The intbv.signed() function will classify the value of the intbv
      instance either as signed or unsigned. If the value is classified
      as signed it will be returned unchanged as integer value. If the
      value is considered unsigned, the bits as specified by _nrbits
      will be considered as 2's complement number and returned. This
      feature will allow to create slices and have the sliced bits be
      considered a 2's complement number.

      The classification is based on the following possible combinations
      of the min and max value.
          
        ----+----+----+----+----+----+----+----
           -3   -2   -1    0    1    2    3
      1                   min  max
      2                        min  max
      3              min       max
      4              min            max
      5         min            max
      6         min       max
      7         min  max
      8   neither min nor max is set
      9   only max is set
      10  only min is set

      From the above cases, # 1 and 2 are considered unsigned and the
      signed() function will convert the value to a signed number.
      Decision about the sign will be done based on the msb. The msb is
      based on the _nrbits value.
      
      So the test will be if min >= 0 and _nrbits > 0. Then the instance
      is considered unsigned and the value is returned as 2's complement
      number.
      '''

      # value is considered unsigned
      if self.min >= 0 and self._nrbits > 0:

        # get 2's complement value of bits
        msb = self._nrbits-1

        sign = ((self._val >> msb) & 0x1) > 0
        
        # mask off the bits msb-1:lsb, they are always positive
        mask = (1<<msb) - 1
        retVal = self._val & mask
        # if sign bit is set, subtract the value of the sign bit
        if sign:
          retVal -= 1<<msb

      else: # value is returned just as is
        retVal = self._val

      return retVal
