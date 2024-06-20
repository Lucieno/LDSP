from random import SystemRandom # cryptographic random byte generator
from hashlib import sha256

from py_eth_pairing import curve_add, curve_mul

#from py_eth_pairing import curve_add, curve_mul

# Convert a string with hex digits, colons, and whitespace to a long integer
def hex2int(hexString):
    return int("".join(hexString.replace(":","").split()),16)

# Half the extended Euclidean algorithm:
#    Computes   gcd(a,b) = a*x + b*y  
#    Returns only gcd, x (not y)
# From http://rosettacode.org/wiki/Modular_inverse#Python
def half_extended_gcd(aa, bb):
    lastrem, rem = abs(aa), abs(bb)
    x, lastx = 0, 1
    while rem:
        lastrem, (quotient, rem) = rem, divmod(lastrem, rem)
        x, lastx = lastx - quotient * x, x
    return lastrem, lastx

# Modular inverse: compute the multiplicative inverse i of a mod m:
#     i*a = a*i = 1 mod m
def modular_inverse(a, m):
    g, x = half_extended_gcd(a, m)
    if g != 1:
        raise ValueError
    return x % m

# Hash the message M and the curve point R
#  (this isn't any offical scheme, but a simple ASCII concatenation)
def hashThis(M,R):
    hash=sha256();
    hash.update(M.encode());
    #hash.update(M);
    hash.update(str(R).encode());
    return int(hash.hexdigest(),16); # part 1 of signature


# An elliptic curve has these fields:
#   p: the prime used to mod all coordinates
#   a: linear part of curve: y^2 = x^3 + ax + b
#   b: constant part of curve
#   G: a curve point (G.x,G.y) used as a "generator"
#   n: the order of the generator
class ECcurve:
    def __init__(self):
        return

    # Prime field multiplication: return a*b mod p
    def field_mul(self, a, b):
        return (a * b) % self.p

    # Prime field division: return num/den mod p
    def field_div(self, num, den):
        inverse_den = modular_inverse(den % self.p, self.p)
        return self.field_mul(num % self.p, inverse_den)

    # Prime field exponentiation: raise num to power mod p
    def field_exp(self, num, power):
        return pow(num % self.p, power, self.p)

    # Return the special identity point
    #   We pick x=p, y=0
    def identity(self):
        return ECpoint(self, self.p, 0, 1)

    # Return true if point Q lies on our curve
    def touches(self, Q):
        x = Q.get_x()
        y = Q.get_y()
        y2 = (y * y) % self.p
        x3ab = (self.field_mul((x * x) % self.p + self.a, x) + self.b) % self.p
        return y2 == (x3ab) % self.p

    # Return the slope of the tangent of this curve at point Q
    def tangent(self, Q):
        return self.field_div(Q.x * Q.x * 3 + self.a, Q.y * 2)

    # Return a doubled version of this elliptic curve point
    #  Closely follows Gueron & Krasnov 2013 figure 2
    def double(self, Q):
        if (Q.x == self.p): # doubling the identity
            return Q
        S = (4 * Q.x * Q.y * Q.y) % self.p
        Z2 = Q.z * Q.z
        Z4 = (Z2 * Z2) % self.p
        M = (3 * Q.x * Q.x + self.a * Z4)
        x = (M * M - 2 * S) % self.p
        Y2 = Q.y * Q.y
        y = (M * (S - x) - 8 * Y2 * Y2) % self.p
        z = (2 * Q.y * Q.z) % self.p
        return ECpoint(self, x, y, z)

    # Return the "sum" of these elliptic curve points
    #  Closely follows Gueron & Krasnov 2013 figure 2
    def add(self, Q1, Q2):
        # Identity special cases
        if (Q1.x == self.p): # Q1 is identity
            return Q2
        if (Q2.x == self.p): # Q2 is identity
            return Q1
        Q1z2 = Q1.z * Q1.z
        Q2z2 = Q2.z * Q2.z
        xs1 = (Q1.x * Q2z2) % self.p
        xs2 = (Q2.x * Q1z2) % self.p
        ys1 = (Q1.y * Q2z2 * Q2.z) % self.p
        ys2 = (Q2.y * Q1z2 * Q1.z) % self.p
        
        # Equality special cases
        if (xs1 == xs2): 
            if (ys1 == ys2): # adding point to itself
                return self.double(Q1)
            else: # vertical pair--result is the identity
                return self.identity()

        # Ordinary case
        xd = (xs2 - xs1) % self.p   # caution: if not python, negative result?
        yd = (ys2 - ys1) % self.p
        xd2 = (xd * xd) % self.p
        xd3 = (xd2 * xd) % self.p
        x = (yd * yd - xd3 - 2 * xs1 * xd2) % self.p
        y = (yd * (xs1 * xd2 - x) - ys1 * xd3) % self.p
        z = (xd * Q1.z * Q2.z) % self.p
        return ECpoint(self, x, y, z)

    # "Multiply" this elliptic curve point Q by the scalar (integer) m
    #    Often the point Q will be the generator G
    def mul(self, m, Q):
        R=self.identity() # return point
        while m != 0:  # binary multiply loop
            if m&1: # bit is set
                #print("  mul: adding Q to R =",R);
                R = self.add(R, Q)
                #print("  mul: added Q to R =",R);
            m = m>>1
            if (m != 0):
                #print("  mul: doubling Q =",Q);
                Q = self.double(Q)        
        return R

