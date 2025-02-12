// pragma solidity >=0.4.0;
pragma solidity ^0.7.6;

/**
 * @title Pairing
 * @dev BN128 pairing operations. Taken from https://github.com/JacobEberhardt/ZoKrates/blob/da5b13f845145cf43d555c7741158727ef0018a2/zokrates_core/src/verification.rs.
 */
library Pairing {
    /*
     * Structs
     */

    struct G1Point {
        uint x;
        uint y;
    }

    struct G2Point {
        uint[2] x;
        uint[2] y;
    }


    uint public constant ERROR_EXE = 2;
    uint public constant WRONG = 1;
    uint public constant SUCCESS = 0;


    /*
     * Internal functions
     */

    /**
     * @return The generator of G1.
     */
    function P1() internal pure returns (G1Point memory) {
        return G1Point(1, 2);
    }

    /**
     * @return The generator of G2.
     */
    function P2() internal pure returns (G2Point memory) {
        return G2Point({
            x: [
                11559732032986387107991004021392285783925812861821192530917403151452391805634,
                10857046999023057135944570762232829481370756359578518086990519993285655852781
            ],
            y: [
                4082367875863433681332203403145435568316851327593401208105741076214120093531,
                8495653923123431417604973247489272438418190587263600148770280649306958101930
            ]
        });
    }

    /**
     * @dev Hashes a message into G1.
     * @param _message Message to hash.
     * @return Hashed G1 point. 
     */
    function hashToG1(bytes memory _message) internal returns (G1Point memory) {
        uint256 h = uint256(keccak256(_message));
        return curveMul(P1(), h);
    }

    /**
     * @dev Negates a point in G1.
     * @param _point Point to negate.
     * @return The negated point.
     */
    function negate(G1Point memory _point) internal pure returns (G1Point memory) {
        return negateLst([_point.x, _point.y]);
    }

    function negateLst(uint[2] memory _point) internal pure returns (G1Point memory) {
        uint q = 21888242871839275222246405745257275088696311157297823662689037894645226208583;
        if (_point[0] == 0 && _point[1] == 0) {
            return G1Point(0, 0);
        }
        return G1Point(_point[0], q - (_point[1] % q));
    }

    /**
     * @dev Computes the pairing check e(p1[0], p2[0]) *  .... * e(p1[n], p2[n]) == 1
     * @param _g1points List of points in G1.
     * @param _g2points List of points in G2.
     * @return True if pairing check succeeds.
     */
    function pairing(G1Point[] memory _g1points, G2Point[] memory _g2points) internal returns (uint) {
        require(_g1points.length == _g2points.length, "Point count mismatch.");

        uint elements = _g1points.length;
        uint inputSize = elements * 6;
        uint[] memory input = new uint[](inputSize);


        for (uint i = 0; i < elements; i++) {
            input[i * 6 + 0] = _g1points[i].x;
            input[i * 6 + 1] = _g1points[i].y;
            input[i * 6 + 2] = _g2points[i].x[0];
            input[i * 6 + 3] = _g2points[i].x[1];
            input[i * 6 + 4] = _g2points[i].y[0];
            input[i * 6 + 5] = _g2points[i].y[1];
        }

        uint[1] memory out;
        bool success;

        assembly {
            success := call(sub(gas(), 2000), 8, 0, add(input, 0x20), mul(inputSize, 0x20), out, 0x20)
        }
        // require(success, "Pairing operation failed.");

        if (success == false) {
            return ERROR_EXE;
        } else if (out[0] == 0) {
            return WRONG;
        } else {
            return SUCCESS;
        }

        // return out[0] != 0;
    }

    /**
     * @dev Convenience method for pairing check on two pairs.
     * @param _g1point1 First point in G1.
     * @param _g2point1 First point in G2.
     * @param _g1point2 Second point in G1.
     * @param _g2point2 Second point in G2.
     * @return True if the pairing check succeeds.
     */
    function pairing2(
        G1Point memory _g1point1,
        G2Point memory _g2point1,
        G1Point memory _g1point2,
        G2Point memory _g2point2
    ) internal returns (uint) {
        G1Point[] memory g1points = new G1Point[](2);
        G2Point[] memory g2points = new G2Point[](2);
        g1points[0] = _g1point1;
        g1points[1] = _g1point2;
        g2points[0] = _g2point1;
        g2points[1] = _g2point2;
        return pairing(g1points, g2points);
    }


    /*
     * Private functions
     */

    /**
     * @dev Multiplies a point in G1 by a scalar.
     * @param _point G1 point to multiply.
     * @param _scalar Scalar to multiply.
     * @return The resulting G1 point.
     */
    function curveMul(G1Point memory _point, uint _scalar) internal returns (G1Point memory) {
        uint[3] memory input;
        input[0] = _point.x;
        input[1] = _point.y;
        input[2] = _scalar;

        bool success;
        G1Point memory result;
        assembly {
            success := call(sub(gas(), 2000), 7, 0, input, 0x80, result, 0x60)
        }
        require(success, "Point multiplication failed.");
        
        return result;
    }

    function addG1(G1Point memory _point1, G1Point memory _point2) internal returns (G1Point memory) {
        uint[4] memory input;
        input[0] = _point1.x;
        input[1] = _point1.y;
        input[2] = _point2.x;
        input[3] = _point2.y;
        bool success;
        G1Point memory result;
        assembly {
            success := call(sub(gas(), 2000), 6, 0, input, 0xc0, result, 0x60)
        // Use "invalid" to make gas estimation work
         //   switch success case 0 {invalid}
        }
        require(success, "Points addition failed.");
        return result;
    }

    function expMod(uint base, uint e, uint m) internal returns (uint o) {
        bool success;
        assembly {
            // define pointer
            let p := mload(0x40)
            // store data assembly-favouring ways
            mstore(p, 0x20)             // Length of Base
            mstore(add(p, 0x20), 0x20)  // Length of Exponent
            mstore(add(p, 0x40), 0x20)  // Length of Modulus
            mstore(add(p, 0x60), base)  // Base
            mstore(add(p, 0x80), e)     // Exponent
            mstore(add(p, 0xa0), m)     // Modulus
            success := staticcall(sub(gas(), 2000), 0x05, p, 0xc0, p, 0x20)
            // data
            o := mload(p)
        }

        require(success, "expMod failed.");
    }

}