# A point on an elliptic curve: (x,y)
#   Using special (X,Y,Z) Jacobian point representation
class ECpoint:
    """A point on an elliptic curve (x/z^2,y/z^3)"""
    def __init__(self, curve, x, y, z):
        self.curve = curve
        self.x = x
        self.y = y
        self.z = z
        # This self-check has a big performance cost.
        #if not x==curve.p and not curve.touches(self):
        #    print(" ECpoint left curve: ",self)

    # "Add" this point to another point on the same curve
    def add(self, Q2):
        return self.curve.add(self, Q2)

    # "Multiply" this point by a scalar
    def mul(self, m):
        return self.curve.mul(m, self)
    
    # Extract non-projective X and Y coordinates
    #   This is the only time we need the expensive modular inverse
    def get_x(self):
        return self.curve.field_div(self.x, (self.z * self.z) % self.curve.p)

    def get_y(self):
        return self.curve.field_div(self.y, (self.z * self.z * self.z) % self.curve.p)

    # Print this ECpoint
    def __str__(self):
        if (self.x == self.curve.p):
            return "identity_point"
        else:
            return "("+str(self.get_x())+", "+str(self.get_y())+")"

class Schnorrsecp256k1(ECcurve):
    def __init__(self):
        self.p = hex2int("FFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFEFFFFFC2F")
        self.a = 0 # it's a Koblitz curve, with no linear part
        self.b = 7
        # n is the order of the curve, used for ECDSA
        self.n = hex2int("FFFFFFFF FFFFFFFF FFFFFFFF FFFFFFFE BAAEDCE6 AF48A03B BFD25E8C D0364141")
        # SEC's "04" means they're representing the generator point's X,Y parts explicitly.
        self.G = ECpoint(curve=self,
                          x=hex2int("79BE667E F9DCBBAC 55A06295 CE870B07 029BFCDB 2DCE28D9 59F2815B 16F81798"),
                          y=hex2int("483ADA77 26A3C465 5DA4FBFC 0E1108A8 FD17B448 A6855419 9C47D08F FB10D4B8"),
                          z=1  # projective coordinates, start with Z==1
                        )
        self.rand = SystemRandom() # create strong random number generator

    def Schnorr_sign(self, sk: int, message: str):
        d = sk % self.n # secret key
        Q = self.G.mul(d)
        k = self.rand.getrandbits(256) % self.n # message nonce
        R = self.G.mul(k) # used to encode
        e = hashThis(message, R) # part 1 of signature
        s = (k - e * d) % self.n # part 2 of signature

        vk = "%d;%d;%d" % (Q.x, Q.y, Q.z) #public key
        sigma = "%d;%d" % (e, s) #S

        return vk, sigma

    def Schnorr_verify(self, sigma, vk, M):
        Generator = self.G
        sigma = sigma.split(";")
        e = int(sigma[0])
        s = int(sigma[1])
        vk = vk.split(";")
        vk_point = ECpoint(curve=self, x=int(vk[0]), y=int(vk[1]), z=int(vk[2]))
        Rv = self.G.mul(s).add(vk_point.mul(e))
        ev = hashThis(M, Rv)
        return e == ev


class Schnorrbn128_leader:
    def __init__(self):
        self.rand = SystemRandom()
        self.sk = 11522266377974662729521524526087191922992110831431765861642141343503609770779
        self.G1 = (1, 2)
        self.curve_order = 21888242871839275222246405745257275088548364400416034343698204186575808495617

    def Schnorr_sign(self, message: str): #assume sk < curve_order
        Q = curve_mul(self.G1, self.sk)
        k = self.rand.getrandbits(256) % self.curve_order
        R = curve_mul(self.G1, k)
        e = hashThis(message, R)
        s = (k - e * self.sk) % self.curve_order
        signature = "%d;%d" % (e, s)
   
        return signature

class Schnorrbn128:
    def __init__(self):
        self.vk = (11086577915690224135620704344365800945114819089084513210222838541073542725104,
                   4460287318258275375240925920373324558137077213855624363359286584097902939847)
        self.G1 = (1, 2)

    def Schnorr_verify(self, sigma, message):
        sigma = sigma.split(";")
        if len(sigma) != 2:
            return False
        e = int(sigma[0])
        s = int(sigma[1])
        rv = curve_add(curve_mul(self.G1, s), curve_mul(self.vk, e))
        ev = hashThis(message, rv)
        return e == ev
